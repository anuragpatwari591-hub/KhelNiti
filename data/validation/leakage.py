"""Structural guard against future-data leakage into predictions.

Every feature consumed by a model must be stamped with the time it was
true as of. This module is the single choke point that enforces
`feature_timestamp <= prediction_timestamp` — the feature-store read path
(ml/feature_engineering) is required to call `assert_no_leakage` (or
`filter_leakage_safe`) before handing features to a model.
"""
from dataclasses import dataclass
from datetime import datetime

from data.validation.exceptions import LeakageError


@dataclass(frozen=True)
class TimestampedFeature:
    name: str
    value: float | int | str | dict
    feature_timestamp: datetime


def assert_no_leakage(feature_timestamp: datetime, prediction_timestamp: datetime, feature_name: str = "") -> None:
    if feature_timestamp > prediction_timestamp:
        raise LeakageError(
            f"Feature '{feature_name}' timestamped {feature_timestamp.isoformat()} is after "
            f"prediction timestamp {prediction_timestamp.isoformat()} — would leak future information."
        )


def filter_leakage_safe(
    features: list[TimestampedFeature], prediction_timestamp: datetime
) -> list[TimestampedFeature]:
    """Returns only the features that are safe to use as of
    `prediction_timestamp`, silently dropping (not raising on) any that are
    not yet available — this is the normal case for a live prediction where
    some aggregate hasn't been recomputed yet, as opposed to a bug that
    hands the model literal future data.
    """
    return [f for f in features if f.feature_timestamp <= prediction_timestamp]


def assert_batch_no_leakage(features: list[TimestampedFeature], prediction_timestamp: datetime) -> None:
    """Strict variant for training/backtesting pipelines: any leaking
    feature in the batch is a bug in the pipeline, not an expected runtime
    condition, so it raises rather than silently filtering.
    """
    for f in features:
        assert_no_leakage(f.feature_timestamp, prediction_timestamp, f.name)
