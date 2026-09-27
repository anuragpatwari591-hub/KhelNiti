#!/usr/bin/env bash
# One-time local setup: Python venv + backend deps + frontend deps + .env.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — edit it before using real providers."
fi

echo "Setting up backend virtualenv..."
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "Installing frontend dependencies..."
(cd apps/web && npm install)

echo "Setup complete. Next: scripts/migrate.sh, then scripts/seed.sh (optional), then run the app."
