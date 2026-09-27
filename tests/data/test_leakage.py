from datetime import datetime, timedelta, timezone

import pytest

from data.validation.exceptions import LeakageError
from data.validation.leakage import (
    TimestampedFeature,
    assert_batch_no_leakage,
    assert_no_leakage,
    filter_leakage_safe,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_assert_no_leakage_allows_past_feature():
    assert_no_leakage(NOW - timedelta(minutes=1), NOW)  # must not raise


def test_assert_no_leakage_allows_exact_same_timestamp():
    assert_no_leakage(NOW, NOW)  # must not raise


def test_assert_no_leakage_rejects_future_feature():
    with pytest.raises(LeakageError):
        assert_no_leakage(NOW + timedelta(minutes=1), NOW, feature_name="current_run_rate")


def test_filter_leakage_safe_drops_future_features_silently():
    features = [
        TimestampedFeature("past", 1, NOW - timedelta(minutes=5)),
        TimestampedFeature("future", 2, NOW + timedelta(minutes=5)),
    ]
    safe = filter_leakage_safe(features, NOW)
    assert [f.name for f in safe] == ["past"]


def test_assert_batch_no_leakage_raises_on_any_future_feature():
    features = [
        TimestampedFeature("past", 1, NOW - timedelta(minutes=5)),
        TimestampedFeature("future", 2, NOW + timedelta(minutes=5)),
    ]
    with pytest.raises(LeakageError):
        assert_batch_no_leakage(features, NOW)
