from datetime import datetime

from pydantic import BaseModel


class PredictionOut(BaseModel):
    """Mirrors the spec's probability-display rule: a probability is never
    shown without its timestamp, model version, and data-quality context.
    """

    model_config = {"protected_namespaces": ()}

    id: int
    match_id: int
    sport: str
    prediction_type: str
    prediction_time: datetime
    model_name: str
    model_version: str
    probabilities: dict[str, float]
    model_confidence: float | None
    data_quality: str
    explanation: str | None
    result_status: str


class PredictionFeatureOut(BaseModel):
    feature_name: str
    feature_value: dict
    feature_timestamp: datetime

    model_config = {"from_attributes": True}
