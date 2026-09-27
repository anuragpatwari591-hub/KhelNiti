# Contributing

## Workflow

1. Inspect what's already there before changing it — read
   `docs/ARCHITECTURE.md` for module boundaries and the roadmap so you
   don't duplicate something already planned or accidentally reverse a
   deliberate design choice (e.g. market data separation, mock/production
   isolation).
2. Write the code.
3. Run the relevant tests (`scripts/test.sh`, or a targeted `pytest
   tests/ml/test_x.py -v`).
4. Fix anything that breaks.
5. For frontend changes, run `npm run build` in `apps/web` (type-checks
   and builds) and actually look at the page in a browser — a passing
   build is not the same as a working feature.
6. Update the relevant doc(s) in `docs/` in the same change — a schema
   change without a `docs/DATABASE.md` update, or a new model without a
   `docs/ML.md`/`docs/MODEL_LIMITATIONS.md` update, is an incomplete PR.
7. Commit with a scoped, descriptive message (see below).

## Commit style

`type(scope): summary`, e.g.:

```
feat(ml): add player run-projection model
fix(api): correct leakage check in prediction feature snapshot
docs(architecture): update roadmap after news pipeline lands
test(backend): cover probability-sum validation on predictions endpoint
```

## Non-negotiables

These aren't style preferences — they're the properties the whole project
depends on being true everywhere, always:

- **No future-data leakage.** Any new feature must carry a
  `feature_timestamp` and go through `data/validation/leakage.py`. Any new
  training/backtesting split must be chronological
  (`ml/backtesting/splits.py`), never randomly shuffled.
- **No fabricated data.** A new mock provider or mock data path must set
  `data_quality=DataQuality.MOCK` (or the equivalent) and must never be
  reachable when `DATA_PROVIDER_MODE=live`.
- **No fake accuracy.** A metric shown anywhere must come from
  `ml/calibration/metrics.py` run against real (if currently mock)
  predictions — never a hard-coded or estimated number.
- **Every probability is validated.** Call
  `data/validation/probability.py:assert_valid_distribution` before
  persisting or returning any probability distribution.
- **Every prediction is audited.** A new prediction type should follow the
  existing `predictions` / `prediction_features` / `prediction_results`
  pattern (`database/models/predictions.py`) — don't return a probability
  from an endpoint without persisting how it was produced.
- **Market data stays separate.** Never fold `odds_snapshots` /
  `market_movements` into a model's default feature set — see
  `docs/ML.md#market-data-separation`.

## Adding a new sport model

Follow the existing shape (`ml/cricket/` or `ml/football/`): feature
extraction with timestamps, a documented statistical/ML approach (not
"whichever library sounds most advanced"), a training script under
`ml/training/` using `ml/backtesting/splits.py`, calibration metrics from
`ml/calibration/metrics.py`, and a `backtest_runs` row via
`ml/backtesting/runner.py:persist_backtest_run`.

## Adding a new API endpoint

Add it under the relevant `backend/app/<module>/routes.py`, with a
Pydantic schema in that module's `schemas.py`. Read endpoints are public
by default; anything that writes data or triggers computation should
require `Depends(get_current_user)` (see
`backend/app/authentication/deps.py`).

## Local database for tests

Tests need a real PostgreSQL database at `DATABASE_URL_TEST` (default
`khelniti_test` — see `.env.example`), separate from your dev database.
`tests/conftest.py` creates/drops all tables once per test session and
runs each test inside a rolled-back transaction, so tests never leak
state — but they do need write access to a real schema.
