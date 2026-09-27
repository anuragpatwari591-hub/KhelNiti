#!/usr/bin/env bash
# Runs the full backend/ml/data pytest suite against $DATABASE_URL_TEST.
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate 2>/dev/null || true
set -a; [ -f .env ] && source .env; set +a
pytest tests/backend tests/ml tests/data -v
