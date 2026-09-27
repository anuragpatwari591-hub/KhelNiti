import pytest

from data.validation.duplicates import (
    assert_no_duplicate_deliveries,
    assert_no_duplicate_matches,
    find_duplicate_keys,
)
from data.validation.exceptions import DuplicateDataError


def test_find_duplicate_keys_identifies_repeats():
    keys = [(1, 1), (1, 2), (1, 1), (2, 1)]
    assert find_duplicate_keys(keys) == [(1, 1)]


def test_find_duplicate_keys_empty_when_all_unique():
    assert find_duplicate_keys([(1, 1), (1, 2)]) == []


def test_assert_no_duplicate_matches_raises_on_repeat_external_ref():
    with pytest.raises(DuplicateDataError):
        assert_no_duplicate_matches([("provider-a", "match-1"), ("provider-a", "match-1")])


def test_assert_no_duplicate_matches_allows_same_ref_different_source():
    assert_no_duplicate_matches([("provider-a", "match-1"), ("provider-b", "match-1")])  # must not raise


def test_assert_no_duplicate_deliveries_raises_on_repeat_sequence():
    with pytest.raises(DuplicateDataError):
        assert_no_duplicate_deliveries([(10, 1), (10, 2), (10, 1)])
