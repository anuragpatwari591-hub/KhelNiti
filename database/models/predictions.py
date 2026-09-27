"""Model versioning and the full prediction audit trail.

Every prediction served to a user is persisted here — including the exact
feature snapshot that produced it and, once the match resolves, whether it
was right — so that no prediction is ever unauditable and failed
predictions are never quietly dropped.
"""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, TimestampMixin
from database.models.enums import DataQuality, PredictionResultStatus, Sport


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    training_data_start: Mapped[date | None] = mapped_column(Date)
    training_data_end: Mapped[date | None] = mapped_column(Date)
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("model_name", "version", name="uq_model_name_version"),)


class ModelMetric(Base, TimestampMixin):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)  # brier_score, log_loss, accuracy, ece
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"))
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"))
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    sport: Mapped[Sport] = mapped_column(nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    prediction_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), nullable=False)
    data_version: Mapped[str] = mapped_column(String(50), nullable=False)

    probabilities: Mapped[dict] = mapped_column(JSON, nullable=False)
    point_estimate: Mapped[float | None] = mapped_column(Float)
    data_quality: Mapped[DataQuality] = mapped_column(nullable=False)
    model_confidence: Mapped[float | None] = mapped_column(Float)
    explanation: Mapped[str | None] = mapped_column(Text)
    result_status: Mapped[PredictionResultStatus] = mapped_column(
        default=PredictionResultStatus.PENDING, nullable=False, index=True
    )


class PredictionFeature(Base, TimestampMixin):
    """The exact feature snapshot consumed by a prediction, for audit and
    for re-verifying `feature_timestamp <= prediction_time` after the fact.
    """

    __tablename__ = "prediction_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False, index=True)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"value": ...} to allow scalars/arrays
    feature_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PredictionResult(Base, TimestampMixin):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), nullable=False, unique=True)
    actual_outcome: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    brier_contribution: Mapped[float | None] = mapped_column(Float)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BacktestRun(Base, TimestampMixin):
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    train_start: Mapped[date] = mapped_column(Date, nullable=False)
    train_end: Mapped[date] = mapped_column(Date, nullable=False)
    validation_start: Mapped[date] = mapped_column(Date, nullable=False)
    validation_end: Mapped[date] = mapped_column(Date, nullable=False)
    test_start: Mapped[date] = mapped_column(Date, nullable=False)
    test_end: Mapped[date] = mapped_column(Date, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
