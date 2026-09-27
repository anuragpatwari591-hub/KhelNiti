"""Live match-state feature extraction for cricket.

Every feature is derived purely from deliveries bowled *up to and
including* the ball being evaluated — there is no lookahead into future
balls, so a `MatchState` built from `deliveries_so_far` is safe to use for
a prediction timestamped at that same ball's `delivery_time`.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from data.validation.leakage import TimestampedFeature


class _DeliveryLike(Protocol):
    over_number: int
    ball_number: int
    runs_batter: int
    runs_extras: int
    is_wicket: bool
    score_before_ball: int
    wickets_before_ball: int
    delivery_time: datetime


def phase_for_over(over_number: int) -> str:
    if over_number < 6:
        return "powerplay"
    if over_number < 16:
        return "middle"
    return "death"


@dataclass(frozen=True)
class MatchState:
    innings_number: int
    balls_bowled: int
    total_balls: int
    current_score: int
    wickets_lost: int
    target: int | None
    as_of: datetime


def build_match_state(
    deliveries_so_far: list[_DeliveryLike],
    innings_number: int,
    target: int | None,
    total_overs: int = 20,
) -> MatchState:
    total_balls = total_overs * 6
    if not deliveries_so_far:
        raise ValueError("cannot build match state with zero deliveries")
    last = deliveries_so_far[-1]
    current_score = last.score_before_ball + last.runs_batter + last.runs_extras
    wickets_lost = last.wickets_before_ball + (1 if last.is_wicket else 0)
    return MatchState(
        innings_number=innings_number,
        balls_bowled=len(deliveries_so_far),
        total_balls=total_balls,
        current_score=current_score,
        wickets_lost=wickets_lost,
        target=target,
        as_of=last.delivery_time,
    )


def extract_features(state: MatchState) -> dict[str, TimestampedFeature]:
    balls_remaining = max(state.total_balls - state.balls_bowled, 0)
    overs_bowled = state.balls_bowled / 6.0
    overs_remaining = balls_remaining / 6.0
    wickets_in_hand = 10 - state.wickets_lost
    current_run_rate = state.current_score / overs_bowled if overs_bowled > 0 else 0.0

    required_run_rate = None
    runs_needed = None
    pressure_index = 0.0
    if state.target is not None:
        runs_needed = max(state.target - state.current_score, 0)
        required_run_rate = runs_needed / overs_remaining if overs_remaining > 0 else float("inf")
        pressure_index = (required_run_rate - current_run_rate) if required_run_rate != float("inf") else 999.0

    current_over = state.balls_bowled // 6
    values: dict[str, float] = {
        "balls_bowled": float(state.balls_bowled),
        "balls_remaining": float(balls_remaining),
        "wickets_lost": float(state.wickets_lost),
        "wickets_in_hand": float(wickets_in_hand),
        "current_score": float(state.current_score),
        "current_run_rate": current_run_rate,
        "is_powerplay": float(phase_for_over(current_over) == "powerplay"),
        "is_middle_overs": float(phase_for_over(current_over) == "middle"),
        "is_death_overs": float(phase_for_over(current_over) == "death"),
        "is_second_innings": float(state.innings_number == 2),
    }
    if required_run_rate is not None:
        values["required_run_rate"] = min(required_run_rate, 99.0)
        values["runs_needed"] = float(runs_needed)
        values["pressure_index"] = min(pressure_index, 99.0)

    return {name: TimestampedFeature(name=name, value=value, feature_timestamp=state.as_of) for name, value in values.items()}


FEATURE_ORDER = [
    "balls_remaining",
    "wickets_in_hand",
    "current_run_rate",
    "required_run_rate",
    "runs_needed",
    "pressure_index",
    "is_powerplay",
    "is_death_overs",
]


def feature_vector(features: dict[str, TimestampedFeature]) -> list[float]:
    """Fixed-order numeric vector for the win-probability model. Missing
    keys (e.g. `required_run_rate` during the first innings) default to 0,
    matching how the training pipeline encodes first-innings rows.
    """
    return [features[name].value if name in features else 0.0 for name in FEATURE_ORDER]
