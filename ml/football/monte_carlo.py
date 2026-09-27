"""Monte Carlo simulation of a football match's remaining minutes.

Given the pre-match expected goal rates (from the Dixon-Coles model) and
the current live state (minute, score so far), simulates the rest of the
match by drawing additional goals for each side from a Poisson
distribution scaled to the remaining playing time. This assumes goals in
the remaining minutes are independent of what has already happened beyond
the elapsed-time scaling — a reasonable, explainable simplification for a
live in-match projection, not a claim of perfect realism (e.g. it does not
model a team parking the bus while protecting a lead).
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MatchSimulationResult:
    final_home_goals: np.ndarray
    final_away_goals: np.ndarray

    def outcome_probabilities(self) -> dict[str, float]:
        n = len(self.final_home_goals)
        home = float(np.sum(self.final_home_goals > self.final_away_goals)) / n
        draw = float(np.sum(self.final_home_goals == self.final_away_goals)) / n
        away = float(np.sum(self.final_home_goals < self.final_away_goals)) / n
        return {"home": home, "draw": draw, "away": away}

    def scoreline_distribution(self, top_n: int = 5) -> list[tuple[int, int, float]]:
        n = len(self.final_home_goals)
        pairs = list(zip(self.final_home_goals.tolist(), self.final_away_goals.tolist()))
        unique, counts = np.unique(pairs, axis=0, return_counts=True)
        order = np.argsort(counts)[::-1][:top_n]
        return [(int(unique[i][0]), int(unique[i][1]), float(counts[i]) / n) for i in order]


def simulate_remaining_match(
    mu_home_full_match: float,
    mu_away_full_match: float,
    minutes_elapsed: int,
    home_goals_so_far: int,
    away_goals_so_far: int,
    match_length_minutes: int = 90,
    n_simulations: int = 5000,
    seed: int | None = None,
) -> MatchSimulationResult:
    rng = np.random.default_rng(seed)
    remaining_fraction = max(match_length_minutes - minutes_elapsed, 0) / match_length_minutes

    additional_home = rng.poisson(mu_home_full_match * remaining_fraction, size=n_simulations)
    additional_away = rng.poisson(mu_away_full_match * remaining_fraction, size=n_simulations)

    return MatchSimulationResult(
        final_home_goals=home_goals_so_far + additional_home,
        final_away_goals=away_goals_so_far + additional_away,
    )
