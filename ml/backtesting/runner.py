"""Persists a completed backtest as a `backtest_runs` row.

A `ModelVersion`/`ModelMetric` pair (see `database/models/predictions.py`)
records what a specific trained model scores on one metric; a
`BacktestRun` is the higher-level record of the whole chronological
train/validation/test experiment that produced it — kept even if the
resulting model is never promoted to `is_active=True`, so no backtest
result (good or bad) is ever silently discarded.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.models.enums import Sport
from database.models.predictions import BacktestRun


def persist_backtest_run(
    session: Session,
    sport: Sport,
    model_name: str,
    model_version: str,
    train_range: tuple,
    validation_range: tuple,
    test_range: tuple,
    metrics: dict,
    notes: str | None = None,
) -> BacktestRun:
    run = BacktestRun(
        sport=sport,
        model_name=model_name,
        model_version=model_version,
        train_start=train_range[0],
        train_end=train_range[1],
        validation_start=validation_range[0],
        validation_end=validation_range[1],
        test_start=test_range[0],
        test_end=test_range[1],
        metrics=metrics,
        run_at=datetime.now(timezone.utc),
        notes=notes,
    )
    session.add(run)
    session.flush()
    return run
