# Backtesting

## Methodology

`ml/backtesting/splits.py:temporal_split` sorts every match/checkpoint by
date and cuts three contiguous, non-overlapping ranges — train (oldest),
validation, test (most recent). There is no shuffling anywhere in the
pipeline: this is the one property that "no future leakage in training
splits" depends on structurally rather than as a convention someone has to
remember.

Split sizes are **not** hard-coded to specific calendar years — they're a
fraction of however many dated items are available
(`train_frac=0.70, validation_frac=0.15`, remainder to test), so the same
code works whether the underlying dataset covers two seasons or ten. The
spec's example years (2014-2021 / 2022 / 2023-2025) describe the
*technique* (chronological, non-overlapping), not a value baked into this
codebase.

## What's evaluated

For each backtest:
1. Fit the model on the training split only.
2. Where the model uses an auxiliary empirical prior (cricket's Monte
   Carlo phase distributions), estimate it **only from the training
   split** — evaluating a phase-frequency table built partly from test-set
   matches would itself be a leakage bug.
3. Evaluate on validation (used to sanity-check before looking at test)
   and test, using `ml/calibration/metrics.py`: Brier score, log loss,
   accuracy, and expected calibration error (binary), or the multiclass
   equivalents (football's 3-way outcome).
4. Persist a `backtest_runs` row (`database/models/predictions.py`) with
   the exact train/validation/test date ranges and the full metrics JSON
   — every run, not just the ones with good numbers.

## Running a backtest

```bash
python -m ml.training.train_cricket_win_probability
python -m ml.training.train_football_expected_goals
```

These scripts *are* the backtest runner for each model today — training
and backtesting share the same chronological-split code path
(`ml/backtesting/splits.py`), because a backtest is precisely "train on
the past, evaluate on the untouched future" repeated as a distinct,
recorded experiment. `ml/backtesting/runner.py:persist_backtest_run` is the
shared persistence call both scripts use, factored out so a future
model-specific script (e.g. a player run-projection backtest) reuses the
same `backtest_runs` schema without re-implementing it.

## Current results (mock data)

| Model | Test accuracy | Test Brier | Notes |
|---|---|---|---|
| `cricket_win_probability` (ensemble) | 71.7% | 0.176 | 260 synthetic T20 matches |
| `football_match_outcome` (Dixon-Coles) | 61.7% | 0.543 | 400 synthetic fixtures |

These numbers are real outputs of the commands above, re-run before every
release of this document — not a fixed claim. They describe skill on
**synthetic mock data** designed to have the same statistical structure
the models assume (phase-dependent ball outcomes; team-level Poisson
attack/defense). They are not, and must not be read as, evidence of skill
on real cricket or football matches — see `docs/MODEL_LIMITATIONS.md`.

## Error analysis

`ml/calibration/metrics.py:reliability_bins` returns per-bucket
(predicted-probability range) counts and observed outcome rates — the
data behind a reliability diagram — so miscalibration in a specific
probability range (e.g. the model is overconfident specifically above
90%) is visible rather than hidden inside a single aggregate number.
Slicing backtest results by competition/season is supported by
`model_metrics.competition_id`/`season_id` (nullable FKs) but not yet
wired into either training script — see `docs/ARCHITECTURE.md#roadmap`.
