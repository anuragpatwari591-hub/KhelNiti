"""Event-driven prediction recompute + the "why did the prediction change"
audit trail.

`CRICKET_TRIGGER_EVENTS` names the `match_events.event_type` values that
should cause a fresh prediction — not every ball, but every moment that
plausibly moves the number. Recomputing on every single delivery would be
wasteful and would drown a live feed in noise indistinguishable from a
real shift in the game state.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.predictions.service import (
    InsufficientMatchDataError,
    NoActiveModelError,
    compute_cricket_win_probability,
)
from database.models.core import Match, MatchEvent
from database.models.enums import Sport
from database.models.predictions import Prediction

CRICKET_TRIGGER_EVENTS = {"wicket", "boundary", "over_complete", "innings_break", "toss"}
FOOTBALL_TRIGGER_EVENTS = {"goal", "red_card", "penalty", "half_time", "full_time"}


def latest_two_predictions(db: Session, match_id: int, prediction_type: str) -> tuple[Prediction | None, Prediction | None]:
    """Returns (current, previous) — the two most recent predictions of
    this type for this match, most recent first.
    """
    stmt = (
        select(Prediction)
        .where(Prediction.match_id == match_id, Prediction.prediction_type == prediction_type)
        .order_by(Prediction.prediction_time.desc())
        .limit(2)
    )
    rows = db.scalars(stmt).all()
    current = rows[0] if len(rows) > 0 else None
    previous = rows[1] if len(rows) > 1 else None
    return current, previous


def explain_change(previous: Prediction | None, current: Prediction, event_type: str) -> dict:
    """Builds the "why did the prediction change" payload from two actual
    stored predictions — every number and factor here was already computed
    and persisted, nothing is invented for the explanation.
    """
    primary_outcome = next(iter(current.probabilities))
    current_p = current.probabilities[primary_outcome]
    previous_p = previous.probabilities.get(primary_outcome) if previous else None

    return {
        "outcome": primary_outcome,
        "previous_probability": previous_p,
        "new_probability": current_p,
        "delta": (current_p - previous_p) if previous_p is not None else None,
        "triggering_event": event_type,
        "reasons": current.explanation.split("; ") if current.explanation else [],
        "model_version_id": current.model_version_id,
    }


def process_match_event(db: Session, match_event: MatchEvent) -> dict | None:
    """Called right after a `MatchEvent` row is committed. Recomputes a
    prediction if the event type warrants it and returns a payload
    (prediction + change explanation) ready to broadcast — or None if this
    event type isn't a trigger, or if there wasn't enough live data yet
    (a normal condition early in a match, not an error).
    """
    match = db.get(Match, match_event.match_id)
    if match is None:
        return None

    if match.sport == Sport.CRICKET and match_event.event_type in CRICKET_TRIGGER_EVENTS:
        try:
            prediction = compute_cricket_win_probability(db, match_event.match_id)
        except (InsufficientMatchDataError, NoActiveModelError):
            return None

        _, previous = latest_two_predictions(db, match_event.match_id, "win_probability")
        change = explain_change(previous, prediction, match_event.event_type)
        return {
            "type": "prediction_update",
            "match_id": match_event.match_id,
            "prediction_id": prediction.id,
            "probabilities": prediction.probabilities,
            "model_confidence": prediction.model_confidence,
            "data_quality": prediction.data_quality.value,
            "prediction_time": prediction.prediction_time.isoformat(),
            "change": change,
        }

    # Football's Dixon-Coles live projection is match-level (not persisted
    # per-event yet) — see docs/ARCHITECTURE.md roadmap.
    return None
