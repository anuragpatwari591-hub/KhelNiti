#!/usr/bin/env bash
# Applies all pending Alembic migrations to $DATABASE_URL (from .env).
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate 2>/dev/null || true
set -a; [ -f .env ] && source .env; set +a
alembic upgrade head
