"""All ORM models, imported here so `Base.metadata` is complete for Alembic
autogenerate and for `Base.metadata.create_all()` in tests.
"""
from database.models.base import Base
from database.models.context import (
    MarketMovement,
    NewsArticle,
    NewsEntity,
    OddsSnapshot,
    WeatherSnapshot,
)
from database.models.core import (
    Competition,
    Lineup,
    Match,
    MatchEvent,
    Player,
    Season,
    Team,
    User,
    Venue,
)
from database.models.cricket import (
    Delivery,
    Innings,
    PlayerBowlerMatchup,
    PlayerCompetitionStats,
    PlayerMatchStats,
    PlayerOpponentStats,
    PlayerVenueStats,
    TeamMatchStats,
)
from database.models.football import FootballEvent, FootballPlayerStats, FootballTeamStats
from database.models.predictions import (
    BacktestRun,
    ModelMetric,
    ModelVersion,
    Prediction,
    PredictionFeature,
    PredictionResult,
)

__all__ = [
    "Base",
    "User",
    "Team",
    "Player",
    "Venue",
    "Competition",
    "Season",
    "Match",
    "Lineup",
    "MatchEvent",
    "Innings",
    "Delivery",
    "PlayerMatchStats",
    "TeamMatchStats",
    "PlayerVenueStats",
    "PlayerCompetitionStats",
    "PlayerOpponentStats",
    "PlayerBowlerMatchup",
    "FootballEvent",
    "FootballPlayerStats",
    "FootballTeamStats",
    "WeatherSnapshot",
    "NewsArticle",
    "NewsEntity",
    "OddsSnapshot",
    "MarketMovement",
    "ModelVersion",
    "ModelMetric",
    "Prediction",
    "PredictionFeature",
    "PredictionResult",
    "BacktestRun",
]
