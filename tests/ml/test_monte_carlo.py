import pytest

from data.ingestion.providers.mock_cricket import MockCricketProvider
from ml.cricket.monte_carlo import estimate_phase_distributions, simulate_innings_completion, simulate_match_win_probability


@pytest.fixture(scope="module")
def phase_distributions():
    provider = MockCricketProvider(seed=123)
    corpus = provider.generate_training_corpus(n_matches=15)
    deliveries = [d for m in corpus for d in m.deliveries]
    return estimate_phase_distributions(deliveries)


def test_estimate_phase_distributions_sums_to_one_per_phase(phase_distributions):
    for phase, dist in phase_distributions.items():
        total = dist.run_probs.sum() + dist.wicket_prob
        assert total == pytest.approx(1.0, abs=1e-6), phase


def test_estimate_phase_distributions_wicket_prob_higher_in_death_overs(phase_distributions):
    # Death overs carry more risk in the mock generator's own profile —
    # the estimator should recover that from the data, not assume it.
    assert phase_distributions["death"].wicket_prob > phase_distributions["powerplay"].wicket_prob


def test_simulate_innings_completion_scores_are_non_negative(phase_distributions):
    result = simulate_innings_completion(
        phase_distributions, current_score=50, wickets=2, balls_bowled=60, total_balls=120, n_simulations=500, seed=1
    )
    assert (result.final_scores >= 50).all()
    assert (result.final_wickets >= 2).all()
    assert (result.final_wickets <= 10).all()


def test_simulate_innings_completion_win_probability_is_bounded(phase_distributions):
    result = simulate_innings_completion(
        phase_distributions, current_score=100, wickets=3, balls_bowled=90, total_balls=120,
        target=150, n_simulations=500, seed=2,
    )
    assert 0.0 <= result.win_probability <= 1.0


def test_chasing_easy_target_gives_high_win_probability(phase_distributions):
    # Already past the target with balls to spare — should be ~certain.
    result = simulate_innings_completion(
        phase_distributions, current_score=150, wickets=2, balls_bowled=100, total_balls=120,
        target=120, n_simulations=200, seed=3,
    )
    assert result.win_probability > 0.95


def test_simulate_match_win_probability_second_innings_returns_valid_distribution(phase_distributions):
    result = simulate_match_win_probability(
        phase_distributions, innings_number=2, current_score=80, wickets=4, balls_bowled=80,
        total_balls=120, target=150, n_simulations=500, seed=4,
    )
    total = result["batting_team_win_probability"] + result["bowling_team_win_probability"]
    assert total == pytest.approx(1.0)
    assert 0.0 <= result["batting_team_win_probability"] <= 1.0


def test_simulate_match_win_probability_first_innings_returns_valid_distribution(phase_distributions):
    result = simulate_match_win_probability(
        phase_distributions, innings_number=1, current_score=40, wickets=1, balls_bowled=30,
        total_balls=120, target=None, n_simulations=500, seed=5,
    )
    total = result["batting_team_win_probability"] + result["bowling_team_win_probability"]
    assert total == pytest.approx(1.0)
    assert 0.0 <= result["batting_team_win_probability"] <= 1.0
