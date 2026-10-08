"""Ordered stage execution with a shared interpreter and an overlap lock."""

import fcntl
import os
import subprocess
import sys
from datetime import UTC, datetime

from techbro_pipeline.config import Settings, day_stamp

STAGES = [
    ("scan", "scan.py (X home timeline)"),
    ("sources", "sources.py (RSS)"),
    ("topics", "topic_tracker.py (topics)"),
    ("threads", "build_threads_draft.py (Threads draft)"),
    ("dataset", "build_dataset.py (CSV)"),
]


def run():
    settings = Settings.from_env()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    with (settings.data_dir / ".pipeline.lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("[error] another pipeline run is active", file=sys.stderr)
            return 1
        with (settings.data_dir / "pipeline.log").open("a", encoding="utf-8") as log:

            def emit(text):
                print(text, flush=True)
                log.write(text + "\n")
                log.flush()

            run_day = day_stamp()
            emit(f"=== RUN {run_day} ===")
            for index, (command, label) in enumerate(STAGES, start=1):
                emit(f"=== [{index}/{len(STAGES)}] {label} ===")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "techbro_pipeline.cli", command],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=os.environ.copy(),
                        timeout=900,
                    )
                except (subprocess.TimeoutExpired, OSError) as exc:
                    emit(f"[error] stage could not complete: {type(exc).__name__}")
                    emit(f"=== FAILED {index} ===")
                    return 1
                if result.stdout:
                    emit(result.stdout.rstrip())
                if result.returncode:
                    emit(f"[error] {command} exited with code {result.returncode}")
                    emit(f"=== FAILED {index} ===")
                    return result.returncode if result.returncode > 0 else 1
            if os.getenv("REPLIZ_AUTO_SCHEDULE", "false").lower() in {"1", "true", "yes"}:
                from techbro_pipeline.repliz import ReplizError, daily_schedule_time

                emit("=== Repliz scheduling ===")
                try:
                    at = daily_schedule_time(run_day).isoformat()
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "techbro_pipeline.cli",
                            "repliz",
                            "schedule",
                            "--date",
                            run_day,
                            "--at",
                            at,
                            "--submit",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        env=os.environ.copy(),
                        timeout=120,
                    )
                except (ReplizError, subprocess.TimeoutExpired, OSError) as exc:
                    message = str(exc) if isinstance(exc, ReplizError) else type(exc).__name__
                    emit(f"[error] Repliz scheduling failed: {message}")
                    emit("=== FAILED Repliz ===")
                    return 1
                if result.stdout:
                    emit(result.stdout.rstrip())
                if result.returncode:
                    emit("[error] Repliz scheduling failed; inspect the submission receipt")
                    emit("=== FAILED Repliz ===")
                    return 1
            emit(f"=== DONE {datetime.now(UTC).isoformat()} ===")
    return 0
