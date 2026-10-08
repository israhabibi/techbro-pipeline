import fcntl
import subprocess
import sys

import pytest

from techbro_pipeline import demo, pipeline
from techbro_pipeline.config import day_stamp, write_json
from techbro_pipeline.web.pipeline_status import build_status


def test_pipeline_stops_at_failed_stage_and_uses_current_interpreter(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    calls = []

    def stage(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if len(calls) == 2 else 0, "stage output")

    monkeypatch.setattr(pipeline.subprocess, "run", stage)
    assert pipeline.run() == 1
    assert len(calls) == 2
    assert all(command[0] == sys.executable for command in calls)
    log = (data / "pipeline.log").read_text()
    assert "FAILED 2" in log
    assert "=== DONE" not in log
    assert build_status(str(data), day_stamp())["overall"] == "fail"


def test_pipeline_rejects_overlapping_run(isolated_runtime):
    data, _ = isolated_runtime
    data.mkdir()
    with (data / ".pipeline.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert pipeline.run() == 1


def test_pipeline_timeout_is_recorded_as_failure(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 900)

    monkeypatch.setattr(pipeline.subprocess, "run", timeout)
    assert pipeline.run() == 1
    assert "=== FAILED 1 ===" in (data / "pipeline.log").read_text()


def test_in_progress_status_is_never_ok(isolated_runtime):
    data, _ = isolated_runtime
    data.mkdir()
    (data / "pipeline.log").write_text("=== [1/5] scan.py ===\nscanning\n")
    assert build_status(str(data), day_stamp())["overall"] == "pending"


def test_completed_run_with_missing_artifacts_is_failure(isolated_runtime):
    data, _ = isolated_runtime
    data.mkdir()
    log = []
    for index in range(1, 6):
        log.extend([f"=== [{index}/5] stage ===", "output"])
    log.append("=== DONE demo ===")
    (data / "pipeline.log").write_text("\n".join(log))
    assert build_status(str(data), day_stamp())["overall"] == "fail"


def test_status_does_not_mistake_an_old_run_for_today(isolated_runtime):
    data, _ = isolated_runtime
    data.mkdir()
    (data / "pipeline.log").write_text(
        "=== RUN 20000101 ===\n=== [1/5] scan ===\noutput\n=== DONE demo ===\n"
    )
    assert build_status(str(data), day_stamp())["overall"] == "warn"


def test_demo_runs_entire_offline_pipeline_and_reports_ok(isolated_runtime):
    data, dataset = isolated_runtime
    assert demo.main() == 0
    status = build_status(str(data), day_stamp())
    assert status["overall"] == "ok"
    assert all(stage["artifact"]["ok"] for stage in status["stages"])
    assert all(
        (dataset / name).is_file()
        for name in ("techbro_tweets.csv", "techbro_topics.csv", "techbro_activity.csv")
    )


def test_demo_refuses_to_replace_existing_feed(isolated_runtime):
    import pytest

    data, _ = isolated_runtime
    write_json(data / "feed" / f"feed_{day_stamp()}.json", {"tweets": []})
    with pytest.raises(SystemExit, match="refuses"):
        demo.main()


def test_default_pipeline_never_schedules_posts(monkeypatch):
    calls = []

    def stage(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, "completed")

    monkeypatch.setattr(pipeline.subprocess, "run", stage)
    assert pipeline.run() == 0
    assert len(calls) == 5
    assert all("repliz" not in command for command in calls)


@pytest.mark.parametrize("publish_code", [0, 1])
def test_opt_in_schedules_only_after_all_stages_and_propagates_failure(
    isolated_runtime, monkeypatch, publish_code
):
    data, _ = isolated_runtime
    monkeypatch.setenv("REPLIZ_AUTO_SCHEDULE", "true")
    monkeypatch.setenv("REPLIZ_SCHEDULE_TIME", "10:00")
    calls = []

    def stage(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command, publish_code if "repliz" in command else 0, "completed"
        )

    monkeypatch.setattr(pipeline.subprocess, "run", stage)
    assert pipeline.run() == publish_code
    assert len(calls) == 6
    assert calls[-1][3:5] == ["repliz", "schedule"]
    assert "--submit" in calls[-1]
    assert calls[-1][calls[-1].index("--date") + 1] == day_stamp()
    log = (data / "pipeline.log").read_text()
    if publish_code:
        assert "=== FAILED Repliz ===" in log
        assert "=== DONE" not in log
        assert build_status(str(data), day_stamp())["overall"] == "fail"
    else:
        assert "=== DONE" in log


def test_failed_collection_never_reaches_repliz(monkeypatch):
    monkeypatch.setenv("REPLIZ_AUTO_SCHEDULE", "true")
    calls = []

    def stage(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1, "failed")

    monkeypatch.setattr(pipeline.subprocess, "run", stage)
    assert pipeline.run() == 1
    assert len(calls) == 1 and "repliz" not in calls[0]


def test_missing_daily_publish_time_returns_failure(isolated_runtime, monkeypatch):
    data, _ = isolated_runtime
    monkeypatch.setenv("REPLIZ_AUTO_SCHEDULE", "true")
    monkeypatch.setattr(
        pipeline.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "completed"),
    )
    assert pipeline.run() == 1
    assert "=== FAILED Repliz ===" in (data / "pipeline.log").read_text()
