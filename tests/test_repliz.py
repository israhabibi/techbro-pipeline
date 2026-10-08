"""Observable publishing behavior, with synthetic credentials and a fake API."""

import fcntl
import json
import sys
from datetime import UTC, datetime

import httpx
import pytest

from techbro_pipeline import cli, repliz
from techbro_pipeline.config import write_json

DAY = "20310102"
AT = "2031-01-02T10:00:00+07:00"
ACCOUNT = "synthetic-threads-id"


@pytest.fixture
def draft(isolated_runtime):
    data, _ = isolated_runtime
    path = data / "threads" / f"threads_draft_{DAY}.json"
    write_json(path, {"date": DAY, "parts": [{"text": "1/2 Opening"}, {"text": "2/2 Closing"}]})
    return path


def payload():
    return repliz.build_payload(DAY, ACCOUNT, repliz.parse_schedule_time(AT))


def fake_api(calls, *, post_status=200, post_json=None, timeout=False, connected=True):
    def handle(request):
        calls.append(request)
        if request.url.path == "/public/account":
            return httpx.Response(
                200,
                json={
                    "docs": [{"_id": ACCOUNT, "type": "threads", "isConnected": connected}],
                    "totalPages": 1,
                },
            )
        if timeout:
            raise httpx.ReadTimeout("secret-value-must-not-be-printed", request=request)
        return httpx.Response(
            post_status, json=post_json if post_json is not None else {"scheduleId": "schedule-1"}
        )

    return repliz.ReplizClient("fake-access", "fake-secret", transport=httpx.MockTransport(handle))


def test_preview_needs_no_keys_creates_no_receipt_and_preserves_reply_order(
    draft, monkeypatch, capsys
):
    monkeypatch.setenv("REPLIZ_ACCOUNT_ID", ACCOUNT)
    assert cli.main(["repliz", "schedule", "--date", DAY, "--at", AT]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "preview"
    post = result["payload"]
    assert post["description"] == "1/2 Opening"
    assert [reply["description"] for reply in post["replies"]] == ["2/2 Closing"]
    assert post["scheduleAt"] == "2031-01-02T03:00:00Z"
    assert post["type"] == "text" and post["medias"] == []
    assert not repliz.receipt_path(DAY, ACCOUNT).exists()


@pytest.mark.parametrize("day", ["../20310102", "20311301", "203112", "2031012"])
def test_invalid_date_is_rejected(day):
    with pytest.raises(repliz.ReplizError, match="YYYYMMDD"):
        repliz.validate_day(day)


@pytest.mark.parametrize("at", ["tomorrow", "2031-01-02", "2031-01-02T10:00:00"])
def test_schedule_requires_explicit_timezone(at):
    with pytest.raises(repliz.ReplizError):
        repliz.parse_schedule_time(at)


def test_missing_requested_draft_never_falls_back_to_previous_day(draft):
    with pytest.raises(repliz.ReplizError, match="missing"):
        repliz.build_payload("20310103", ACCOUNT, repliz.parse_schedule_time(AT))


@pytest.mark.parametrize("parts", [[], [{"text": ""}], [{"text": 7}], [{"text": "🙂" * 126}]])
def test_invalid_or_overlength_draft_is_rejected_without_truncation(draft, parts):
    write_json(draft, {"date": DAY, "parts": parts})
    with pytest.raises(repliz.ReplizError):
        payload()


def test_exact_500_byte_unicode_caption_is_supported(draft):
    write_json(draft, {"date": DAY, "parts": [{"text": "🙂" * 125}]})
    assert payload()["description"] == "🙂" * 125


def test_mismatched_draft_date_is_rejected(draft):
    write_json(draft, {"date": "20310101", "parts": [{"text": "Wrong day"}]})
    with pytest.raises(repliz.ReplizError, match="does not match"):
        payload()


def test_submission_persists_receipt_and_rerun_makes_no_network_calls(draft):
    calls = []
    with fake_api(calls) as client:
        receipt = repliz.schedule(DAY, payload(), client)
        assert repliz.schedule(DAY, payload(), client) == receipt
    assert [call.method for call in calls] == ["GET", "POST"]
    assert calls[0].url.host == "api.repliz.com"
    assert calls[0].url.params["types[0]"] == "threads"
    assert calls[0].headers["Authorization"].startswith("Basic ")
    assert json.loads(calls[1].content) == payload()
    assert receipt["state"] == "scheduled" and receipt["scheduleId"] == "schedule-1"
    assert json.loads(repliz.receipt_path(DAY, ACCOUNT).read_text()) == receipt
    assert "fake-secret" not in repliz.receipt_path(DAY, ACCOUNT).read_text()


def test_changed_content_cannot_create_second_schedule_for_same_day(draft):
    calls = []
    with fake_api(calls) as client:
        repliz.schedule(DAY, payload(), client)
        write_json(draft, {"date": DAY, "parts": [{"text": "Changed"}]})
        with pytest.raises(repliz.ReplizError, match="already recorded"):
            repliz.schedule(DAY, payload(), client)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "options", [{"timeout": True}, {"post_status": 500}, {"post_status": 401}, {"post_json": {}}]
)
def test_uncertain_submission_blocks_retry(draft, options):
    calls = []
    with fake_api(calls, **options) as client:
        with pytest.raises(repliz.ReplizError, match="unknown"):
            repliz.schedule(DAY, payload(), client)
        with pytest.raises(repliz.ReplizError, match="already recorded"):
            repliz.schedule(DAY, payload(), client)
    assert len(calls) == 2
    assert json.loads(repliz.receipt_path(DAY, ACCOUNT).read_text())["state"] == "unknown"


