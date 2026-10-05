#!/usr/bin/env bash
# Daily data pipeline: scan X -> sources RSS -> topics -> Threads draft -> dataset
# Dijadwalkan via crontab, misal: 0 8 * * * cd /home/isra/techbro/techbro-pipeline && ./pipeline_daily.sh >> data/pipeline.log 2>&1
set -eo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
mkdir -p data

# Aktifkan koleksi RSS tambahan (Google News + Tempo) untuk sources.py & merge_sources.py
export ENABLE_SUPPLEMENTAL_RSS=1

if [[ -z "${ADACODE_API_KEY:-}" && -f .env ]]; then
  ADACODE_API_KEY="$(grep -m1 '^ADACODE_API_KEY=' .env | cut -d= -f2- | tr -d '\"')"
  export ADACODE_API_KEY
fi

echo "=== [1/6] scan.py (X home timeline) ==="
python3 scan.py 2>&1 | tail -5

echo "=== [2/6] sources.py (Google News + Tempo RSS) ==="
python3 sources.py 2>&1 | tail -5

echo "=== [3/6] merge_sources.py (gabung RSS ke digest) ==="
python3 merge_sources.py 2>&1 | tail -3 || echo "[skip] merge_sources: digest belum ada (dibuat via LLM cron)"

echo "=== [4/6] topic_tracker.py (extract topik hangat) ==="
python3 topic_tracker.py 2>&1 | tail -5

echo "=== [5/6] build_threads_draft.py (draft Threads, tidak dipublikasikan) ==="
python3 build_threads_draft.py

echo "=== [6/6] build_dataset.py (CSV Kaggle-ready) ==="
python3 build_dataset.py 2>&1 | tail -3

echo "=== DONE $(date -u) ==="
