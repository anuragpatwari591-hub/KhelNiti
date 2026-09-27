"""Selects concrete provider implementations based on `DATA_PROVIDER_MODE`.

This is the ONLY place in the codebase that should import a concrete
provider class — everything else (API, ML, live engine) depends on the
`data/ingestion/providers/base.py` interfaces and calls
`get_cricket_provider()` / etc. Adding a real provider means writing a new
class implementing the relevant interface and adding one branch here.
"""
import os

from data.ingestion.providers.base import (
    CricketDataProvider,
    FootballDataProvider,
    MarketDataProvider,
    NewsDataProvider,
    WeatherDataProvider,
)
from data.ingestion.providers.mock_cricket import MockCricketProvider
from data.ingestion.providers.mock_football import MockFootballProvider
from data.ingestion.providers.mock_market import MockMarketProvider
from data.ingestion.providers.mock_news import MockNewsProvider
from data.ingestion.providers.mock_weather import MockWeatherProvider


class ProviderNotConfiguredError(RuntimeError):
    """Raised when DATA_PROVIDER_MODE=live but no real provider is registered."""


def _mode() -> str:
    return os.environ.get("DATA_PROVIDER_MODE", "mock").lower()


def get_cricket_provider() -> CricketDataProvider:
    if _mode() == "mock":
        return MockCricketProvider()
    raise ProviderNotConfiguredError(
        "DATA_PROVIDER_MODE=live but no real CricketDataProvider is registered. "
        "Implement one against your licensed vendor and add it here — see docs/DATA_SOURCES.md."
    )


def get_football_provider() -> FootballDataProvider:
    if _mode() == "mock":
        return MockFootballProvider()
    raise ProviderNotConfiguredError(
        "DATA_PROVIDER_MODE=live but no real FootballDataProvider is registered. "
        "Implement one against your licensed vendor and add it here — see docs/DATA_SOURCES.md."
    )


def get_news_provider() -> NewsDataProvider:
    if _mode() == "mock":
        return MockNewsProvider()
    raise ProviderNotConfiguredError(
        "DATA_PROVIDER_MODE=live but no real NewsDataProvider is registered — see docs/DATA_SOURCES.md."
    )


def get_weather_provider() -> WeatherDataProvider:
    if _mode() == "mock":
        return MockWeatherProvider()
    raise ProviderNotConfiguredError(
        "DATA_PROVIDER_MODE=live but no real WeatherDataProvider is registered — see docs/DATA_SOURCES.md."
    )


def get_market_provider() -> MarketDataProvider | None:
    """Returns None (market intelligence disabled) unless explicitly
    configured — market data requires a paid license, so it never turns on
    implicitly the way mock cricket/football data does.
    """
    if _mode() == "mock":
        return MockMarketProvider()
    if not os.environ.get("MARKET_DATA_PROVIDER"):
        return None
    raise ProviderNotConfiguredError(
        "MARKET_DATA_PROVIDER is set but no real MarketDataProvider is registered — see docs/DATA_SOURCES.md."
    )
