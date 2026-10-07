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
    monkeypatch.setattr(smoke.subprocess, "run", lambda *args, **kwargs: None)
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
