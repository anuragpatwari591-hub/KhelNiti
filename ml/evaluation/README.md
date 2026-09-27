# Evaluation (folded into ml/calibration for now)

The spec lists `evaluation/` and `calibration/` as separate concerns.
Today all metric computation (Brier score, log loss, accuracy, expected
calibration error, reliability bins — both binary and multiclass) lives in
`ml/calibration/metrics.py` and is used directly by both
`ml/training/*` and `ml/backtesting/*`. A split into a distinct
`evaluation` layer (e.g. richer error analysis, slicing by competition/
season beyond what `model_metrics.competition_id`/`season_id` already
support) is reserved here for when that's needed — see
[docs/BACKTESTING.md](../../docs/BACKTESTING.md#error-analysis).
