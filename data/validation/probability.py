"""Probability bounds and consistency checks.

Used by every model-serving path before a prediction is persisted or
returned: "every probability must be between 0 and 1 and mutually
consistent" is enforced here rather than trusted from model output.
"""
import math

from data.validation.exceptions import ProbabilityError

_SUM_TOLERANCE = 1e-6


def assert_valid_probability(p: float, label: str = "probability") -> None:
    if math.isnan(p) or math.isinf(p):
        raise ProbabilityError(f"{label}={p} is not a finite number")
    if not (0.0 <= p <= 1.0):
        raise ProbabilityError(f"{label}={p} is outside the valid [0, 1] range")


def assert_valid_distribution(probabilities: dict[str, float], label: str = "distribution") -> None:
    """Every outcome's probability must be in [0, 1] and the full set of
    mutually exclusive outcomes must sum to 1 within floating-point
    tolerance (e.g. home/draw/away, or win/loss for a two-outcome market).
    """
    if not probabilities:
        raise ProbabilityError(f"{label} is empty")
    for outcome, p in probabilities.items():
        assert_valid_probability(p, f"{label}[{outcome}]")
    total = sum(probabilities.values())
    if abs(total - 1.0) > _SUM_TOLERANCE:
        raise ProbabilityError(f"{label} sums to {total}, expected 1.0 (+/- {_SUM_TOLERANCE})")
