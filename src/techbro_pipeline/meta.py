"""Publish reviewed draft chains through Meta's official Threads API."""

import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import dotenv_values, set_key

from techbro_pipeline.config import Settings, day_stamp, write_json

API_URL = "https://graph.threads.net/v1.0/"
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class ThreadsError(Exception):
    """An error safe to show without response bodies or token values."""


def validate_day(day):
    try:
        parsed = datetime.strptime(day, "%Y%m%d")
    except (TypeError, ValueError):
        raise ThreadsError("date must be YYYYMMDD") from None
    if parsed.strftime("%Y%m%d") != day:
        raise ThreadsError("date must be YYYYMMDD")
    return day


def read_draft(day):
    validate_day(day)
    path = Settings.from_env().data_dir / "threads" / f"threads_draft_{day}.json"
    try:
        draft = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ThreadsError(
            "requested draft is missing or invalid; generate and review it first"
        ) from None
    if not isinstance(draft, dict) or draft.get("date") != day:
        raise ThreadsError("draft date does not match the requested day")
    return validated_texts(draft.get("parts"))


def validated_texts(parts):
    if not isinstance(parts, list) or not parts:
        raise ThreadsError("draft must contain at least one text part")
    texts = []
    for index, part in enumerate(parts, start=1):
        text = part.get("text") if isinstance(part, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise ThreadsError(f"draft part {index} is empty or invalid")
        if len(text) > 500:
            raise ThreadsError(f"draft part {index} exceeds Threads' 500-character limit")
        texts.append(text)
    return texts


def response_id(result):
    value = result.get("id")
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise ThreadsError("Meta did not return a valid object ID")
    return value


class ThreadsClient:
    def __init__(self, token, *, transport=None, sleep=time.sleep):
        if not token or any(character.isspace() for character in token):
            raise ThreadsError("set THREADS_ACCESS_TOKEN to your Threads user access token")
        self.token = token
        self.sleep = sleep
        self.http = httpx.Client(
            base_url=API_URL,
            headers={"Authorization": "Bearer " + token},
            timeout=30,
            follow_redirects=False,
            transport=transport,
        )

    @classmethod
    def from_env(cls):
        return cls(os.getenv("THREADS_ACCESS_TOKEN", ""))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.http.close()

    def request(self, method, path, **kwargs):
        try:
            response = self.http.request(method, path, **kwargs)
        except httpx.RequestError:
            raise ThreadsError(
                "Meta request did not complete; no automatic retry was attempted"
            ) from None
        if not 200 <= response.status_code < 300:
            raise ThreadsError(
                f"Meta returned HTTP {response.status_code}; check token expiry and Threads permissions"
            )
        try:
            result = response.json()
        except ValueError:
            raise ThreadsError("Meta returned an invalid JSON response") from None
        if not isinstance(result, dict) or "error" in result:
            raise ThreadsError("Meta returned an unexpected response")
        return result

    def profile(self):
        result = self.request("GET", "me", params={"fields": "id,username"})
        user_id = response_id(result)
        username = result.get("username")
        if not isinstance(username, str) or not username:
            raise ThreadsError("Meta did not return a valid Threads profile")
        return {"id": user_id, "username": username}

    def create_container(self, text, reply_to_id=None):
        data = {"media_type": "TEXT", "text": text}
        if reply_to_id:
            data["reply_to_id"] = reply_to_id
        # Keep creation separate from publishing; never set auto_publish_text.
        return response_id(self.request("POST", "me/threads", data=data))

    def create_video_container(self, text, video_url):
        return response_id(
            self.request(
                "POST",
                "me/threads",
                data={"media_type": "VIDEO", "video_url": video_url, "text": text},
            )
        )

    def wait_until_ready(self, container_id, attempts=10, interval=2):
        for attempt in range(attempts):
            result = self.request("GET", container_id, params={"fields": "status"})
            status = result.get("status")
            if status == "FINISHED":
                return
            if status != "IN_PROGRESS":
                raise ThreadsError(
                    "container is not publishable; inspect its receipt and Threads account"
                )
            if attempt < attempts - 1:
                self.sleep(interval)
        raise ThreadsError("container is still processing; rerun to check the same container")

    def publish_container(self, container_id):
        return response_id(
            self.request("POST", "me/threads_publish", data={"creation_id": container_id})
        )

    def refresh(self):
        result = self.request(
            "GET",
            "https://graph.threads.net/refresh_access_token",
            params={"grant_type": "th_refresh_token"},
        )
        token, expires = result.get("access_token"), result.get("expires_in")
        if (
            not isinstance(token, str)
            or not token
            or any(character.isspace() for character in token)
            or not isinstance(expires, int)
            or expires <= 0
        ):
            raise ThreadsError("Meta returned an invalid token refresh response")
        return token, expires


def receipt_path(day, user_id):
    validate_day(day)
    account_hash = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return Settings.from_env().data_dir / "meta" / f"publish_{day}_{account_hash}.json"


def recorded_draft(day, user_id):
    if not user_id or not ID_RE.fullmatch(user_id):
        raise ThreadsError("set THREADS_USER_ID before reading a recorded draft")
    path = receipt_path(day, user_id)
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ThreadsError("recorded draft is missing or invalid") from None
    if (
        not isinstance(receipt, dict)
        or receipt.get("date") != day
        or receipt.get("userId") != user_id
    ):
        raise ThreadsError("recorded draft does not match the selected account and date")
    texts = validated_texts(receipt.get("parts"))
    fingerprint = hashlib.sha256(json.dumps(texts).encode("utf-8")).hexdigest()
    if receipt.get("requestHash") != fingerprint:
        raise ThreadsError("recorded draft content is invalid; inspect the receipt before retrying")
    return texts


def publish(day, texts, client, expected_user_id):
    """Resume known progress and block any publish whose outcome is uncertain."""
    validate_day(day)
    if not expected_user_id or not ID_RE.fullmatch(expected_user_id):
        raise ThreadsError("set THREADS_USER_ID from the meta profile command before publishing")
    profile = client.profile()
    if profile["id"] != expected_user_id:
        raise ThreadsError("token belongs to a different account than THREADS_USER_ID")
    path = receipt_path(day, profile["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(json.dumps(texts).encode("utf-8")).hexdigest()
    with path.with_suffix(".lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ThreadsError("another publisher for this account and day is active") from None
        if path.exists():
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(receipt, dict) or receipt.get("requestHash") != fingerprint:
                raise ThreadsError(
                    "draft differs from the recorded submission; inspect the receipt first"
                )
            parts = receipt.get("parts")
            if (
                receipt.get("date") != day
                or receipt.get("userId") != expected_user_id
                or not isinstance(parts, list)
                or len(parts) != len(texts)
                or any(not isinstance(part, dict) for part in parts)
            ):
                raise ThreadsError("submission receipt is invalid; inspect it before retrying")
        else:
            receipt = {
                "date": day,
                "userId": profile["id"],
                "requestHash": fingerprint,
                "state": "in_progress",
                "parts": [
                    {
                        "number": index,
                        "text": text,
                        "state": "draft",
                        "containerId": None,
                        "postId": None,
                    }
                    for index, text in enumerate(texts, start=1)
                ],
            }
            write_json(path, receipt)
        unfinished = False
        for index, part in enumerate(receipt["parts"], start=1):
            state = part.get("state")
            if (
                part.get("number") != index
                or not isinstance(state, str)
                or state
                not in {"draft", "creating", "created", "publishing", "unknown", "published"}
            ):
                raise ThreadsError("submission receipt is invalid; inspect it before retrying")
            if state == "published":
                if unfinished:
                    raise ThreadsError(
                        "submission receipt is invalid; published parts must be consecutive"
                    )
                response_id({"id": part.get("postId")})
            else:
                unfinished = True
            if state in {"created", "publishing", "unknown", "published"}:
                response_id({"id": part.get("containerId")})
        if any(part["state"] in {"publishing", "unknown"} for part in receipt["parts"]):
            raise ThreadsError("publish outcome is unknown; inspect Threads before retrying")
        reply_to_id = None
        for part, text in zip(receipt["parts"], texts, strict=True):
            if part.get("state") == "published":
                reply_to_id = response_id({"id": part.get("postId")})
                continue
            if not part.get("containerId"):
                part["state"] = "creating"
                write_json(path, receipt)
                # A lost creation response is safe to retry: containers are not posts.
                part["containerId"] = client.create_container(text, reply_to_id)
                part["state"] = "created"
                write_json(path, receipt)
            container_id = response_id({"id": part["containerId"]})
            client.wait_until_ready(container_id)
            part["state"] = "publishing"
            write_json(path, receipt)
            try:
                part["postId"] = client.publish_container(container_id)
            except ThreadsError:
                part["state"] = "unknown"
                receipt["state"] = "unknown"
                write_json(path, receipt)
                raise ThreadsError(
                    "publish outcome is unknown; inspect Threads before retrying"
                ) from None
            part["state"] = "published"
            write_json(path, receipt)
            reply_to_id = part["postId"]
        receipt["state"] = "published"
        write_json(path, receipt)
        return receipt


def public_media_url(base_url, day, filename):
    """Build a public video URL from the configured public app origin."""
    parsed = urlparse(base_url or "")
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ThreadsError("set THREADS_MEDIA_PUBLIC_BASE_URL to a public HTTPS app origin")
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        if parsed.hostname.lower() == "localhost" or "." not in parsed.hostname:
            raise ThreadsError("THREADS_MEDIA_PUBLIC_BASE_URL must use a public hostname") from None
    else:
        if not address.is_global:
            raise ThreadsError("THREADS_MEDIA_PUBLIC_BASE_URL must use a public hostname")
    validate_day(day)
    if not re.fullmatch(rf"techbro-{day}-\d{{6}}-[0-9a-f]{{8}}\.mp4", filename or ""):
        raise ThreadsError("video filename is invalid")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/api/daily/{day}/video/{filename}"


def video_receipt_path(day, user_id, fingerprint):
    validate_day(day)
    account_hash = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    return Settings.from_env().data_dir / "meta" / f"video_{day}_{account_hash}_{fingerprint}.json"


def publish_video(day, filename, caption, video_path, video_url, client, expected_user_id):
    """Publish one video with a durable receipt to prevent duplicate retries."""
    validate_day(day)
    if not isinstance(caption, str) or not caption.strip() or len(caption) > 500:
        raise ThreadsError("caption must contain 1–500 characters")
    video_path = Path(video_path)
    if not video_path.is_file() or video_path.suffix.lower() != ".mp4":
        raise ThreadsError("rendered MP4 is missing or invalid")
    video_hash = hashlib.sha256()
    with video_path.open("rb") as video_file:
        for chunk in iter(lambda: video_file.read(1024 * 1024), b""):
            video_hash.update(chunk)
    fingerprint = hashlib.sha256(f"{video_hash.hexdigest()}\0{caption}".encode()).hexdigest()
    profile = client.profile()
    if not expected_user_id or not ID_RE.fullmatch(expected_user_id):
        raise ThreadsError("set THREADS_USER_ID from the meta profile command before publishing")
    if profile["id"] != expected_user_id:
        raise ThreadsError("token belongs to a different account than THREADS_USER_ID")
    path = video_receipt_path(day, profile["id"], fingerprint)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(".lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ThreadsError("another publisher for this video is active") from None
        if path.exists():
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if (
                not isinstance(receipt, dict)
                or receipt.get("requestHash") != fingerprint
                or receipt.get("userId") != profile["id"]
                or receipt.get("date") != day
                or receipt.get("filename") != filename
            ):
                raise ThreadsError("video receipt is invalid; inspect it before retrying")
            if receipt.get("state") == "published":
                return receipt
            if receipt.get("state") == "unknown":
                raise ThreadsError("publish outcome is unknown; inspect Threads before retrying")
        else:
            receipt = {
                "date": day,
                "userId": profile["id"],
                "filename": filename,
                "requestHash": fingerprint,
                "state": "draft",
                "containerId": None,
                "postId": None,
            }
            write_json(path, receipt)
        if not receipt.get("containerId"):
            receipt["state"] = "creating"
            write_json(path, receipt)
            receipt["containerId"] = client.create_video_container(caption, video_url)
            receipt["state"] = "created"
            write_json(path, receipt)
        container_id = response_id({"id": receipt["containerId"]})
        client.wait_until_ready(container_id, attempts=90, interval=5)
        receipt["state"] = "publishing"
        write_json(path, receipt)
        try:
            receipt["postId"] = client.publish_container(container_id)
        except ThreadsError:
            receipt["state"] = "unknown"
            write_json(path, receipt)
            raise ThreadsError(
                "video publish outcome is unknown; inspect Threads before retrying"
            ) from None
        receipt["state"] = "published"
        write_json(path, receipt)
        return receipt


def refresh_token_file(path, client):
    """Persist a refreshed token in an existing local environment file, never stdout."""
    if not path.is_file() or dotenv_values(path).get("THREADS_ACCESS_TOKEN") != client.token:
        raise ThreadsError(
            "token destination must be an existing environment file matching the current token"
        )
    token, expires = client.refresh()
    set_key(path, "THREADS_ACCESS_TOKEN", token, quote_mode="always")
    path.chmod(0o600)
    return {"refreshed": True, "expires_in": expires}


def main():
    parser = argparse.ArgumentParser(prog="techbro meta")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("profile", help="Read the authenticated Threads account")
    post = commands.add_parser("publish", help="Preview a draft; --submit publishes immediately")
    post.add_argument(
        "--date", default=day_stamp(), help="Exact draft date YYYYMMDD, default Jakarta today"
    )
    post.add_argument(
        "--submit", action="store_true", help="Publish a real Threads post and reply chain"
    )
    post.add_argument(
        "--resume", action="store_true", help="Use the original draft saved in its receipt"
    )
    status = commands.add_parser("status", help="Read local publication receipts")
    status.add_argument("--date", default=day_stamp())
    refresh = commands.add_parser("refresh", help="Refresh a long-lived token and save it locally")
    refresh.add_argument(
        "--save-token", type=Path, required=True, help="Existing local environment file"
    )
    args = parser.parse_args()
    try:
        if args.command == "profile":
            with ThreadsClient.from_env() as client:
                result = client.profile()
        elif args.command == "refresh":
            with ThreadsClient.from_env() as client:
                result = refresh_token_file(args.save_token, client)
        elif args.command == "status":
            validate_day(args.date)
            folder = Settings.from_env().data_dir / "meta"
            result = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(folder.glob(f"publish_{args.date}_*.json"))
            ]
        else:
            user_id = os.getenv("THREADS_USER_ID", "")
            texts = recorded_draft(args.date, user_id) if args.resume else read_draft(args.date)
            if args.submit:
                with ThreadsClient.from_env() as client:
                    result = publish(args.date, texts, client, user_id)
            else:
                result = {
                    "mode": "preview",
                    "date": args.date,
                    "userId": user_id or None,
                    "parts": [
                        {"number": index, "text": text} for index, text in enumerate(texts, start=1)
                    ],
                }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ThreadsError, OSError, ValueError) as exc:
        message = (
            str(exc)
            if isinstance(exc, ThreadsError)
            else "local publication data could not be read or written"
        )
        print(f"[error] {message}", file=sys.stderr)
        return 1
