"""Chronological (never random) train/validation/test splitting.

"Never randomly mix future matches into training" is enforced structurally
here: items are sorted by date first, then cut at fixed points — there is
no shuffle step anywhere in this module.
"""
from dataclasses import dataclass
from datetime import date
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class TemporalSplit(Generic[T]):
    train: list[T]
    validation: list[T]
    test: list[T]
    train_range: tuple[date, date]
    validation_range: tuple[date, date]
    test_range: tuple[date, date]


def temporal_split(
    items: list[T],
    date_key,
    train_frac: float = 0.70,
    validation_frac: float = 0.15,
) -> TemporalSplit[T]:
    """Splits `items` chronologically by `date_key(item)`.

    Fractions are of item *count*, not calendar time — appropriate when
    matches aren't evenly distributed across the calendar. The date ranges
    reported alongside each split are the actual min/max dates in that
    split, for storing on a `backtest_runs` row.
    """
    if not items:
        raise ValueError("cannot split an empty list")
    if not (0 < train_frac < 1) or not (0 <= validation_frac < 1) or train_frac + validation_frac >= 1:
        raise ValueError("train_frac and validation_frac must leave a non-empty test fraction")

    ordered = sorted(items, key=date_key)
    n = len(ordered)
    train_end = max(int(n * train_frac), 1)
    validation_end = max(train_end + int(n * validation_frac), train_end + 1)
    validation_end = min(validation_end, n - 1) if n > train_end + 1 else train_end + 1

    train = ordered[:train_end]
    validation = ordered[train_end:validation_end]
    test = ordered[validation_end:]

    if not validation or not test:
        raise ValueError(
            f"split produced an empty validation ({len(validation)}) or test ({len(test)}) set "
            f"from {n} items — provide more items or adjust fractions"
        )

    return TemporalSplit(
        train=train,
        validation=validation,
        test=test,
        train_range=(date_key(train[0]), date_key(train[-1])),
        validation_range=(date_key(validation[0]), date_key(validation[-1])),
        test_range=(date_key(test[0]), date_key(test[-1])),
    )