def test_disconnected_account_creates_no_schedule_or_receipt(draft):
    calls = []
    with fake_api(calls, connected=False) as client:
        with pytest.raises(repliz.ReplizError, match="connected Threads"):
            repliz.schedule(DAY, payload(), client)
    assert len(calls) == 1
    assert not repliz.receipt_path(DAY, ACCOUNT).exists()


def test_past_schedule_rejected_before_any_network_request(draft):
    post = payload()
    post["scheduleAt"] = "2000-01-01T00:00:00Z"
    calls = []
    with fake_api(calls) as client:
        with pytest.raises(repliz.ReplizError, match="future"):
            repliz.schedule(DAY, post, client)
    assert calls == []


def test_incomplete_receipt_from_interruption_blocks_second_post(draft):
    write_json(repliz.receipt_path(DAY, ACCOUNT), {"state": "pending"})
    calls = []
    with fake_api(calls) as client, pytest.raises(repliz.ReplizError, match="already recorded"):
        repliz.schedule(DAY, payload(), client)
    assert not calls


def test_overlapping_submission_is_rejected(draft):
    path = repliz.receipt_path(DAY, ACCOUNT)
    path.parent.mkdir(parents=True)
    calls = []
    with path.with_suffix(".lock").open("a") as lock, fake_api(calls) as client:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(repliz.ReplizError, match="active"):
            repliz.schedule(DAY, payload(), client)
    assert not calls


def test_account_listing_paginates_and_excludes_token_fields():
    calls = []

    def handle(request):
        page = int(request.url.params["page"])
        calls.append(page)
        return httpx.Response(
            200,
            json={
                "docs": [
                    {
                        "_id": f"account-{page}",
                        "type": "threads",
                        "isConnected": True,
                        "username": "fictional",
                        "token": "do-not-display",
                    }
                ],
                "totalPages": 2,
                "hasNextPage": page == 1,
            },
        )

    with repliz.ReplizClient("fake", "fake", transport=httpx.MockTransport(handle)) as client:
        accounts = client.accounts()
    assert calls == [1, 2]
    assert [a["id"] for a in accounts] == ["account-1", "account-2"]
    assert "do-not-display" not in json.dumps(accounts)


def test_http_errors_do_not_show_response_body():
    def handle(request):
        return httpx.Response(403, text="secret from server")

    with repliz.ReplizClient("fake", "fake", transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(repliz.ReplizError, match="HTTP 403") as error:
            client.accounts()
    assert "secret" not in str(error.value)


def test_missing_keys_fail_with_instructions_without_reading_credentials(monkeypatch, capsys):
    assert cli.main(["repliz", "accounts"]) == 1
    assert "REPLIZ_ACCESS_KEY" in capsys.readouterr().err


def test_local_status_requires_no_keys_or_network(draft, capsys):
    write_json(repliz.receipt_path(DAY, ACCOUNT), {"state": "pending"})
    assert cli.main(["repliz", "status", "--date", DAY]) == 0
    assert json.loads(capsys.readouterr().out) == [{"state": "pending"}]


def test_daily_schedule_time_is_jakarta_and_validates_input(monkeypatch):
    monkeypatch.setenv("REPLIZ_SCHEDULE_TIME", "10:00")
    assert repliz.daily_schedule_time(DAY).astimezone(UTC) == datetime(2031, 1, 2, 3, tzinfo=UTC)
    monkeypatch.setenv("REPLIZ_SCHEDULE_TIME", "tomorrow")
    with pytest.raises(repliz.ReplizError, match="HH:MM"):
        repliz.daily_schedule_time(DAY)


def test_submit_flag_is_required_for_real_schedule(draft, monkeypatch, capsys):
    calls = []
    monkeypatch.setenv("REPLIZ_ACCOUNT_ID", ACCOUNT)
    monkeypatch.setattr(repliz.ReplizClient, "from_env", lambda: fake_api(calls))
    assert cli.main(["repliz", "schedule", "--date", DAY, "--at", AT, "--submit"]) == 0
    assert json.loads(capsys.readouterr().out)["scheduleId"] == "schedule-1"
    assert len(calls) == 2


def test_cli_restores_arguments_after_repliz_command(monkeypatch):
    original = sys.argv
    monkeypatch.setattr(repliz, "main", lambda: 0)
    assert cli.main(["repliz", "accounts"]) == 0
    assert sys.argv is original
