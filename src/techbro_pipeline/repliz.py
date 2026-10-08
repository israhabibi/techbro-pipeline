"""Preview and schedule reviewed Threads drafts through the Repliz public API."""

import argparse
import fcntl
import hashlib
import json
import os
import sys
from datetime import UTC, datetime

import httpx

from techbro_pipeline.config import LOCAL_TZ, Settings, day_stamp, write_json

API_URL = "https://api.repliz.com"


class ReplizError(Exception):
    """An actionable error safe to show without credentials or response bodies."""


def validate_day(day):
    try:
        parsed = datetime.strptime(day, "%Y%m%d")
    except (ValueError, TypeError):
        raise ReplizError("date must be YYYYMMDD") from None
    if parsed.strftime("%Y%m%d") != day:
        raise ReplizError("date must be YYYYMMDD")
    return day


def parse_schedule_time(value):
    try:
        scheduled = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ReplizError("schedule time must be an ISO 8601 datetime with a timezone") from None
    if scheduled.tzinfo is None:
        raise ReplizError("schedule time needs a timezone, for example +07:00")
    return scheduled.astimezone(UTC)


def build_payload(day, account_id, schedule_at):
    """Read exactly the requested day's draft, never an older fallback artifact."""
    validate_day(day)
    if not isinstance(account_id, str) or not account_id.strip():
        raise ReplizError("set REPLIZ_ACCOUNT_ID to the connected Threads account ID")
    if schedule_at.tzinfo is None:
        raise ReplizError("schedule time needs a timezone")
    path = Settings.from_env().data_dir / "threads" / f"threads_draft_{day}.json"
    try:
        draft = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ReplizError(
            "requested draft is missing or invalid; generate and review it first"
        ) from None
    if not isinstance(draft, dict) or draft.get("date") != day:
        raise ReplizError("draft date does not match the requested day")
    parts = draft.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ReplizError("draft must contain at least one text part")
    posts = []
    for index, part in enumerate(parts, start=1):
        text = part.get("text") if isinstance(part, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise ReplizError(f"draft part {index} is empty or invalid")
        # Repliz documents a UTF-8 byte limit, including emojis, for Threads captions.
        if len(text.encode("utf-8")) > 500:
            raise ReplizError(f"draft part {index} exceeds Repliz's 500-byte text limit")
        posts.append({"title": "", "description": text, "type": "text", "medias": []})
    return {
        **posts[0],
        "replies": posts[1:],
        "accountId": account_id.strip(),
        "scheduleAt": schedule_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
    }


class ReplizClient:
    def __init__(self, access_key, secret_key, *, transport=None):
        if not access_key or not secret_key:
            raise ReplizError(
                "set REPLIZ_ACCESS_KEY and REPLIZ_SECRET_KEY in your local environment"
            )
        if ":" in access_key:
            raise ReplizError("REPLIZ_ACCESS_KEY cannot contain a colon")
        self.http = httpx.Client(
            base_url=API_URL,
            auth=httpx.BasicAuth(access_key, secret_key),
            timeout=30,
            follow_redirects=False,
            transport=transport,
        )

    @classmethod
    def from_env(cls):
        return cls(os.getenv("REPLIZ_ACCESS_KEY", ""), os.getenv("REPLIZ_SECRET_KEY", ""))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.http.close()

    def request(self, method, path, **kwargs):
        try:
            response = self.http.request(method, path, **kwargs)
        except httpx.RequestError:
            raise ReplizError(
                "Repliz request did not complete; no automatic retry was attempted"
            ) from None
        if not 200 <= response.status_code < 300:
            raise ReplizError(
                f"Repliz returned HTTP {response.status_code}; check API access and configuration"
            )
        try:
            result = response.json()
        except ValueError:
            raise ReplizError("Repliz returned an invalid JSON response") from None
        if not isinstance(result, dict):
            raise ReplizError("Repliz returned an unexpected response format")
        return result

    def accounts(self):
        """Return only account identifiers and connection metadata, across pages."""
        accounts = []
        for page in range(1, 101):
            result = self.request(
                "GET", "/public/account", params={"page": page, "limit": 20, "types[0]": "threads"}
            )
            docs = result.get("docs")
            total_pages = result.get("totalPages", 1)
            if (
                not isinstance(docs, list)
                or any(not isinstance(doc, dict) for doc in docs)
                or not isinstance(total_pages, int)
                or total_pages < 1
            ):
                raise ReplizError("Repliz returned an invalid account list")
            for doc in docs:
                if doc.get("type") == "threads":
                    accounts.append(
                        {
                            "id": doc.get("_id") or doc.get("id"),
                            "name": doc.get("name"),
                            "username": doc.get("username"),
                            "type": "threads",
                            "isConnected": doc.get("isConnected") is True,
                        }
                    )
            if not result.get("hasNextPage") and page >= total_pages:
                return accounts
        raise ReplizError("too many account pages; account discovery did not complete")

    def create_schedule(self, payload):
        result = self.request("POST", "/public/schedule", json=payload)
        schedule_id = result.get("scheduleId")
        if not isinstance(schedule_id, str) or not schedule_id.strip():
            raise ReplizError(
                "Repliz did not return a scheduleId; verify the dashboard before retrying"
            )
        return schedule_id


def receipt_path(day, account_id):
    validate_day(day)
    account_hash = hashlib.sha256(account_id.encode("utf-8")).hexdigest()
    return Settings.from_env().data_dir / "repliz" / f"schedule_{day}_{account_hash}.json"


def schedule(day, payload, client):
    """Serialize submissions and stop after any ambiguous remote result."""
    path = receipt_path(day, payload["accountId"])
    path.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    with path.with_suffix(".lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ReplizError("another submission for this account and day is active") from None
        if path.exists():
            previous = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(previous, dict):
                raise ReplizError("submission receipt is invalid; inspect it before retrying")
            if previous.get("state") == "scheduled" and previous.get("requestHash") == fingerprint:
                return previous
            raise ReplizError(
                "submission already recorded for this day; inspect its receipt and Repliz dashboard"
            )
        if parse_schedule_time(payload["scheduleAt"]) <= datetime.now(UTC):
            raise ReplizError("schedule time must be in the future")
        account = next((a for a in client.accounts() if a["id"] == payload["accountId"]), None)
        if account is None or not account["isConnected"]:
            raise ReplizError("target is not a connected Threads account; check REPLIZ_ACCOUNT_ID")
        receipt = {
            "date": day,
            "accountId": payload["accountId"],
            "scheduleAt": payload["scheduleAt"],
            "requestHash": fingerprint,
            "state": "pending",
        }
        # Persist before POST: interruption or a lost response must not cause a duplicate.
        write_json(path, receipt)
        try:
            receipt["scheduleId"] = client.create_schedule(payload)
        except ReplizError:
            receipt["state"] = "unknown"
            write_json(path, receipt)
            raise ReplizError(
                "submission outcome is unknown; inspect the Repliz dashboard before any retry"
            ) from None
        receipt["state"] = "scheduled"
        write_json(path, receipt)
        return receipt


def daily_schedule_time(day):
    validate_day(day)
    value = os.getenv("REPLIZ_SCHEDULE_TIME", "")
    try:
        clock = datetime.strptime(value, "%H:%M")
    except ValueError:
        raise ReplizError("set REPLIZ_SCHEDULE_TIME to HH:MM in Asia/Jakarta") from None
    if clock.strftime("%H:%M") != value:
        raise ReplizError("REPLIZ_SCHEDULE_TIME must be HH:MM")
    date = datetime.strptime(day, "%Y%m%d")
    return date.replace(hour=clock.hour, minute=clock.minute, tzinfo=LOCAL_TZ)


def main():
    parser = argparse.ArgumentParser(prog="techbro repliz")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("accounts", help="List connected Threads accounts (read-only)")
    post = commands.add_parser("schedule", help="Preview a draft; --submit creates a live schedule")
    post.add_argument(
        "--date", default=day_stamp(), help="Draft date YYYYMMDD, default today in Jakarta"
    )
    post.add_argument(
        "--at", help="Publish datetime including timezone; otherwise REPLIZ_SCHEDULE_TIME"
    )
    post.add_argument(
        "--submit", action="store_true", help="Create a Repliz schedule that will publish"
    )
    status = commands.add_parser(
        "status", help="Read local submission receipts (not publish confirmation)"
    )
    status.add_argument("--date", default=day_stamp())
    args = parser.parse_args()
    try:
        if args.command == "accounts":
            with ReplizClient.from_env() as client:
                result = client.accounts()
        elif args.command == "status":
            validate_day(args.date)
            folder = Settings.from_env().data_dir / "repliz"
            result = [
                json.loads(path.read_text())
                for path in sorted(folder.glob(f"schedule_{args.date}_*.json"))
            ]
        else:
            scheduled = parse_schedule_time(args.at) if args.at else daily_schedule_time(args.date)
            payload = build_payload(args.date, os.getenv("REPLIZ_ACCOUNT_ID", ""), scheduled)
            if args.submit:
                with ReplizClient.from_env() as client:
                    result = schedule(args.date, payload, client)
            else:
                if scheduled <= datetime.now(UTC):
                    raise ReplizError("schedule time must be in the future")
                result = {"mode": "preview", "payload": payload}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ReplizError, OSError, ValueError) as exc:
        # Generic filesystem/JSON failures can contain paths or data, so redact them.
        message = (
            str(exc)
            if isinstance(exc, ReplizError)
            else "local submission data could not be read or written"
        )
        print(f"[error] {message}", file=sys.stderr)
        return 1
