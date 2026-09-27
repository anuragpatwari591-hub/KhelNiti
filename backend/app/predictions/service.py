"""Bridges the DB-backed match state to the ML layer and persists the
resulting prediction as a full audit record — this is the one place the
API touches `ml/cricket`, so the API never has to know how the model
works, only how to ask for a prediction and store what it got back.
"""
import os
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.validation.exceptions import InvalidDataError
from database.models.cricket import Delivery, Innings
from database.models.core import Match
from database.models.enums import PredictionResultStatus, Sport
from database.models.predictions import ModelVersion, Prediction, PredictionFeature
from ml.cricket.features import build_match_state, extract_features
from ml.cricket.win_probability import CricketWinProbabilityEnsemble

CRICKET_WIN_PROBABILITY_MODEL_NAME = "cricket_win_probability"


class NoActiveModelError(Exception):
    pass


class InsufficientMatchDataError(Exception):
    pass


@lru_cache(maxsize=4)
def _load_ensemble(artifact_path: str) -> CricketWinProbabilityEnsemble:
    return CricketWinProbabilityEnsemble.load(artifact_path)


def _active_model_version(db: Session, model_name: str, sport: Sport) -> ModelVersion:
    model_version = db.scalar(
        select(ModelVersion)
        .where(ModelVersion.model_name == model_name, ModelVersion.sport == sport, ModelVersion.is_active.is_(True))
        .order_by(ModelVersion.trained_at.desc())
    )
    if model_version is None:
        raise NoActiveModelError(
            f"No active model_versions row for '{model_name}' — run "
            f"`python -m ml.training.train_cricket_win_probability` first."
        )
    return model_version


def compute_cricket_win_probability(db: Session, match_id: int) -> Prediction:
    match = db.get(Match, match_id)
    if match is None:
        raise InsufficientMatchDataError(f"Match {match_id} not found")
    if match.sport != Sport.CRICKET:
        raise InsufficientMatchDataError(f"Match {match_id} is not a cricket match")

    latest_innings = db.scalar(
        select(Innings).where(Innings.match_id == match_id).order_by(Innings.innings_number.desc())
    )
    if latest_innings is None:
        raise InsufficientMatchDataError(f"Match {match_id} has no innings data yet")

    deliveries = db.scalars(
        select(Delivery).where(Delivery.innings_id == latest_innings.id).order_by(Delivery.sequence)
    ).all()
    if not deliveries:
        raise InsufficientMatchDataError(f"Innings {latest_innings.id} has no deliveries yet")

    target = latest_innings.target if latest_innings.innings_number == 2 else None
    try:
        state = build_match_state(deliveries, latest_innings.innings_number, target)
    except ValueError as exc:
        raise InsufficientMatchDataError(str(exc)) from exc

    model_version = _active_model_version(db, CRICKET_WIN_PROBABILITY_MODEL_NAME, Sport.CRICKET)
    if not model_version.artifact_path or not os.path.exists(model_version.artifact_path):
        raise NoActiveModelError(f"Active model_versions.id={model_version.id} has no usable artifact_path")

    ensemble = _load_ensemble(model_version.artifact_path)
    result = ensemble.predict(state)

    now = datetime.now(timezone.utc)
    prediction = Prediction(
        match_id=match_id,
        sport=Sport.CRICKET,
        prediction_type="win_probability",
        prediction_time=now,
        model_version_id=model_version.id,
        feature_version="v1",
        data_version=match.data_quality.value,
        probabilities=result.probabilities,
        model_confidence=result.model_confidence,
        data_quality=match.data_quality,
        explanation="; ".join(result.top_factors) if result.top_factors else None,
        result_status=PredictionResultStatus.PENDING,
    )
    db.add(prediction)
    db.flush()

    for name, value in result.feature_snapshot.items():
        db.add(
            PredictionFeature(
                prediction_id=prediction.id,
                feature_name=name,
                feature_value={"value": value},
                feature_timestamp=state.as_of,
            )
        )

    db.commit()
    db.refresh(prediction)
    return prediction
