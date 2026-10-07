import sys

import pytest

from techbro_pipeline import cli, demo, scan


def test_cli_dispatches_demo_and_restores_arguments(monkeypatch):
    original = sys.argv
    monkeypatch.setattr(demo, "main", lambda: 0)
    assert cli.main(["demo"]) == 0
    assert sys.argv is original


def test_cli_scan_uses_page_setting_and_validates_bounds(monkeypatch):
    received = []
    monkeypatch.setattr(scan, "main", lambda pages: received.append(pages))
    monkeypatch.setenv("SCAN_PAGES", "4")
    assert cli.main(["scan"]) == 0
    assert received == [4]
    with pytest.raises(SystemExit):
        cli.main(["scan", "0"])


def test_serve_defaults_to_loopback_and_supports_port(monkeypatch):
    import uvicorn

    received = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: received.append(kwargs))
    assert cli.main(["serve", "--port", "9001"]) == 0
    assert received == [{"host": "127.0.0.1", "port": 9001}]


def test_cli_pipeline_dispatches_and_rejects_extra_arguments(monkeypatch):
    from techbro_pipeline import pipeline

    monkeypatch.setattr(pipeline, "run", lambda: 1)
    assert cli.main(["pipeline"]) == 1
    with pytest.raises(SystemExit):
        cli.main(["pipeline", "unknown"])


def test_environment_file_is_explicit_and_preserves_exported_values(tmp_path, monkeypatch):
    path = tmp_path / "demo.env"
    path.write_text("SCAN_PAGES=7\n", encoding="utf-8")
    received = []
    monkeypatch.setenv("SCAN_PAGES", "2")
    monkeypatch.setattr(scan, "main", lambda pages: received.append(pages))
    cli.main(["--env-file", str(path), "scan"])
    assert received == [2]
    with pytest.raises(SystemExit):
        cli.main(["--env-file", str(tmp_path / "absent"), "scan"])
