"""Start an installed package with synthetic data and verify real HTTP responses."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def clean_environment():
    env = os.environ.copy()
    for key in list(env):
        if key in {
            "DATA_DIR",
            "DATASET_DIR",
            "CREDS_FILE",
            "TEMPLATE_DIR",
            "ADACODE_API_KEY",
            "OPENAI_API_KEY",
            "PEXELS_API_KEY",
            "VIDEO_ASSETS_DIR",
            "ENABLE_VIDEO_RENDER",
            "ENABLE_SUPPLEMENTAL_RSS",
            "PYTHONPATH",
            "VIRTUAL_ENV",
            "UV_PROJECT_ENVIRONMENT",
        } or key.startswith("X_"):
            env.pop(key, None)
    return env


def main():
    with tempfile.TemporaryDirectory(prefix="techbro-smoke-") as name:
        folder = Path(name)
        env = clean_environment()
        env.update(DATA_DIR=str(folder / "data"), DATASET_DIR=str(folder / "dataset"))
        # Run from outside the repository: the package must supply its templates.
        subprocess.run(
            [sys.executable, "-m", "techbro_pipeline.cli", "demo"],
            cwd=folder,
            env=env,
            check=True,
            timeout=30,
        )
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        with (folder / "server.log").open("w+") as log:
            server = subprocess.Popen(
                [sys.executable, "-m", "techbro_pipeline.cli", "serve", "--port", str(port)],
                cwd=folder,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                base = f"http://127.0.0.1:{port}"
                deadline = time.monotonic() + 20
                while True:
                    try:
                        with urllib.request.urlopen(base + "/health", timeout=2) as response:
                            assert json.load(response) == {"ok": True}
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if server.poll() is not None or time.monotonic() >= deadline:
                            log.flush()
                            log.seek(0)
                            raise RuntimeError(
                                "Server did not become healthy: " + log.read()[-3000:]
                            ) from None
                        time.sleep(0.2)
                for route in ("/", "/daily", "/status", "/topics-timeline"):
                    with urllib.request.urlopen(base + route, timeout=5) as response:
                        assert response.status == 200
                        assert b"<!" in response.read()
                with urllib.request.urlopen(base + "/api/status", timeout=5) as response:
                    status = json.load(response)
                    assert status["overall"] == "ok", status
                day = status["day"]
                with urllib.request.urlopen(
                    base + f"/api/daily/{day}/tweets", timeout=5
                ) as response:
                    assert json.load(response)["total"] == 1
                print("HTTP smoke passed: health, dashboard, status, topics, and pagination")
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
