#!/usr/bin/env bash
set -euo pipefail
cd /opt/techbro-pipeline
exec /opt/techbro-pipeline/.venv/bin/techbro pipeline
