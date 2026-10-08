"""The verifier tolerates a server's transient startup connection reset."""

import importlib.util
import io
import json
from pathlib import Path
from types import SimpleNamespace


def test_smoke_retries_connection_reset_and_stops_server(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "smoke.py"
    spec = importlib.util.spec_from_file_location("techbro_smoke_verifier", path)
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    terminated = []
    server = SimpleNamespace(
        poll=lambda: None, terminate=lambda: terminated.append(True), wait=lambda **kwargs: 0
    )
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if "demo" in command:
            drafts = Path(kwargs["env"]["DATA_DIR"]) / "threads"
            drafts.mkdir(parents=True)
            (drafts / "threads_draft_20260101.json").write_text("{}")
        return SimpleNamespace(stdout='{"mode": "preview"}')

    monkeypatch.setattr(smoke.subprocess, "run", run)
    monkeypatch.setattr(smoke.subprocess, "Popen", lambda *args, **kwargs: server)
    monkeypatch.setattr(smoke.time, "sleep", lambda _: None)
    calls = []

    class Response(io.BytesIO):
        status = 200

    def request(url, **kwargs):
        calls.append(url)
        if len(calls) == 1:
            raise ConnectionResetError("server still starting")
        payload = (
            {"ok": True}
            if url.endswith("/health")
            else {"overall": "ok", "day": "20260101"}
            if url.endswith("/api/status")
            else {"total": 1}
        )
        return Response(
            b"<!doctype html>"
            if "/api/" not in url and not url.endswith("/health")
            else json.dumps(payload).encode()
        )

    monkeypatch.setattr(smoke.urllib.request, "urlopen", request)
    assert smoke.main() == 0
    assert calls[0] == calls[1]
    assert terminated == [True]
    assert "repliz" in commands[1] and "--submit" not in commands[1]


def test_clean_checkout_environment_excludes_publishing_configuration(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "smoke.py"
    spec = importlib.util.spec_from_file_location("techbro_smoke_environment", path)
    smoke = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(smoke)
    for name in (
        "REPLIZ_ACCESS_KEY",
        "REPLIZ_SECRET_KEY",
        "REPLIZ_ACCOUNT_ID",
        "REPLIZ_AUTO_SCHEDULE",
    ):
        monkeypatch.setenv(name, "synthetic")
    assert not any(name.startswith("REPLIZ_") for name in smoke.clean_environment())
