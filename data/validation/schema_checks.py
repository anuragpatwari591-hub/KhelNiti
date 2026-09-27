"""Domain sanity checks for incoming delivery/event payloads.

Hard violations (impossible values) raise `InvalidDataError` and the record
must be rejected. Soft issues (e.g. a bowler name not found in the known
squad) are returned as warnings — callers should downgrade `data_quality`
rather than invent the missing information (per the "missing data reduces
data-quality rather than being silently invented" rule).
"""
from datetime import datetime

from data.ingestion.providers.types import DeliveryPayload, FootballEventPayload
from data.validation.exceptions import InvalidDataError


def validate_delivery(payload: DeliveryPayload, match_scheduled_start: datetime | None = None) -> list[str]:
    warnings: list[str] = []

    if payload.runs_batter < 0 or payload.runs_batter > 6:
        raise InvalidDataError(f"Impossible runs_batter={payload.runs_batter} at sequence {payload.sequence}")
    if payload.runs_extras < 0:
        raise InvalidDataError(f"Negative runs_extras at sequence {payload.sequence}")
    if payload.wickets_before_ball < 0 or payload.wickets_before_ball > 10:
        raise InvalidDataError(f"Impossible wickets_before_ball={payload.wickets_before_ball}")
    if payload.score_before_ball < 0:
        raise InvalidDataError(f"Negative score_before_ball at sequence {payload.sequence}")
    if payload.over_number < 0:
        raise InvalidDataError(f"Negative over_number at sequence {payload.sequence}")
    if not (1 <= payload.ball_number <= 9):
        # Allow up to 9 to accommodate extras re-bowled within an over.
        raise InvalidDataError(f"Implausible ball_number={payload.ball_number} at sequence {payload.sequence}")
    if match_scheduled_start is not None and payload.delivery_time < match_scheduled_start:
        raise InvalidDataError(
            f"delivery_time {payload.delivery_time.isoformat()} precedes match start "
            f"{match_scheduled_start.isoformat()}"
        )
    if payload.is_wicket and not payload.dismissal_type:
        warnings.append("is_wicket=True but dismissal_type missing")
    if not payload.batter_name:
        warnings.append("batter_name missing")
    if not payload.bowler_name:
        warnings.append("bowler_name missing")

    return warnings


def validate_football_event(payload: FootballEventPayload, match_scheduled_start: datetime | None = None) -> list[str]:
    warnings: list[str] = []

    if not (0 <= payload.minute <= 130):
        raise InvalidDataError(f"Implausible minute={payload.minute} for event {payload.event_type}")
    if payload.added_time is not None and payload.added_time < 0:
        raise InvalidDataError("Negative added_time")
    if payload.shot_x is not None and not (0 <= payload.shot_x <= 100):
        raise InvalidDataError(f"shot_x={payload.shot_x} out of pitch-percentage range 0..100")
    if payload.shot_y is not None and not (0 <= payload.shot_y <= 100):
        raise InvalidDataError(f"shot_y={payload.shot_y} out of pitch-percentage range 0..100")
    if match_scheduled_start is not None and payload.event_time < match_scheduled_start:
        raise InvalidDataError(
            f"event_time {payload.event_time.isoformat()} precedes match start "
            f"{match_scheduled_start.isoformat()}"
        )
    if payload.event_type in {"goal", "yellow_card", "red_card"} and not payload.player_name:
        warnings.append(f"{payload.event_type} event missing player_name")

    return warnings


def validate_delivery_sequence_monotonic(payloads: list[DeliveryPayload]) -> None:
    """Deliveries within one innings must be strictly increasing in
    `sequence` — anything else means the provider sent out-of-order or
    duplicate data.
    """
    last_sequence = -1
    for p in payloads:
        if p.sequence <= last_sequence:
            raise InvalidDataError(
                f"Non-monotonic delivery sequence: {p.sequence} follows {last_sequence}"
            )
        last_sequence = p.sequence
