"""Threads publishing behavior with a fake Meta API and synthetic tokens."""

import fcntl
import json
from urllib.parse import parse_qs

import httpx
import pytest
from dotenv import dotenv_values

from techbro_pipeline import cli, meta
from techbro_pipeline.config import write_json

DAY = "20310102"
USER_ID = "123456789"
TOKEN = "synthetic-token"


@pytest.fixture
def draft(isolated_runtime):
    data, _ = isolated_runtime
    path = data / "threads" / f"threads_draft_{DAY}.json"
    write_json(path, {"date": DAY, "parts": [{"text": "1/2 Opening"}, {"text": "2/2 Closing"}]})
    return path


class FakeMeta:
    def __init__(self):
        self.calls = []
        self.creates = []
        self.publishes = []
        self.user_id = USER_ID
        self.fail_create = None
        self.fail_publish = None
        self.invalid_publish = False
        self.statuses = []
        self.refreshes = 0

    def handle(self, request):
        self.calls.append(request)
        path = request.url.path.removeprefix("/v1.0/").lstrip("/")
        if path == "me":
            return httpx.Response(200, json={"id": self.user_id, "username": "fictional_builder"})
        if path == "me/threads":
            self.creates.append(parse_qs(request.content.decode()))
            if len(self.creates) == self.fail_create:
                raise httpx.ReadTimeout("do-not-display-token", request=request)
            return httpx.Response(200, json={"id": f"container-{len(self.creates)}"})
        if path == "me/threads_publish":
            self.publishes.append(parse_qs(request.content.decode()))
            if len(self.publishes) == self.fail_publish:
                raise httpx.ReadTimeout("do-not-display-token", request=request)
            return httpx.Response(
                200, json={} if self.invalid_publish else {"id": f"post-{len(self.publishes)}"}
            )
        if path == "refresh_access_token":
            self.refreshes += 1
            return httpx.Response(
                200, json={"access_token": "new-synthetic-token", "expires_in": 5184000}
            )
        if path.startswith("container-"):
            return httpx.Response(
                200, json={"status": self.statuses.pop(0) if self.statuses else "FINISHED"}
            )
        raise AssertionError("Unexpected fake API request")

    def client(self):
        return meta.ThreadsClient(
            TOKEN, transport=httpx.MockTransport(self.handle), sleep=lambda _: None
        )


