"""Shared enums used across the schema.

Plain Python `enum.Enum` classes stored as `sqlalchemy.Enum` columns rather
than free-text strings, so invalid values are rejected at the DB layer.
"""
import enum


class Sport(str, enum.Enum):
    CRICKET = "cricket"
    FOOTBALL = "football"


class DataQuality(str, enum.Enum):
    """Attached to any row sourced from an external or mock provider.

    `MOCK` must never appear on data presented to a user as production
    data — the API/UI layer surfaces this value directly so mock data is
    always visibly labeled.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MOCK = "mock"


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    POSTPONED = "postponed"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class NewsVerificationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    REPORTED = "reported"
    UNVERIFIED = "unverified"


class NewsCategory(str, enum.Enum):
    INJURY = "injury"
    SUSPENSION = "suspension"
    SELECTION = "selection"
    LINEUP = "lineup"
    WEATHER = "weather"
    PITCH = "pitch"
    TRANSFER = "transfer"
    MANAGER = "manager"
    TACTICS = "tactics"
    TRAINING = "training"
    OTHER = "other"


class PredictionResultStatus(str, enum.Enum):
    PENDING = "pending"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    VOID = "void"
