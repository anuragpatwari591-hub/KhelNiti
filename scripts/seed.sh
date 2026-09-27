#!/usr/bin/env bash
# Loads mock development data (never run with APP_ENV=production).
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate 2>/dev/null || true
set -a; [ -f .env ] && source .env; set +a
python -m database.seed.mock_data
