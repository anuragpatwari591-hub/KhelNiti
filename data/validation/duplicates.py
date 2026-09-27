"""Duplicate-detection helpers.

The database enforces the canonical uniqueness constraints (see
`database/models/*` — e.g. `uq_match_source_ref`, `uq_delivery_innings_sequence`).
These functions let ingestion code check *before* attempting an insert, so
a duplicate in an incoming batch produces a clear, catchable error instead
of a raw `IntegrityError`, and so a batch can be de-duplicated against
itself before it ever reaches the database.
"""
from collections.abc import Iterable, Sequence

from data.validation.exceptions import DuplicateDataError


def find_duplicate_keys(keys: Sequence[tuple]) -> list[tuple]:
    """Returns the list of keys that appear more than once in `keys`."""
    seen: set[tuple] = set()
    duplicates: list[tuple] = []
    for key in keys:
        if key in seen:
            duplicates.append(key)
        else:
            seen.add(key)
    return duplicates


def assert_no_duplicate_matches(external_refs: Iterable[tuple[str, str]]) -> None:
    """`external_refs` is an iterable of (data_source, external_ref)."""
    duplicates = find_duplicate_keys(list(external_refs))
    if duplicates:
        raise DuplicateDataError(f"Duplicate match external_ref(s) in batch: {duplicates}")


def assert_no_duplicate_deliveries(innings_sequence_pairs: Iterable[tuple[int, int]]) -> None:
    """`innings_sequence_pairs` is an iterable of (innings_id_or_placeholder, sequence)."""
    duplicates = find_duplicate_keys(list(innings_sequence_pairs))
    if duplicates:
        raise DuplicateDataError(f"Duplicate delivery (innings, sequence) in batch: {duplicates}")
