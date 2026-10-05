#!/usr/bin/env bash
# Daily data pipeline: track topics -> draft Threads post -> build dataset
# Runs after digest (01:00 UTC), at 02:00 UTC (09:00 WIB)
set -eo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p data

if [[ -z "${ADACODE_API_KEY:-}" && -f .env ]]; then
  ADACODE_API_KEY="$(grep -m1 '^ADACODE_API_KEY=' .env | cut -d= -f2- | tr -d '\"')"
  export ADACODE_API_KEY
fi

echo "=== [1/3] topic_tracker.py (extract topik hangat) ==="
python3 topic_tracker.py 2>&1 | tail -5

echo "=== [2/3] build_threads_draft.py (draft Threads, tidak dipublikasikan) ==="
python3 build_threads_draft.py

echo "=== [3/3] build_dataset.py (CSV Kaggle-ready) ==="
python3 build_dataset.py 2>&1 | tail -3

echo "=== DONE $(date -u) ==="
