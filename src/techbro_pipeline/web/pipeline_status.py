#!/usr/bin/env python3
"""Health check for the daily pipeline.

Reads the cron log plus the artifacts each stage is expected to write, so a
missing or skipped stage shows up on the web instead of only in a log file the
user has to open by hand.
"""

import glob
import json
import os
import re

OK, WARN, FAIL, SKIP, PENDING = "ok", "warn", "fail", "skip", "pending"

STEP_RE = re.compile(r"^=== \[(\d)/(\d)\]\s+(.+?)\s+===\s*$")
DONE_RE = re.compile(r"^=== DONE (.+?) ===\s*$")
RUN_RE = re.compile(r"^=== RUN (\d{8}) ===\s*$", re.MULTILINE)
LOG_MAX_BYTES = 512 * 1024

# (label, artifact template relative to DATA_DIR) — None means "no artifact to check".
STAGES = [
    ("scan.py (X home timeline)", "feed/feed_{day}.json"),
    ("sources.py (Google News + Tempo RSS)", "sources/sources_{day}.json"),
    ("topic_tracker.py (ekstrak topik hangat)", "topics/topics_{day}.json"),
    ("build_threads_draft.py (draft Threads)", "threads/threads_draft_{day}.json"),
    ("build_dataset.py (CSV Kaggle-ready)", "@dataset"),
]

PIPELINE_MARKER = "pipeline_daily.sh"

CRONTAB_SNAPSHOT = "crontab.txt"


def _read_log(data_dir):
    """Return the tail of pipeline.log, or None when the file is absent."""
    path = os.path.join(data_dir, "pipeline.log")
    if not os.path.isfile(path):
        return None
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        if size > LOG_MAX_BYTES:
            fh.seek(size - LOG_MAX_BYTES)
            fh.readline()  # drop the partial first line
        return fh.read().decode("utf-8", "replace")


def _last_run(log_text):
    """Slice only the most recent run out of an append-only log.

    Anchor on the last `[1/n]` marker, not the first: the log outlives changes in
    step count, so an older 6-step run would otherwise be paired with today's
    5-stage labels and shift every badge by one.
    """
    if not log_text:
        return None
    lines = log_text.splitlines()
    starts = [
        i
        for i, line in enumerate(lines)
        if (match := STEP_RE.match(line)) and match.group(1) == "1"
    ]
    if not starts:
        return None
    return lines[starts[-1] :]


def _classify(step_lines, finished):
    if any("[skip]" in line or "SKIP" in line for line in step_lines):
        return SKIP
    if any(
        "[warn]" in line or "[error]" in line or "Traceback" in line or "Error" in line
        for line in step_lines
    ):
        return WARN
    if not finished:
        return PENDING
    # `tail -N` on a healthy stage still prints something; an empty body means
    # the script died before its first print.
    if not [line for line in step_lines if line.strip()]:
        return FAIL
    return OK


def _tail(step_lines, limit=4):
    return [line for line in step_lines if line.strip()][-limit:]


def _artifact(data_dir, template, day):
    if not template:
        return None
    if template == "@dataset":
        dataset_dir = os.environ.get(
            "DATASET_DIR", os.path.join(os.path.dirname(data_dir), "dataset")
        )
        return {
            "ok": os.path.isfile(os.path.join(dataset_dir, "techbro_tweets.csv")),
            "detail": "dataset/techbro_tweets.csv",
        }
    path = os.path.join(data_dir, template.format(day=day))
    valid = False
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as handle:
                valid = isinstance(json.load(handle), dict)
        except (OSError, ValueError):
            pass
    return {
        "ok": valid,
        "detail": os.path.relpath(path, data_dir),
        "bytes": os.path.getsize(path) if os.path.isfile(path) else 0,
    }


def _parse_steps(run_lines):
    """Group the last run's log body into per-stage records."""
    parsed = []
    for line in run_lines:
        match = STEP_RE.match(line)
        if match:
            parsed.append(
                {
                    "index": int(match.group(1)),
                    "total": int(match.group(2)),
                    "label": match.group(3),
                    "lines": [],
                }
            )
            continue
        if DONE_RE.match(line):
            if parsed:
                parsed[-1]["lines"].append(line)
            continue
        if parsed:
            parsed[-1]["lines"].append(line)
    return parsed


def _read_crontab(data_dir):
    """Best-effort crontab view.

    The container cannot see the host crontab, so the pipeline writes a snapshot
    when it runs. Absent snapshot means "unknown", never "nothing scheduled".
    """
    path = os.path.join(data_dir, CRONTAB_SNAPSHOT)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except OSError:
        return None


def _external_cron(crontab_lines):
    """Derive other scheduled jobs from the crontab snapshot.

    Hardcoding sibling repos would rot the moment a job is renamed or moved, so
    anything in the crontab that is not this pipeline is reported as external.
    """
    entries = []
    for line in crontab_lines or []:
        parts = line.split(None, 5)
        schedule = " ".join(parts[:5]) if len(parts) > 5 else line
        command = parts[5] if len(parts) > 5 else line
        if PIPELINE_MARKER in command:
            continue
        target = command.split()[0] if command.split() else command
        entries.append(
            {
                "label": target.rsplit("/", 1)[-1] or target,
                "state": OK,
                "note": f"{schedule} · {command}",
                "artifact": None,
            }
        )
    return entries


def build_status(data_dir, day):
    """Assemble the full status payload for the /status page."""
    log_text = _read_log(data_dir)
    run_lines = _last_run(log_text)
    parsed = _parse_steps(run_lines) if run_lines else []
    done_line = next((line for line in reversed(run_lines or []) if DONE_RE.match(line)), None)
    finished = done_line is not None
    failed = any(line.startswith("=== FAILED ") for line in run_lines or [])
    run_dates = RUN_RE.findall(log_text or "")
    run_date_matches = not run_dates or run_dates[-1] == day

    stages = []
    for position, (label, artifact) in enumerate(STAGES):
        record = parsed[position] if position < len(parsed) else None
        stage_finished = finished or position < len(parsed) - 1
        state = (
            _classify(record["lines"], stage_finished)
            if record
            else (FAIL if finished else PENDING)
        )
        artifact = _artifact(data_dir, artifact, day)
        if record and failed and position == len(parsed) - 1:
            state = FAIL
        elif state == OK and artifact and not artifact["ok"]:
            state = FAIL
        if not run_date_matches:
            state = WARN
        stages.append(
            {
                "index": position + 1,
                "label": label,
                "state": state,
                "detail": _tail(record["lines"]) if record else [],
                "artifact": artifact,
                "in_log": record is not None,
            }
        )

    crontab = _read_crontab(data_dir)
    externals = _external_cron(crontab)

    states = [s["state"] for s in stages]
    if not parsed:
        overall = PENDING
    elif FAIL in states:
        overall = FAIL
    elif WARN in states or SKIP in states:
        overall = WARN
    elif PENDING in states or not finished:
        overall = PENDING
    else:
        overall = OK

    dates = []
    for path in glob.glob(os.path.join(data_dir, "feed", "feed_*.json")):
        stamp = os.path.basename(path)[5:-5]
        if len(stamp) == 8 and stamp.isdigit():
            dates.append(stamp)

    return {
        "day": day,
        "overall": overall,
        "stages": stages,
        "externals": externals,
        "done_line": done_line,
        "has_log": log_text is not None,
        "dates": sorted(set(dates), reverse=True),
        "crontab": crontab,
    }
