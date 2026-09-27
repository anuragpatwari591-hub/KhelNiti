"""Calibration and skill metrics for binary probability forecasts.

Used by both `ml/training/*` (to report validation/test metrics) and
`ml/backtesting` (to persist metrics per `backtest_runs` row). Every metric
here is computed directly from (predicted probability, actual outcome)
pairs — nothing is a hard-coded or assumed accuracy figure.
"""
import math
from dataclasses import dataclass


def brier_score(predicted_probs: list[float], actual_outcomes: list[int]) -> float:
    """Mean squared error between predicted probability and the 0/1
    outcome. Lower is better; 0 is perfect, 0.25 is what a coin-flip
    forecaster gets on a balanced binary outcome.
    """
    _check_same_length(predicted_probs, actual_outcomes)
    n = len(predicted_probs)
    if n == 0:
        raise ValueError("no predictions to score")
    return sum((p - y) ** 2 for p, y in zip(predicted_probs, actual_outcomes)) / n


def log_loss(predicted_probs: list[float], actual_outcomes: list[int], eps: float = 1e-12) -> float:
    _check_same_length(predicted_probs, actual_outcomes)
    n = len(predicted_probs)
    if n == 0:
        raise ValueError("no predictions to score")
    total = 0.0
    for p, y in zip(predicted_probs, actual_outcomes):
        p_clipped = min(max(p, eps), 1 - eps)
        total += -(y * math.log(p_clipped) + (1 - y) * math.log(1 - p_clipped))
    return total / n


def accuracy(predicted_probs: list[float], actual_outcomes: list[int], threshold: float = 0.5) -> float:
    _check_same_length(predicted_probs, actual_outcomes)
    n = len(predicted_probs)
    if n == 0:
        raise ValueError("no predictions to score")
    correct = sum(1 for p, y in zip(predicted_probs, actual_outcomes) if (p >= threshold) == bool(y))
    return correct / n


@dataclass(frozen=True)
class ReliabilityBin:
    bin_lower: float
    bin_upper: float
    predicted_mean: float | None
    observed_rate: float | None
    count: int


def reliability_bins(predicted_probs: list[float], actual_outcomes: list[int], n_bins: int = 10) -> list[ReliabilityBin]:
    """Buckets predictions into `n_bins` equal-width probability ranges and
    compares the mean predicted probability to the observed outcome rate in
    each — the data behind a reliability diagram.
    """
    _check_same_length(predicted_probs, actual_outcomes)
    bins: list[list[tuple[float, int]]] = [[] for _ in range(n_bins)]
    for p, y in zip(predicted_probs, actual_outcomes):
        idx = min(int(p * n_bins), n_bins - 1)
        bins[idx].append((p, y))

    results = []
    for i, bucket in enumerate(bins):
        lower, upper = i / n_bins, (i + 1) / n_bins
        if not bucket:
            results.append(ReliabilityBin(lower, upper, None, None, 0))
            continue
        mean_pred = sum(p for p, _ in bucket) / len(bucket)
        observed = sum(y for _, y in bucket) / len(bucket)
        results.append(ReliabilityBin(lower, upper, mean_pred, observed, len(bucket)))
    return results


def expected_calibration_error(predicted_probs: list[float], actual_outcomes: list[int], n_bins: int = 10) -> float:
    """Weighted average absolute gap between predicted and observed rate
    across reliability bins — a single-number calibration summary.
    """
    bins = reliability_bins(predicted_probs, actual_outcomes, n_bins)
    total = len(predicted_probs)
    if total == 0:
        raise ValueError("no predictions to score")
    ece = 0.0
    for b in bins:
        if b.count == 0:
            continue
        ece += (b.count / total) * abs(b.predicted_mean - b.observed_rate)
    return ece


def _check_same_length(a: list, b: list) -> None:
    if len(a) != len(b):
        raise ValueError(f"predicted_probs and actual_outcomes must be the same length, got {len(a)} vs {len(b)}")
