"""Cricket win-probability ensemble: calibrated logistic regression blended
with Monte Carlo simulation, plus lightweight next-ball/next-over
projections derived from the same empirical phase distributions.

Neither component is trusted alone: the logistic model captures learned
patterns across many historical matches' match-states, while the Monte
Carlo simulation reasons forward from the exact current state using
empirical ball-outcome frequencies. Blending them, and reporting how much
they agree as `model_confidence`, is more honest than presenting either
number alone as "the" probability.
"""
from dataclasses import dataclass

import joblib
import numpy as np

from data.validation.probability import assert_valid_distribution
from ml.cricket.features import FEATURE_ORDER, MatchState, extract_features, feature_vector, phase_for_over
from ml.cricket.monte_carlo import RUN_VALUES, PhaseDistribution, simulate_match_win_probability


@dataclass(frozen=True)
class WinProbabilityPrediction:
    probabilities: dict[str, float]  # {"batting_team": p, "bowling_team": 1-p}
    model_confidence: float  # 1 - |logistic_p - monte_carlo_p|, in [0, 1]
    logistic_probability: float
    monte_carlo_probability: float
    top_factors: list[str]
    feature_snapshot: dict[str, float]


class CricketWinProbabilityEnsemble:
    """`version` should match a `model_versions.version` row once trained
    and registered (see ml/training/train_cricket_win_probability.py)."""

    def __init__(self, logistic_model, distributions: dict[str, PhaseDistribution], version: str):
        self.logistic_model = logistic_model
        self.distributions = distributions
        self.version = version

    def predict(self, state: MatchState, n_simulations: int = 1500, seed: int | None = None) -> WinProbabilityPrediction:
        features = extract_features(state)
        vector = np.array([feature_vector(features)])

        logistic_p = float(self.logistic_model.predict_proba(vector)[0, 1])

        mc = simulate_match_win_probability(
            self.distributions,
            innings_number=state.innings_number,
            current_score=state.current_score,
            wickets=state.wickets_lost,
            balls_bowled=state.balls_bowled,
            total_balls=state.total_balls,
            target=state.target,
            n_simulations=n_simulations,
            seed=seed,
        )
        monte_carlo_p = mc["batting_team_win_probability"]

        blended_p = float(np.clip(0.5 * logistic_p + 0.5 * monte_carlo_p, 0.0, 1.0))
        confidence = float(1.0 - abs(logistic_p - monte_carlo_p))

        probabilities = {"batting_team": blended_p, "bowling_team": 1.0 - blended_p}
        assert_valid_distribution(probabilities, "cricket_win_probability")

        top_factors = _explain(features)

        return WinProbabilityPrediction(
            probabilities=probabilities,
            model_confidence=confidence,
            logistic_probability=logistic_p,
            monte_carlo_probability=monte_carlo_p,
            top_factors=top_factors,
            feature_snapshot={name: f.value for name, f in features.items()},
        )

    def save(self, path: str) -> None:
        joblib.dump({"logistic_model": self.logistic_model, "distributions": self.distributions, "version": self.version}, path)

    @classmethod
    def load(cls, path: str) -> "CricketWinProbabilityEnsemble":
        payload = joblib.load(path)
        return cls(payload["logistic_model"], payload["distributions"], payload["version"])


def _explain(features: dict) -> list[str]:
    """Plain-language factors driving the current state, ordered by
    magnitude — feeds the "why did the prediction change" audit trail.
    Never invents a reason: every entry is derived directly from a feature
    value that was actually computed.
    """
    factors = []
    pressure = features.get("pressure_index")
    if pressure is not None:
        if pressure.value > 1.5:
            factors.append("required run rate is well above the current run rate")
        elif pressure.value < -1.5:
            factors.append("current run rate is comfortably ahead of what's required")
    wickets_in_hand = features.get("wickets_in_hand")
    if wickets_in_hand is not None:
        if wickets_in_hand.value <= 3:
            factors.append("few wickets remain in hand")
        elif wickets_in_hand.value >= 8:
            factors.append("most wickets are still in hand")
    if features.get("is_death_overs") and features["is_death_overs"].value == 1.0:
        factors.append("match is in the death overs")
    return factors[:3]


def predict_next_over_runs_distribution(
    distributions: dict[str, PhaseDistribution], over_number: int, n_simulations: int = 5000, seed: int | None = None
) -> dict[int, float]:
    """Distribution over total runs scored in the next over, simulated from
    the phase's per-ball distribution (6 independent draws)."""
    rng = np.random.default_rng(seed)
    dist = distributions[phase_for_over(over_number)]
    outcomes = np.concatenate([dist.run_probs, [dist.wicket_prob]])
    outcomes = outcomes / outcomes.sum()

    draws = rng.choice(len(outcomes), size=(n_simulations, 6), p=outcomes)
    is_wicket = draws == len(RUN_VALUES)
    runs = np.where(is_wicket, 0, RUN_VALUES[np.clip(draws, 0, len(RUN_VALUES) - 1)])
    over_totals = runs.sum(axis=1)

    values, counts = np.unique(over_totals, return_counts=True)
    total = counts.sum()
    return {int(v): float(c) / total for v, c in zip(values, counts)}


def predict_wicket_probability_this_over(distributions: dict[str, PhaseDistribution], over_number: int) -> float:
    p_ball = distributions[phase_for_over(over_number)].wicket_prob
    return 1.0 - (1.0 - p_ball) ** 6


def predict_boundary_probability_next_ball(distributions: dict[str, PhaseDistribution], over_number: int) -> float:
    dist = distributions[phase_for_over(over_number)]
    boundary_indices = [i for i, v in enumerate(RUN_VALUES) if v in (4, 6)]
    return float(dist.run_probs[boundary_indices].sum())
