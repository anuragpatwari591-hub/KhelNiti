"""Monte Carlo simulation of remaining cricket innings.

Phase (powerplay/middle/death) run and wicket distributions are estimated
empirically from historical ball-by-ball data (`estimate_phase_distributions`)
rather than hard-coded, so the simulator reflects whatever data it was
built from. Simulation is vectorized with numpy: each of `n_simulations`
independent trajectories is advanced one ball at a time.
"""
from dataclasses import dataclass

import numpy as np

from ml.cricket.features import phase_for_over

RUN_VALUES = np.array([0, 1, 2, 3, 4, 6])


@dataclass(frozen=True)
class PhaseDistribution:
    run_probs: np.ndarray  # aligned with RUN_VALUES, sums to (1 - wicket_prob)
    wicket_prob: float


def estimate_phase_distributions(deliveries: list) -> dict[str, PhaseDistribution]:
    """`deliveries` is any iterable of objects with `.over_number`,
    `.runs_batter`, `.is_wicket` (e.g. `DeliveryPayload` or ORM `Delivery`
    rows) drawn from real (or mock) historical matches.
    """
    counts = {
        phase: {"runs": np.zeros(len(RUN_VALUES)), "wickets": 0, "balls": 0}
        for phase in ("powerplay", "middle", "death")
    }
    for d in deliveries:
        phase = phase_for_over(d.over_number)
        counts[phase]["balls"] += 1
        if d.is_wicket:
            counts[phase]["wickets"] += 1
        else:
            idx = np.searchsorted(RUN_VALUES, d.runs_batter)
            if idx < len(RUN_VALUES) and RUN_VALUES[idx] == d.runs_batter:
                counts[phase]["runs"][idx] += 1

    distributions = {}
    for phase, c in counts.items():
        balls = max(c["balls"], 1)
        wicket_prob = c["wickets"] / balls
        run_probs = c["runs"] / balls
        # Normalize the non-wicket mass to exactly (1 - wicket_prob) so the
        # full distribution (runs + wicket) sums to 1.
        non_wicket_mass = run_probs.sum()
        if non_wicket_mass > 0:
            run_probs = run_probs * (1 - wicket_prob) / non_wicket_mass
        distributions[phase] = PhaseDistribution(run_probs=run_probs, wicket_prob=wicket_prob)
    return distributions


def _simulate_balls(
    distributions: dict[str, PhaseDistribution],
    start_score: np.ndarray,
    start_wickets: np.ndarray,
    start_over: int,
    balls_remaining: int,
    target: int | None,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """Advances `n_simulations` trajectories `balls_remaining` balls
    forward. Returns (final_scores, final_wickets, reached_target_mask).
    """
    n = start_score.shape[0]
    score = start_score.copy()
    wickets = start_wickets.copy()
    reached_target = np.zeros(n, dtype=bool) if target is not None else None
    active = wickets < 10

    ball_global = start_over * 6
    for _ in range(balls_remaining):
        if not active.any():
            break
        over_number = ball_global // 6
        phase = phase_for_over(over_number)
        dist = distributions[phase]

        outcomes = np.concatenate([dist.run_probs, [dist.wicket_prob]])
        outcomes = outcomes / outcomes.sum()  # guard against float drift
        draws = rng.choice(len(outcomes), size=n, p=outcomes)

        is_wicket_draw = draws == len(RUN_VALUES)
        runs_draw = np.where(is_wicket_draw, 0, RUN_VALUES[np.clip(draws, 0, len(RUN_VALUES) - 1)])

        score = np.where(active, score + runs_draw, score)
        wickets = np.where(active & is_wicket_draw, wickets + 1, wickets)
        active = wickets < 10

        if target is not None:
            newly_reached = active & (score >= target)
            reached_target = reached_target | newly_reached
            active = active & ~newly_reached

        ball_global += 1

    return score, wickets, reached_target


@dataclass(frozen=True)
class SimulationResult:
    final_scores: np.ndarray
    final_wickets: np.ndarray
    win_probability: float | None  # only set when a target was given


def simulate_innings_completion(
    distributions: dict[str, PhaseDistribution],
    current_score: int,
    wickets: int,
    balls_bowled: int,
    total_balls: int = 120,
    target: int | None = None,
    n_simulations: int = 2000,
    seed: int | None = None,
) -> SimulationResult:
    rng = np.random.default_rng(seed)
    balls_remaining = max(total_balls - balls_bowled, 0)
    start_score = np.full(n_simulations, current_score, dtype=np.int64)
    start_wickets = np.full(n_simulations, wickets, dtype=np.int64)

    final_scores, final_wickets, reached_target = _simulate_balls(
        distributions, start_score, start_wickets, balls_bowled // 6, balls_remaining, target, rng
    )

    win_probability = float(reached_target.mean()) if reached_target is not None else None
    return SimulationResult(final_scores=final_scores, final_wickets=final_wickets, win_probability=win_probability)


def simulate_match_win_probability(
    distributions: dict[str, PhaseDistribution],
    innings_number: int,
    current_score: int,
    wickets: int,
    balls_bowled: int,
    total_balls: int = 120,
    target: int | None = None,
    n_simulations: int = 2000,
    seed: int | None = None,
) -> dict:
    """Win probability for the team currently batting, from any point in
    the match.

    - Second innings (a target exists): direct Monte Carlo of the chase.
    - First innings: simulate the remaining first-innings balls to get a
      distribution of possible final totals, then, for a representative
      set of those totals, simulate a full second-innings chase to
      estimate each one's chase-success probability. The team batting
      first wins in proportion to how often the sampled chase fails.
    """
    if innings_number == 2:
        if target is None:
            raise ValueError("innings_number=2 requires a target")
        result = simulate_innings_completion(
            distributions, current_score, wickets, balls_bowled, total_balls, target, n_simulations, seed
        )
        p_batting_wins = result.win_probability
    else:
        first_innings = simulate_innings_completion(
            distributions, current_score, wickets, balls_bowled, total_balls, None, n_simulations, seed
        )
        totals = first_innings.final_scores
        bucket_width = 5
        buckets = (totals // bucket_width) * bucket_width
        unique_buckets, counts = np.unique(buckets, return_counts=True)
        weights = counts / counts.sum()

        chase_sim_count = max(200, n_simulations // max(len(unique_buckets), 1))
        p_chase_success_by_bucket = []
        for bucket_value in unique_buckets:
            chase_target = int(bucket_value) + bucket_width // 2 + 1
            chase_result = simulate_innings_completion(
                distributions, 0, 0, 0, total_balls, chase_target, chase_sim_count,
                seed=None if seed is None else seed + int(bucket_value),
            )
            p_chase_success_by_bucket.append(chase_result.win_probability)

        p_chase_success = float(np.dot(weights, p_chase_success_by_bucket))
        p_batting_wins = 1.0 - p_chase_success

    return {
        "batting_team_win_probability": p_batting_wins,
        "bowling_team_win_probability": 1.0 - p_batting_wins,
        "n_simulations": n_simulations,
    }
