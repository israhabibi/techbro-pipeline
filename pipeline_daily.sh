#!/usr/bin/env bash
# Compatibility launcher. The Python runner owns ordering, logs, and locking.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export DATA_DIR="${DATA_DIR:-$SCRIPT_DIR/data}"
export DATASET_DIR="${DATASET_DIR:-$SCRIPT_DIR/dataset}"
export ENABLE_SUPPLEMENTAL_RSS="${ENABLE_SUPPLEMENTAL_RSS:-1}"
if [[ -f "$SCRIPT_DIR/.env" ]]; then
  exec "$SCRIPT_DIR/.venv/bin/techbro" --env-file "$SCRIPT_DIR/.env" pipeline
fi
exec "$SCRIPT_DIR/.venv/bin/techbro" pipeline
