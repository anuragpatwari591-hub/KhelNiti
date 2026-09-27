"""Provider abstraction interfaces.

Nothing outside `data/ingestion` and `data/normalization` should ever
import a concrete provider implementation directly — the rest of the
platform (API, ML, frontend) depends only on these interfaces, so a new
provider (or a real one replacing the mock) is a drop-in change.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from data.ingestion.providers.types import (
    DeliveryPayload,
    FootballEventPayload,
    MatchSummaryPayload,
    NewsArticlePayload,
    OddsPayload,
    WeatherPayload,
)


class CricketDataProvider(ABC):
    """Source of cricket match, innings, and delivery data."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_live_matches(self) -> list[MatchSummaryPayload]: ...

    @abstractmethod
    def get_deliveries(self, match_external_ref: str, since_sequence: int | None = None) -> list[DeliveryPayload]:
        """Return deliveries for a match, optionally only those after
        `since_sequence` (for incremental live polling)."""
        ...


class FootballDataProvider(ABC):
    """Source of football fixture and event data."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_live_matches(self) -> list[MatchSummaryPayload]: ...

    @abstractmethod
    def get_events(self, match_external_ref: str, since_minute: int | None = None) -> list[FootballEventPayload]: ...


class NewsDataProvider(ABC):
    """Source of sports news articles."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_latest_articles(self, since: datetime | None = None) -> list[NewsArticlePayload]: ...


class WeatherDataProvider(ABC):
    """Source of venue weather/conditions data."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_current_weather(self, venue_external_ref: str) -> WeatherPayload | None: ...


class MarketDataProvider(ABC):
    """Source of betting market / odds data.

    Only wire in a real implementation if you hold a valid data license for
    your jurisdiction — see docs/DATA_SOURCES.md. Market data must never be
    treated as ground truth and must be kept out of the independent model's
    feature set by default (docs/ML.md#market-data-separation).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def get_odds(self, match_external_ref: str) -> list[OddsPayload]: ...
