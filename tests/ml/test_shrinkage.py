import pytest

from ml.feature_engineering.shrinkage import confidence_label, shrink_rate


def test_shrink_rate_zero_sample_size_equals_prior():
    assert shrink_rate(observed_rate=0.9, sample_size=0, prior_rate=0.3) == pytest.approx(0.3)


def test_shrink_rate_converges_toward_observed_as_sample_grows():
    small = shrink_rate(observed_rate=0.9, sample_size=5, prior_rate=0.3, prior_strength=20)
    large = shrink_rate(observed_rate=0.9, sample_size=10_000, prior_rate=0.3, prior_strength=20)
    assert small < large
    assert large == pytest.approx(0.9, abs=0.01)


def test_shrink_rate_rejects_negative_sample_size():
    with pytest.raises(ValueError):
        shrink_rate(0.5, -1, 0.3)


@pytest.mark.parametrize(
    "sample_size,expected",
    [(0, "low"), (9, "low"), (10, "medium"), (49, "medium"), (50, "high"), (1000, "high")],
)
def test_confidence_label_thresholds(sample_size, expected):
    assert confidence_label(sample_size) == expected
