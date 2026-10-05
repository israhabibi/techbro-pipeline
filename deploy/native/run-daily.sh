#!/usr/bin/env bash
set -euo pipefail
cd /opt/techbro-pipeline
"/opt/techbro-pipeline/.venv/bin/python" scan.py "${SCAN_PAGES:-3}"
exec /bin/bash /opt/techbro-pipeline/pipeline_daily.sh
