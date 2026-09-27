from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.authentication.deps import get_current_user
from backend.app.database import get_db
from backend.app.predictions.schemas import PredictionFeatureOut, PredictionOut
from backend.app.predictions.service import (
    InsufficientMatchDataError,
    NoActiveModelError,
    compute_cricket_win_probability,
)
from database.models.core import User
from database.models.predictions import ModelVersion, Prediction, PredictionFeature

router = APIRouter(tags=["predictions"])


def _to_prediction_out(db: Session, prediction: Prediction) -> PredictionOut:
    model_version = db.get(ModelVersion, prediction.model_version_id)
    return PredictionOut(
        id=prediction.id,
        match_id=prediction.match_id,
        sport=prediction.sport.value,
        prediction_type=prediction.prediction_type,
        prediction_time=prediction.prediction_time,
        model_name=model_version.model_name,
        model_version=model_version.version,
        probabilities=prediction.probabilities,
        model_confidence=prediction.model_confidence,
        data_quality=prediction.data_quality.value,
        explanation=prediction.explanation,
        result_status=prediction.result_status.value,
    )


@router.post("/matches/{match_id}/predictions/win-probability", response_model=PredictionOut)
def create_cricket_win_probability_prediction(
    match_id: int, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)
):
    try:
        prediction = compute_cricket_win_probability(db, match_id)
    except NoActiveModelError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except InsufficientMatchDataError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return _to_prediction_out(db, prediction)


@router.get("/matches/{match_id}/predictions", response_model=list[PredictionOut])
def list_match_predictions(match_id: int, limit: int = Query(default=20, le=100), db: Session = Depends(get_db)):
    stmt = (
        select(Prediction)
        .where(Prediction.match_id == match_id)
        .order_by(Prediction.prediction_time.desc())
        .limit(limit)
    )
    predictions = db.scalars(stmt).all()
    return [_to_prediction_out(db, p) for p in predictions]


@router.get("/predictions/{prediction_id}/features", response_model=list[PredictionFeatureOut])
def list_prediction_features(prediction_id: int, db: Session = Depends(get_db)):
    prediction = db.get(Prediction, prediction_id)
    if prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    stmt = select(PredictionFeature).where(PredictionFeature.prediction_id == prediction_id)
    return db.scalars(stmt).all()