def test_preview_needs_no_token_performs_no_network_and_creates_no_receipt(draft, capsys):
    assert cli.main(["meta", "publish", "--date", DAY]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "preview" and result["userId"] is None
    assert [part["text"] for part in result["parts"]] == ["1/2 Opening", "2/2 Closing"]
    assert not meta.receipt_path(DAY, USER_ID).exists()


def test_public_media_url_requires_https_public_host():
    filename = f"techbro-{DAY}-120000-abcd1234.mp4"
    assert meta.public_media_url("https://videos.example.com/app/", DAY, filename) == (
        f"https://videos.example.com/app/api/daily/{DAY}/video/{filename}"
    )
    for invalid in ("http://videos.example.com", "https://localhost", "https://127.0.0.1"):
        with pytest.raises(meta.ThreadsError):
            meta.public_media_url(invalid, DAY, filename)


def test_video_publish_records_receipt_and_does_not_publish_twice(isolated_runtime):
    _, _ = isolated_runtime
    media = isolated_runtime[0] / "videos" / DAY
    media.mkdir(parents=True)
    filename = f"techbro-{DAY}-120000-abcd1234.mp4"
    video = media / filename
    video.write_bytes(b"synthetic video bytes")
    fake = FakeMeta()
    client = fake.client()
    url = f"https://videos.example.com/api/daily/{DAY}/video/{filename}"

    first = meta.publish_video(DAY, filename, "Caption", video, url, client, USER_ID)
    second = meta.publish_video(DAY, filename, "Caption", video, url, client, USER_ID)

    assert first["state"] == second["state"] == "published"
    assert first["postId"] == second["postId"] == "post-1"
    assert len(fake.creates) == len(fake.publishes) == 1
    assert fake.creates[0] == {
        "media_type": ["VIDEO"],
        "video_url": [url],
        "text": ["Caption"],
    }


@pytest.mark.parametrize("day", ["../20310102", "20311301", "203112", "2031012"])
def test_date_requires_exact_calendar_format(day):
    with pytest.raises(meta.ThreadsError, match="YYYYMMDD"):
        meta.read_draft(day)


def test_requested_draft_never_falls_back_to_older_day(draft):
    with pytest.raises(meta.ThreadsError, match="missing"):
        meta.read_draft("20310103")


@pytest.mark.parametrize(
    "draft_value",
    [
        [],
        {"date": DAY, "parts": []},
        {"date": DAY, "parts": [{"text": ""}]},
        {"date": DAY, "parts": [{"text": 5}]},
        {"date": DAY, "parts": [{"text": "t" * 501}]},
        {"date": "20310101", "parts": [{"text": "Wrong day"}]},
    ],
)
def test_invalid_draft_is_rejected_before_publishing(draft, draft_value):
    write_json(draft, draft_value)
    with pytest.raises(meta.ThreadsError):
        meta.read_draft(DAY)


def test_exact_text_limit_preserves_the_reviewed_caption(draft):
    write_json(draft, {"date": DAY, "parts": [{"text": "t" * 500}]})
    assert meta.read_draft(DAY) == ["t" * 500]


def test_publisher_creates_then_publishes_parts_in_order_and_chains_reply_ids(draft):
    api = FakeMeta()
    with api.client() as client:
        result = meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert result["state"] == "published"
    assert [part["postId"] for part in result["parts"]] == ["post-1", "post-2"]
    assert api.creates == [
        {"media_type": ["TEXT"], "text": ["1/2 Opening"]},
        {"media_type": ["TEXT"], "text": ["2/2 Closing"], "reply_to_id": ["post-1"]},
    ]
    assert api.publishes == [{"creation_id": ["container-1"]}, {"creation_id": ["container-2"]}]
    assert all(call.url.host == "graph.threads.net" for call in api.calls)
    assert all(call.headers["Authorization"] == "Bearer " + TOKEN for call in api.calls)
    assert all(TOKEN not in str(call.url) for call in api.calls)
    assert all("auto_publish_text" not in post for post in api.creates)
    assert json.loads(meta.receipt_path(DAY, USER_ID).read_text()) == result
    assert TOKEN not in meta.receipt_path(DAY, USER_ID).read_text()


def test_repeating_completed_publication_only_reads_profile_and_does_not_repost(draft):
    api = FakeMeta()
    with api.client() as client:
        first = meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        assert meta.publish(DAY, meta.read_draft(DAY), client, USER_ID) == first
    assert len(api.creates) == len(api.publishes) == 2
    assert api.calls[-1].method == "GET" and api.calls[-1].url.path.endswith("/me")


def test_changed_draft_is_blocked_after_recorded_publication(draft):
    api = FakeMeta()
    with api.client() as client:
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        with pytest.raises(meta.ThreadsError, match="differs"):
            meta.publish(DAY, ["Changed"], client, USER_ID)
    assert len(api.creates) == len(api.publishes) == 2


@pytest.mark.parametrize("expected", ["", "different-user", "../account"])
def test_explicit_target_is_required_and_wrong_account_never_posts(draft, expected):
    api = FakeMeta()
    with api.client() as client, pytest.raises(meta.ThreadsError):
        meta.publish(DAY, meta.read_draft(DAY), client, expected)
    assert not api.creates and not api.publishes
    assert not meta.receipt_path(DAY, USER_ID).exists()


def test_lost_container_creation_response_can_resume_without_reposting_completed_root(draft):
    api = FakeMeta()
    api.fail_create = 2
    with api.client() as client:
        with pytest.raises(meta.ThreadsError, match="did not complete"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        assert len(api.publishes) == 1
        result = meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert result["state"] == "published"
    assert len(api.creates) == 3 and len(api.publishes) == 2
    assert api.creates[-1]["reply_to_id"] == ["post-1"]


@pytest.mark.parametrize("failed_part", [1, 2])
def test_lost_publish_response_blocks_retry_even_when_previous_parts_succeeded(draft, failed_part):
    api = FakeMeta()
    api.fail_publish = failed_part
    with api.client() as client:
        with pytest.raises(meta.ThreadsError, match="unknown"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        before = (len(api.creates), len(api.publishes))
        with pytest.raises(meta.ThreadsError, match="unknown"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        assert (len(api.creates), len(api.publishes)) == before
    receipt = json.loads(meta.receipt_path(DAY, USER_ID).read_text())
    assert receipt["state"] == "unknown" and receipt["parts"][failed_part - 1]["state"] == "unknown"


def test_publish_success_without_an_id_is_ambiguous_and_never_retried(draft):
    api = FakeMeta()
    api.invalid_publish = True
    with api.client() as client:
        with pytest.raises(meta.ThreadsError, match="unknown"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        with pytest.raises(meta.ThreadsError, match="unknown"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert len(api.publishes) == 1


def test_interruption_before_persisting_publish_result_blocks_duplicate(draft, monkeypatch):
    api = FakeMeta()
    real_write = meta.write_json

    def fail_after_publish(path, receipt):
        if receipt["parts"][0]["state"] == "published":
            raise OSError("simulated interruption")
        real_write(path, receipt)

    monkeypatch.setattr(meta, "write_json", fail_after_publish)
    with api.client() as client, pytest.raises(OSError):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    monkeypatch.setattr(meta, "write_json", real_write)
    with api.client() as client, pytest.raises(meta.ThreadsError, match="unknown"):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert len(api.publishes) == 1


def test_processing_timeout_resumes_same_container(draft):
    api = FakeMeta()
    api.statuses = ["IN_PROGRESS"] * 10
    with api.client() as client:
        with pytest.raises(meta.ThreadsError, match="still processing"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
        assert len(api.creates) == 1 and not api.publishes
        result = meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert result["state"] == "published"
    assert len(api.creates) == len(api.publishes) == 2


@pytest.mark.parametrize("status", ["ERROR", "EXPIRED", "PUBLISHED", None])
def test_unpublishable_container_never_reaches_publish_endpoint(draft, status):
    api = FakeMeta()
    api.statuses = [status]
    with api.client() as client, pytest.raises(meta.ThreadsError, match="not publishable"):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert not api.publishes


def test_overlapping_publisher_is_rejected(draft):
    path = meta.receipt_path(DAY, USER_ID)
    path.parent.mkdir(parents=True)
    api = FakeMeta()
    with path.with_suffix(".lock").open("a") as lock, api.client() as client:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(meta.ThreadsError, match="active"):
            meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert not api.creates and not api.publishes


@pytest.mark.parametrize("status", [401, 403, 500, 302])
def test_error_response_and_redirect_are_redacted(status):
    def handle(request):
        return httpx.Response(
            status,
            json={"error": {"message": "do-not-display-token"}},
            headers={"Location": "https://example.invalid"},
        )

    with meta.ThreadsClient(TOKEN, transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(meta.ThreadsError, match=f"HTTP {status}") as error:
            client.profile()
    assert "do-not-display-token" not in str(error.value)


def test_cli_profile_is_read_only_and_displays_only_identity(monkeypatch, capsys):
    api = FakeMeta()
    monkeypatch.setattr(meta.ThreadsClient, "from_env", lambda: api.client())
    assert cli.main(["meta", "profile"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == {"id": USER_ID, "username": "fictional_builder"}
    assert len(api.calls) == 1 and not api.creates


def test_missing_token_is_reported_without_reading_parent_configuration(capsys):
    assert cli.main(["meta", "profile"]) == 1
    assert "THREADS_ACCESS_TOKEN" in capsys.readouterr().err


def test_local_status_needs_no_token_or_network(draft, capsys):
    write_json(meta.receipt_path(DAY, USER_ID), {"state": "unknown"})
    assert cli.main(["meta", "status", "--date", DAY]) == 0
    assert json.loads(capsys.readouterr().out) == [{"state": "unknown"}]


def test_submit_flag_creates_real_publication_via_fake_api(draft, monkeypatch, capsys):
    api = FakeMeta()
    monkeypatch.setenv("THREADS_USER_ID", USER_ID)
    monkeypatch.setattr(meta.ThreadsClient, "from_env", lambda: api.client())
    assert cli.main(["meta", "publish", "--date", DAY, "--submit"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "published"
    assert len(api.publishes) == 2


def test_token_refresh_preserves_other_configuration_and_never_prints_new_token(
    tmp_path, monkeypatch, capsys
):
    api = FakeMeta()
    path = tmp_path / "synthetic.env"
    path.write_text(f"THREADS_ACCESS_TOKEN={TOKEN}\nTHREADS_APP_ID=12345\n", encoding="utf-8")
    monkeypatch.setattr(meta.ThreadsClient, "from_env", lambda: api.client())
    assert cli.main(["meta", "refresh", "--save-token", str(path)]) == 0
    output = capsys.readouterr().out
    assert "new-synthetic-token" not in output and TOKEN not in output
    assert json.loads(output) == {"refreshed": True, "expires_in": 5184000}
    assert dotenv_values(path)["THREADS_ACCESS_TOKEN"] == "new-synthetic-token"
    assert dotenv_values(path)["THREADS_APP_ID"] == "12345"
    assert path.stat().st_mode & 0o777 == 0o600
    assert api.refreshes == 1
    assert api.calls[-1].url.path == "/refresh_access_token"


def test_refresh_never_updates_an_unrelated_environment_file(tmp_path):
    api = FakeMeta()
    path = tmp_path / "unrelated.env"
    path.write_text("THREADS_ACCESS_TOKEN=different-token\n", encoding="utf-8")
    with api.client() as client, pytest.raises(meta.ThreadsError, match="matching"):
        meta.refresh_token_file(path, client)
    assert not api.calls
    assert path.read_text() == "THREADS_ACCESS_TOKEN=different-token\n"


@pytest.mark.parametrize(
    "change",
    [
        {"state": []},
        {"number": 99},
        {"state": "published", "postId": "post-99", "containerId": "container-99"},
    ],
)
def test_invalid_later_receipt_part_is_rejected_before_posting_root(draft, change):
    api = FakeMeta()
    api.fail_create = 1
    with api.client() as client, pytest.raises(meta.ThreadsError):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    path = meta.receipt_path(DAY, USER_ID)
    receipt = json.loads(path.read_text())
    receipt["parts"][1].update(change)
    write_json(path, receipt)
    before = len(api.creates)
    with api.client() as client, pytest.raises(meta.ThreadsError, match="receipt is invalid"):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    assert len(api.creates) == before and not api.publishes


def test_resume_uses_original_saved_draft_after_working_draft_changes(draft, monkeypatch, capsys):
    api = FakeMeta()
    api.fail_create = 2
    with api.client() as client, pytest.raises(meta.ThreadsError):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    write_json(draft, {"date": DAY, "parts": [{"text": "Different daily draft"}]})
    monkeypatch.setenv("THREADS_USER_ID", USER_ID)
    monkeypatch.setattr(meta.ThreadsClient, "from_env", lambda: api.client())
    assert cli.main(["meta", "publish", "--date", DAY, "--resume"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert [part["text"] for part in preview["parts"]] == ["1/2 Opening", "2/2 Closing"]
    assert len(api.publishes) == 1
    assert cli.main(["meta", "publish", "--date", DAY, "--resume", "--submit"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "published"
    assert api.creates[-1]["text"] == ["2/2 Closing"]
    assert len(api.publishes) == 2


def test_corrupted_saved_text_cannot_be_resumed(draft):
    api = FakeMeta()
    api.fail_create = 1
    with api.client() as client, pytest.raises(meta.ThreadsError):
        meta.publish(DAY, meta.read_draft(DAY), client, USER_ID)
    path = meta.receipt_path(DAY, USER_ID)
    receipt = json.loads(path.read_text())
    receipt["parts"][0]["text"] = "Tampered"
    write_json(path, receipt)
    with pytest.raises(meta.ThreadsError, match="content is invalid"):
        meta.recorded_draft(DAY, USER_ID)
