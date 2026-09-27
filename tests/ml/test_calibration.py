import pytest

from ml.calibration.metrics import (
    accuracy,
    brier_score,
    expected_calibration_error,
    log_loss,
    multiclass_accuracy,
    multiclass_brier_score,
    multiclass_log_loss,
    reliability_bins,
)


def test_brier_score_perfect_predictions_is_zero():
    assert brier_score([1.0, 0.0, 1.0], [1, 0, 1]) == 0.0


def test_brier_score_worst_predictions_is_one():
    assert brier_score([0.0, 1.0], [1, 0]) == 1.0


def test_brier_score_coin_flip_on_balanced_outcomes():
    assert brier_score([0.5, 0.5], [1, 0]) == pytest.approx(0.25)


def test_log_loss_confident_correct_prediction_near_zero():
    assert log_loss([0.99], [1]) < 0.02


def test_log_loss_confident_wrong_prediction_is_large():
    assert log_loss([0.01], [1]) > 4.0


def test_accuracy_counts_threshold_correctly():
    assert accuracy([0.9, 0.4, 0.6, 0.1], [1, 0, 1, 0]) == 1.0


def test_metrics_reject_mismatched_lengths():
    with pytest.raises(ValueError):
        brier_score([0.5], [1, 0])


def test_metrics_reject_empty_input():
    with pytest.raises(ValueError):
        brier_score([], [])


def test_reliability_bins_perfect_calibration():
    # 10 predictions all at 0.9, 9 of which are correct -> observed rate 0.9.
    probs = [0.9] * 10
    outcomes = [1] * 9 + [0]
    bins = reliability_bins(probs, outcomes, n_bins=10)
    populated = [b for b in bins if b.count > 0]
    assert len(populated) == 1
    assert populated[0].observed_rate == pytest.approx(0.9)


def test_expected_calibration_error_zero_when_perfectly_calibrated():
    probs = [0.5] * 100
    outcomes = [1] * 50 + [0] * 50
    assert expected_calibration_error(probs, outcomes, n_bins=10) < 0.05


def test_multiclass_brier_score_perfect_is_zero():
    dists = [{"home": 1.0, "draw": 0.0, "away": 0.0}]
    assert multiclass_brier_score(dists, ["home"]) == 0.0


def test_multiclass_log_loss_and_accuracy():
    dists = [{"home": 0.7, "draw": 0.2, "away": 0.1}, {"home": 0.2, "draw": 0.3, "away": 0.5}]
    labels = ["home", "away"]
    assert multiclass_accuracy(dists, labels) == 1.0
    assert multiclass_log_loss(dists, labels) > 0.0
