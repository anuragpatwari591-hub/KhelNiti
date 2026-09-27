#!/usr/bin/env bash
# Trains and backtests both models, persisting model_versions/model_metrics/
# backtest_runs rows (see docs/ML.md and docs/BACKTESTING.md).
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate 2>/dev/null || true
set -a; [ -f .env ] && source .env; set +a
python -m ml.training.train_cricket_win_probability
python -m ml.training.train_football_expected_goals
