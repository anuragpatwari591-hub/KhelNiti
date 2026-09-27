import pytest
from sklearn.linear_model import LogisticRegression

from data.ingestion.providers.mock_cricket import MockCricketProvider
from ml.cricket.features import build_match_state, extract_features, feature_vector
from ml.cricket.monte_carlo import estimate_phase_distributions
from ml.cricket.win_probability import (
    CricketWinProbabilityEnsemble,
    predict_boundary_probability_next_ball,
    predict_next_over_runs_distribution,
    predict_wicket_probability_this_over,
)


@pytest.fixture(scope="module")
def ensemble(tmp_path_factory):
    provider = MockCricketProvider(seed=99)
    corpus = provider.generate_training_corpus(n_matches=40)

    X, y = [], []
    for m in corpus:
        for innings_number in (1, 2):
            deliveries = [d for d in m.deliveries if d.innings_number == innings_number]
            if len(deliveries) < 30:
                continue
            target = m.first_innings_runs + 1 if innings_number == 2 else None
            state = build_match_state(deliveries[:30], innings_number, target)
            label = int(
                (innings_number == 1 and m.winner == "home") or (innings_number == 2 and m.winner == "away")
            )
            X.append(feature_vector(extract_features(state)))
            y.append(label)

    model = LogisticRegression(max_iter=500).fit(X, y)
    deliveries = [d for m in corpus for d in m.deliveries]
    distributions = estimate_phase_distributions(deliveries)
    return CricketWinProbabilityEnsemble(model, distributions, version="test-1.0.0")


def test_ensemble_predict_returns_valid_distribution(ensemble):
    provider = MockCricketProvider(seed=7)
    m = provider.generate_match("ensemble-test-1")
    second_innings = [d for d in m.deliveries if d.innings_number == 2]
    state = build_match_state(second_innings[:40], 2, target=m.first_innings_runs + 1)

    prediction = ensemble.predict(state, n_simulations=300, seed=1)

    total = sum(prediction.probabilities.values())
    assert total == pytest.approx(1.0)
    assert all(0.0 <= p <= 1.0 for p in prediction.probabilities.values())
    assert 0.0 <= prediction.model_confidence <= 1.0


def test_ensemble_save_and_load_round_trip(ensemble, tmp_path):
    path = str(tmp_path / "model.joblib")
    ensemble.save(path)
    loaded = CricketWinProbabilityEnsemble.load(path)
    assert loaded.version == ensemble.version


def test_next_over_runs_distribution_sums_to_one(ensemble):
    dist = predict_next_over_runs_distribution(ensemble.distributions, over_number=10, n_simulations=2000, seed=1)
    assert sum(dist.values()) == pytest.approx(1.0, abs=1e-6)


def test_wicket_probability_this_over_is_bounded(ensemble):
    p = predict_wicket_probability_this_over(ensemble.distributions, over_number=18)
    assert 0.0 <= p <= 1.0


def test_boundary_probability_next_ball_is_bounded(ensemble):
    p = predict_boundary_probability_next_ball(ensemble.distributions, over_number=3)
    assert 0.0 <= p <= 1.0
