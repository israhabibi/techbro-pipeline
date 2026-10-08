import json
import subprocess
import sys

import pytest

from techbro_pipeline import cli, pipeline, workflow
from techbro_pipeline.config import day_stamp, write_json


def configure(monkeypatch, provider="mock"):
    monkeypatch.setattr(workflow, "invoke", lambda *args: [])
    return workflow.setup(provider)


def make_draft(data, day="20261008", texts=("First part", "Reply")):
    path = data / "threads" / f"threads_draft_{day}.json"
    write_json(path, {"date": day, "parts": [{"text": text} for text in texts]})
    return path


def test_setup_uses_explicit_identity_without_copying_tokens(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    monkeypatch.setenv("THREADS_USER_ID", "synthetic-user")
    monkeypatch.setenv("THREADS_ACCESS_TOKEN", "synthetic-private-token")
    result = configure(monkeypatch, "native")
    path = data / "workflow" / "workspace.json"
    stored = path.read_text()
    assert "synthetic-private-token" not in stored
    assert json.loads(stored)["accounts"][0]["token_env"] == "THREADS_ACCESS_TOKEN"
    assert result["provider"] == "native"
    assert path.stat().st_mode & 0o777 == 0o600
    assert not (path.parent / "credentials.json").exists()
    assert workflow.setup("native") == result
    monkeypatch.setenv("THREADS_USER_ID", "different-user")
    with pytest.raises(workflow.WorkflowError, match="different account"):
        workflow.setup("native")
    assert path.read_text() == stored


def test_setup_requires_configured_identity_and_does_not_discover_credentials(isolated_runtime):
    data, _ = isolated_runtime
    with pytest.raises(workflow.WorkflowError, match="explicit"):
        workflow.setup("native")
    assert not (data / "workflow").exists()


def test_enqueue_captures_all_parts_and_only_creates_a_draft(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    configure(monkeypatch)
    source = make_draft(data)
    calls = []

    def invoke(*args):
        calls.append(args)
        if args[0] == "import":
            captured = json.loads(args[2].read_text())
            assert captured["parts"] == [{"text": "First part"}, {"text": "Reply"}]
            # Changing the original cannot switch the captured content mid-import.
            make_draft(data, texts=("Changed later",))
        return {"job_id": "synthetic-job"}

    monkeypatch.setattr(workflow, "invoke", invoke)
    result = workflow.draft_operation("enqueue", "20261008", at="2026-10-09T09:00:00+07:00")
    assert result["job_id"] == "synthetic-job" and result["approval_required"] is True
    assert [args[0] for args in calls] == ["import", "enqueue"]
    assert "daily-20261008" in calls[0]
    assert calls[1][-2:] == ("--at", "2026-10-09T09:00:00+07:00")
    assert source.is_file()
    assert not list(workflow.home().glob("draft-*"))


@pytest.mark.parametrize("day", ["20261007", "../../bad", "20260230"])
def test_requested_date_never_falls_back_to_another_draft(isolated_runtime, monkeypatch, day):
    data, _ = isolated_runtime
    configure(monkeypatch)
    make_draft(data)
    monkeypatch.setattr(workflow, "invoke", lambda *args: pytest.fail("must not enqueue"))
    with pytest.raises(workflow.WorkflowError):
        workflow.draft_operation("enqueue", day)


def test_draft_date_mismatch_is_rejected(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    configure(monkeypatch)
    path = make_draft(data)
    write_json(path, {"date": "20261007", "parts": [{"text": "Wrong date"}]})
    with pytest.raises(workflow.WorkflowError, match="date does not match"):
        workflow.draft_operation("enqueue", "20261008")


@pytest.mark.parametrize("folder,prefix", [("meta", "publish"), ("repliz", "schedule")])
def test_legacy_receipts_block_enqueue_but_allow_offline_preview(
    isolated_runtime, monkeypatch, folder, prefix
):
    data, _ = isolated_runtime
    configure(monkeypatch)
    make_draft(data)
    write_json(data / folder / f"{prefix}_20261008_synthetic.json", {"state": "unknown"})
    calls = []
    monkeypatch.setattr(workflow, "invoke", lambda *args: calls.append(args) or {})
    with pytest.raises(workflow.WorkflowError, match="legacy publishing receipt"):
        workflow.draft_operation("enqueue", "20261008")
    assert calls == []
    workflow.draft_operation("preview", "20261008")
    assert [args[0] for args in calls] == ["import", "preview"]


@pytest.mark.parametrize("flag", ["THREADS_AUTO_PUBLISH", "REPLIZ_AUTO_SCHEDULE"])
def test_old_auto_publisher_blocks_workflow_dispatch(isolated_runtime, monkeypatch, capsys, flag):
    configure(monkeypatch)
    monkeypatch.setenv(flag, "true")
    monkeypatch.setattr(workflow, "invoke", lambda *args: pytest.fail("must not dispatch"))
    assert cli.main(["workflow", "worker"]) == 1
    assert "disable THREADS_AUTO_PUBLISH" in capsys.readouterr().err


def test_subprocess_failure_and_timeout_do_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("AI_WORKFLOW_EXECUTABLE", "/synthetic/path with spaces/ai-workflow")
    calls = []

    def failed(command, **kwargs):
        calls.append(command)
        assert kwargs["capture_output"] is True
        assert "shell" not in kwargs
        return subprocess.CompletedProcess(command, 1, "synthetic-private-token", "secret stderr")

    monkeypatch.setattr(workflow.subprocess, "run", failed)
    with pytest.raises(workflow.WorkflowError) as failure:
        workflow.invoke("jobs")
    assert "private-token" not in str(failure.value)
    assert "secret stderr" not in str(failure.value)
    assert calls[0][0] == "/synthetic/path with spaces/ai-workflow"

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 300, output="synthetic-private-token")

    monkeypatch.setattr(workflow.subprocess, "run", timeout)
    with pytest.raises(workflow.WorkflowError, match="could not run"):
        workflow.invoke("jobs")


def test_approve_and_status_use_returned_job_id(isolated_runtime, monkeypatch, capsys):
    configure(monkeypatch)
    calls = []
    monkeypatch.setattr(workflow, "invoke", lambda *args: calls.append(args) or {"state": "queued"})
    original = sys.argv
    assert cli.main(["workflow", "approve", "synthetic-job", "--reviewer", "editor"]) == 0
    assert calls == [("approve", "synthetic-job", "--reviewer", "editor")]
    assert json.loads(capsys.readouterr().out)["state"] == "queued"
    assert sys.argv is original
    assert cli.main(["workflow", "status", "synthetic-job"]) == 0
    assert calls[-1] == ("status", "synthetic-job")


def test_enabled_pipeline_queues_only_after_all_stages(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    configure(monkeypatch)
    monkeypatch.setenv("AI_WORKFLOW_AUTO_ENQUEUE", "true")
    calls = []

    def stage(command, **kwargs):
        calls.append(command[3])
        return subprocess.CompletedProcess(command, 0, "completed")

    def enqueue(command, day):
        assert command == "enqueue" and day == day_stamp()
        calls.append("enqueue")
        return {"job_id": "synthetic-job"}

    monkeypatch.setattr(pipeline.subprocess, "run", stage)
    monkeypatch.setattr(workflow, "draft_operation", enqueue)
    assert pipeline.run() == 0
    assert calls == ["scan", "sources", "topics", "threads", "dataset", "enqueue"]
    assert "approval required" in (data / "pipeline.log").read_text()


def test_enqueue_failure_marks_pipeline_failed(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    configure(monkeypatch)
    monkeypatch.setenv("AI_WORKFLOW_AUTO_ENQUEUE", "true")
    monkeypatch.setattr(
        pipeline.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "done")
    )

    def failure(*args, **kwargs):
        raise workflow.WorkflowError("synthetic enqueue failure")

    monkeypatch.setattr(workflow, "draft_operation", failure)
    assert pipeline.run() == 1
    log = (data / "pipeline.log").read_text()
    assert "=== FAILED ai-workflow ===" in log and "=== DONE" not in log


@pytest.mark.parametrize("flag", ["THREADS_AUTO_PUBLISH", "REPLIZ_AUTO_SCHEDULE"])
def test_workflow_and_old_publisher_conflict_before_collection(monkeypatch, flag):
    monkeypatch.setenv("AI_WORKFLOW_AUTO_ENQUEUE", "true")
    monkeypatch.setenv(flag, "true")
    monkeypatch.setattr(
        pipeline.subprocess, "run", lambda *a, **kw: pytest.fail("must not collect")
    )
    assert pipeline.run() == 1


def test_failed_stage_never_enqueues(isolated_runtime, monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("AI_WORKFLOW_AUTO_ENQUEUE", "true")
    monkeypatch.setattr(
        pipeline.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, "failed")
    )
    monkeypatch.setattr(
        workflow, "draft_operation", lambda *a, **kw: pytest.fail("must not enqueue")
    )
    assert pipeline.run() == 1
