import json
import subprocess
from pathlib import Path

import pytest

from techbro_pipeline import cli, pipeline, quick, workflow


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(workflow, "check_workspace", lambda: None)


def test_queue_shortcut_reports_empty_and_lists_jobs(configured, monkeypatch, capsys):
    monkeypatch.setattr(workflow, "invoke", lambda *args: [])
    assert cli.main(["antrean"]) == 0
    assert capsys.readouterr().out.strip() == "Antrean kosong."
    monkeypatch.setattr(
        workflow,
        "invoke",
        lambda *args: [{"id": "synthetic-job", "state": "draft", "release_key": "daily-20310102"}],
    )
    assert cli.main(["antrean"]) == 0
    assert "draft | daily-20310102 | synthetic-job" in capsys.readouterr().out


def test_look_at_job_shows_saved_release_without_approval(configured, monkeypatch, capsys):
    calls = []

    def invoke(*args):
        calls.append(args)
        return {
            "account": {"name": "synthetic-account", "provider": "mock"},
            "post": {"text": "Original queued opening", "replies": ["Original reply"]},
            "job": {"id": "synthetic-job", "state": "draft"},
        }

    monkeypatch.setattr(workflow, "invoke", invoke)
    assert cli.main(["lihat", "synthetic-job"]) == 0
    output = capsys.readouterr().out
    assert "Original queued opening" in output and "Original reply" in output
    assert "Bagian 2/2" in output and "synthetic-account" in output
    assert calls == [("preview-job", "synthetic-job")]


def test_look_at_date_uses_requested_draft(configured, monkeypatch, capsys):
    calls = []

    def preview(command, day):
        calls.append((command, day))
        return {
            "account": {"name": "synthetic-account", "provider": "mock"},
            "post": {"text": "Opening", "replies": []},
        }

    monkeypatch.setattr(workflow, "draft_operation", preview)
    assert cli.main(["lihat", "20310102"]) == 0
    assert calls == [("preview", "20310102")]
    assert "Opening" in capsys.readouterr().out


def test_approve_shortcut_records_reviewer_without_dispatch(configured, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(quick.getpass, "getuser", lambda: "synthetic-editor")
    monkeypatch.setattr(
        workflow, "invoke", lambda *args: calls.append(args) or {"id": "synthetic-job"}
    )
    assert cli.main(["setujui", "synthetic-job"]) == 0
    assert calls == [("approve", "synthetic-job", "--reviewer", "synthetic-editor")]
    assert "Disetujui" in capsys.readouterr().out


def test_send_shortcut_only_runs_approved_worker(configured, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(workflow, "invoke", lambda *args: calls.append(args) or [])
    assert cli.main(["kirim"]) == 0
    assert calls == [("worker", "--steps", 20)]
    assert "Tidak ada posting" in capsys.readouterr().out


@pytest.mark.parametrize("state", ["failed", "needs_review"])
def test_send_shortcut_propagates_failed_or_uncertain_result(
    configured, monkeypatch, capsys, state
):
    monkeypatch.setattr(workflow, "invoke", lambda *args: [{"id": "synthetic-job", "state": state}])
    assert cli.main(["kirim"]) == 1
    assert state in capsys.readouterr().out


def test_send_reports_latest_state_and_pending_poll(configured, monkeypatch, capsys):
    monkeypatch.setattr(
        workflow,
        "invoke",
        lambda *args: [
            {"id": "synthetic-job", "state": "queued"},
            {"id": "synthetic-job", "state": "published"},
            {"id": "other-job", "state": "queued"},
        ],
    )
    assert cli.main(["kirim"]) == 0
    output = capsys.readouterr().out
    assert "published | synthetic-job" in output
    assert "queued | synthetic-job" not in output
    assert "beberapa detik" in output


def test_prepare_shortcut_runs_pipeline(monkeypatch):
    monkeypatch.setattr(pipeline, "run", lambda: 7)
    assert cli.main(["siapkan"]) == 7


def test_launcher_resolves_symlink_and_loads_its_own_environment(tmp_path):
    project = tmp_path / "project with spaces"
    binaries = project / ".venv" / "bin"
    binaries.mkdir(parents=True)
    launcher = project / "techbro"
    launcher.write_text((Path(__file__).resolve().parents[1] / "techbro").read_text())
    launcher.chmod(0o755)
    executable = binaries / "techbro"
    executable.write_text(
        "#!/usr/bin/env python3\nimport json, os, sys\nprint(json.dumps({'cwd': os.getcwd(), 'args': sys.argv[1:]}))\n"
    )
    executable.chmod(0o755)
    (project / ".env").write_text("SYNTHETIC=fixture\n")
    caller = tmp_path / "caller"
    caller.mkdir()
    link = caller / "techbro"
    link.symlink_to(launcher)
    result = subprocess.run([str(link)], cwd=caller, capture_output=True, text=True, check=True)
    output = json.loads(result.stdout)
    assert output == {"cwd": str(project), "args": ["--env-file", str(project / ".env"), "antrean"]}
    result = subprocess.run(
        [str(link), "lihat", "20310102"], cwd=caller, capture_output=True, text=True, check=True
    )
    assert json.loads(result.stdout)["args"][-2:] == ["lihat", "20310102"]


def test_launcher_reports_missing_runtime_without_installing(tmp_path):
    launcher = tmp_path / "techbro"
    launcher.write_text((Path(__file__).resolve().parents[1] / "techbro").read_text())
    launcher.chmod(0o755)
    result = subprocess.run([str(launcher)], capture_output=True, text=True)
    assert result.returncode == 127
    assert "uv sync --locked" in result.stderr
