import math

import pytest

from data.validation.exceptions import ProbabilityError
from data.validation.probability import assert_valid_distribution, assert_valid_probability


def test_assert_valid_probability_accepts_boundaries():
    assert_valid_probability(0.0)
    assert_valid_probability(1.0)
    assert_valid_probability(0.5)


@pytest.mark.parametrize("bad", [-0.01, 1.01, math.nan, math.inf, -math.inf])
def test_assert_valid_probability_rejects_out_of_range_or_non_finite(bad):
    with pytest.raises(ProbabilityError):
        assert_valid_probability(bad)


def test_assert_valid_distribution_accepts_sum_to_one():
    assert_valid_distribution({"home": 0.6, "draw": 0.25, "away": 0.15})


def test_assert_valid_distribution_accepts_floating_point_tolerance():
    assert_valid_distribution({"a": 0.1, "b": 0.2, "c": 0.7000000001})


def test_assert_valid_distribution_rejects_sum_not_one():
    with pytest.raises(ProbabilityError):
        assert_valid_distribution({"home": 0.5, "away": 0.3})


def test_assert_valid_distribution_rejects_out_of_range_member():
    with pytest.raises(ProbabilityError):
        assert_valid_distribution({"home": 1.5, "away": -0.5})


def test_assert_valid_distribution_rejects_empty():
    with pytest.raises(ProbabilityError):
        assert_valid_distribution({})
