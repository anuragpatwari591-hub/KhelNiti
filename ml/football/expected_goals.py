"""Dixon-Coles expected-goals model for football.

A Poisson goal-scoring model with per-team attack/defense strengths, a
home-advantage term, and the Dixon & Coles (1997) low-score correlation
correction (`tau`) for the 0-0/1-0/0-1/1-1 scorelines, where two
independent Poisson processes are known to systematically mis-fit real
football data. Parameters are estimated by maximum likelihood
(`scipy.optimize.minimize`) on historical match goal counts — nothing here
is a hand-picked constant.
"""
from dataclasses import dataclass, field
from datetime import date

import joblib
import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

_RHO_BOUNDS = (-0.5, 0.5)
_HOME_ADV_BOUNDS = (-2.0, 2.0)
_STRENGTH_BOUNDS = (-3.0, 3.0)


@dataclass(frozen=True)
class MatchResult:
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    match_date: date | None = None


def tau(x: int, y: int, mu_home: float, mu_away: float, rho: float) -> float:
    if x == 0 and y == 0:
        value = 1 - mu_home * mu_away * rho
    elif x == 0 and y == 1:
        value = 1 + mu_home * rho
    elif x == 1 and y == 0:
        value = 1 + mu_away * rho
    elif x == 1 and y == 1:
        value = 1 - rho
    else:
        value = 1.0
    return max(value, 1e-6)  # keep the optimizer's log() well-defined off-optimum


@dataclass
class DixonColesModel:
    teams: list[str]
    attack: dict[str, float]
    defense: dict[str, float]
    home_advantage: float
    rho: float
    version: str
    league_average_attack: float = field(default=0.0)
    league_average_defense: float = field(default=0.0)

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float, bool]:
        """Returns (mu_home, mu_away, used_league_average). The third value
        is True if either team was unseen in training and league-average
        strength was substituted — callers should reflect this as lower
        data quality rather than presenting it as a fully-informed estimate.
        """
        used_average = home_team not in self.attack or away_team not in self.attack
        a_home = self.attack.get(home_team, self.league_average_attack)
        d_home = self.defense.get(home_team, self.league_average_defense)
        a_away = self.attack.get(away_team, self.league_average_attack)
        d_away = self.defense.get(away_team, self.league_average_defense)

        mu_home = float(np.exp(a_home - d_away + self.home_advantage))
        mu_away = float(np.exp(a_away - d_home))
        return mu_home, mu_away, used_average

    def score_matrix(self, home_team: str, away_team: str, max_goals: int = 8) -> np.ndarray:
        mu_home, mu_away, _ = self.expected_goals(home_team, away_team)
        matrix = np.zeros((max_goals + 1, max_goals + 1))
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                matrix[x, y] = (
                    poisson.pmf(x, mu_home) * poisson.pmf(y, mu_away) * tau(x, y, mu_home, mu_away, self.rho)
                )
        return matrix / matrix.sum()

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "DixonColesModel":
        return joblib.load(path)


def outcome_probabilities(matrix: np.ndarray) -> dict[str, float]:
    home = float(np.tril(matrix, -1).sum())
    draw = float(np.trace(matrix))
    away = float(np.triu(matrix, 1).sum())
    return {"home": home, "draw": draw, "away": away}


def clean_sheet_probability(matrix: np.ndarray, side: str) -> float:
    if side == "home":
        return float(matrix[:, 0].sum())  # away scored 0
    if side == "away":
        return float(matrix[0, :].sum())  # home scored 0
    raise ValueError("side must be 'home' or 'away'")


def both_teams_to_score_probability(matrix: np.ndarray) -> float:
    return float(matrix[1:, 1:].sum())


def top_scorelines(matrix: np.ndarray, n: int = 5) -> list[tuple[int, int, float]]:
    flat_indices = np.argsort(matrix, axis=None)[::-1][:n]
    return [(int(idx // matrix.shape[1]), int(idx % matrix.shape[1]), float(matrix.flat[idx])) for idx in flat_indices]


def fit_dixon_coles(matches: list[MatchResult], xi: float = 0.0, as_of: date | None = None) -> DixonColesModel:
    """Maximum-likelihood fit. `xi` is an optional exponential time-decay
    rate (Dixon & Coles' own recency-weighting device) — 0 means every
    historical match is weighted equally; a small positive value
    down-weights older matches relative to `as_of` (defaults to the most
    recent match date in the data), giving recent form more influence.
    """
    if not matches:
        raise ValueError("fit_dixon_coles requires at least one match")

    teams = sorted({m.home_team for m in matches} | {m.away_team for m in matches})
    idx = {team: i for i, team in enumerate(teams)}
    n = len(teams)

    if xi > 0:
        reference_date = as_of or max(m.match_date for m in matches if m.match_date is not None)
        weights = np.array(
            [np.exp(-xi * (reference_date - m.match_date).days) if m.match_date else 1.0 for m in matches]
        )
    else:
        weights = np.ones(len(matches))

    home_idx = np.array([idx[m.home_team] for m in matches])
    away_idx = np.array([idx[m.away_team] for m in matches])
    home_goals = np.array([m.home_goals for m in matches])
    away_goals = np.array([m.away_goals for m in matches])

    def negative_log_likelihood(params: np.ndarray) -> float:
        attack = params[:n]
        defense = params[n : 2 * n]
        home_adv = params[2 * n]
        rho = params[2 * n + 1]

        mu_home = np.exp(attack[home_idx] - defense[away_idx] + home_adv)
        mu_away = np.exp(attack[away_idx] - defense[home_idx])

        log_lik = poisson.logpmf(home_goals, mu_home) + poisson.logpmf(away_goals, mu_away)
        tau_terms = np.array(
            [np.log(tau(int(x), int(y), mh, ma, rho)) for x, y, mh, ma in zip(home_goals, away_goals, mu_home, mu_away)]
        )
        return -float(np.sum(weights * (log_lik + tau_terms)))

    x0 = np.concatenate([np.zeros(n), np.zeros(n), [0.2], [-0.1]])
    bounds = [_STRENGTH_BOUNDS] * n + [_STRENGTH_BOUNDS] * n + [_HOME_ADV_BOUNDS, _RHO_BOUNDS]

    result = minimize(negative_log_likelihood, x0, method="L-BFGS-B", bounds=bounds)

    attack_arr = result.x[:n]
    defense_arr = result.x[n : 2 * n]
    # Normalize so mean attack strength is 0 (predictions are unaffected —
    # attack and defense only ever appear as differences — this just makes
    # the individual ratings interpretable).
    shift = attack_arr.mean()
    attack_arr = attack_arr - shift
    defense_arr = defense_arr - shift

    return DixonColesModel(
        teams=teams,
        attack=dict(zip(teams, attack_arr.tolist())),
        defense=dict(zip(teams, defense_arr.tolist())),
        home_advantage=float(result.x[2 * n]),
        rho=float(result.x[2 * n + 1]),
        version="unversioned",
        league_average_attack=0.0,
        league_average_defense=0.0,
    )
