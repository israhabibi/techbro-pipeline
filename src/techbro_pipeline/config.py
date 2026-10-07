"""Shared environment configuration and atomic artifact persistence."""

import csv
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Jakarta")


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    dataset_dir: Path
    credentials_file: Path

    @classmethod
    def from_env(cls):
        data = Path(os.environ.get("DATA_DIR", "data")).resolve()
        return cls(
            data_dir=data,
            dataset_dir=Path(os.environ.get("DATASET_DIR", str(data.parent / "dataset"))).resolve(),
            credentials_file=Path(os.environ.get("CREDS_FILE", "creds.json")).resolve(),
        )


def day_stamp():
    return datetime.now(LOCAL_TZ).strftime("%Y%m%d")


def write_json(path, data):
    """Readers see either the previous artifact or the complete replacement."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o640)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_csv(path, fieldnames, rows):
    """Publish a complete CSV, preserving the previous file on serialization failure."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            os.fchmod(handle.fileno(), 0o640)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
