from datetime import date, timedelta

import pytest

from data.ingestion.providers.mock_football import MockFootballProvider
from ml.football.expected_goals import (
    MatchResult,
    both_teams_to_score_probability,
    clean_sheet_probability,
    fit_dixon_coles,
    outcome_probabilities,
    tau,
    top_scorelines,
)


@pytest.fixture(scope="module")
def fitted_model():
    provider = MockFootballProvider(seed=42)
    corpus = provider.generate_training_corpus(n_matches=120)
    base = date(2025, 1, 1)
    results = [
        MatchResult(m.match.home_team_name, m.match.away_team_name, m.home_goals, m.away_goals, base + timedelta(days=i))
        for i, m in enumerate(corpus)
    ]
    return fit_dixon_coles(results)


def test_tau_reduces_to_one_outside_low_scores():
    assert tau(2, 3, mu_home=1.4, mu_away=1.1, rho=0.1) == 1.0


def test_tau_applies_correction_for_low_scores():
    assert tau(0, 0, mu_home=1.4, mu_away=1.1, rho=0.1) != 1.0


def test_fit_dixon_coles_recovers_all_teams(fitted_model):
    assert set(fitted_model.attack.keys()) == set(fitted_model.teams)
    assert set(fitted_model.defense.keys()) == set(fitted_model.teams)


def test_fit_dixon_coles_home_advantage_is_positive(fitted_model):
    # The mock generator always applies a home-advantage multiplier > 1.
    assert fitted_model.home_advantage > 0


def test_score_matrix_sums_to_one(fitted_model):
    teams = fitted_model.teams
    matrix = fitted_model.score_matrix(teams[0], teams[1])
    assert matrix.sum() == pytest.approx(1.0, abs=1e-6)


def test_outcome_probabilities_sum_to_one(fitted_model):
    teams = fitted_model.teams
    matrix = fitted_model.score_matrix(teams[0], teams[1])
    probs = outcome_probabilities(matrix)
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-6)
    assert all(0.0 <= p <= 1.0 for p in probs.values())


def test_clean_sheet_and_btts_are_bounded(fitted_model):
    teams = fitted_model.teams
    matrix = fitted_model.score_matrix(teams[0], teams[1])
    assert 0.0 <= clean_sheet_probability(matrix, "home") <= 1.0
    assert 0.0 <= clean_sheet_probability(matrix, "away") <= 1.0
    assert 0.0 <= both_teams_to_score_probability(matrix) <= 1.0


def test_top_scorelines_returns_requested_count(fitted_model):
    teams = fitted_model.teams
    matrix = fitted_model.score_matrix(teams[0], teams[1])
    scorelines = top_scorelines(matrix, n=5)
    assert len(scorelines) == 5
    probs = [p for _, _, p in scorelines]
    assert probs == sorted(probs, reverse=True)


def test_expected_goals_falls_back_to_league_average_for_unseen_team(fitted_model):
    mu_home, mu_away, used_average = fitted_model.expected_goals(fitted_model.teams[0], "Unseen FC")
    assert used_average is True
    assert mu_home > 0 and mu_away > 0


def test_fit_dixon_coles_rejects_empty_input():
    with pytest.raises(ValueError):
        fit_dixon_coles([])
