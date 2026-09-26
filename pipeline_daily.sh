#!/usr/bin/env bash
# Daily data pipeline: collect sources -> merge to digest -> track topics -> build dataset
# Runs after digest (01:00 UTC), at 02:00 UTC (09:00 WIB)
set -e
cd /home/isra_habibi/techbro
export ADACODE_API_KEY="$(grep ADACODE_API_KEY .env | cut -d= -f2)"

echo "=== [1/4] sources.py (Google News + Tempo) ==="
python3 sources.py 2>&1 | tail -3

echo "=== [2/4] merge_sources.py (-> pantauan di digest) ==="
python3 merge_sources.py 2>&1 | tail -3

echo "=== [3/4] topic_tracker.py (extract topik hangat) ==="
python3 topic_tracker.py 2>&1 | tail -5

echo "=== [4/4] build_dataset.py (CSV Kaggle-ready) ==="
python3 build_dataset.py 2>&1 | tail -3

echo "=== DONE $(date -u) ==="
