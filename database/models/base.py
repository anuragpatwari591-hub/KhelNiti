"""Declarative base and shared mixins for all KhelNiti ORM models."""
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from database.models.enums import (
    DataQuality,
    MatchStatus,
    NewsCategory,
    NewsVerificationStatus,
    PredictionResultStatus,
    Sport,
    UserRole,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    # Registers each Python Enum -> a single named Postgres ENUM type, so a
    # bare `Mapped[Sport]` annotation anywhere in the schema resolves
    # automatically instead of every column needing its own Enum(...) call.
    type_annotation_map = {
        Sport: SAEnum(Sport, name="sport"),
        DataQuality: SAEnum(DataQuality, name="data_quality"),
        MatchStatus: SAEnum(MatchStatus, name="match_status"),
        UserRole: SAEnum(UserRole, name="user_role"),
        NewsCategory: SAEnum(NewsCategory, name="news_category"),
        NewsVerificationStatus: SAEnum(NewsVerificationStatus, name="news_verification_status"),
        PredictionResultStatus: SAEnum(PredictionResultStatus, name="prediction_result_status"),
    }


class TimestampMixin:
    """created_at/updated_at columns shared by nearly every table.

    Both are set in application code (not DB defaults) so that ingestion
    pipelines can backfill historical rows with accurate timestamps while
    live-written rows get "now" automatically via the ORM default.
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
