#!/usr/bin/env python3
"""Compatibility launcher; implementation is in src/techbro_pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from techbro_pipeline.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["threads", *sys.argv[1:]]))
