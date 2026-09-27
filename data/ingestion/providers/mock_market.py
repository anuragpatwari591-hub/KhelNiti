"""Mock market/odds data provider — development/test only.

Real market data requires a paid, licensed odds feed and is off by default
(`DATA_PROVIDER_MODE=mock`, `MARKET_DATA_PROVIDER=` empty in .env.example).
This mock exists only so the market-intelligence schema and
divergence-calculation code path can be exercised in tests.
"""
import random
from datetime import datetime, timezone

from data.ingestion.providers.base import MarketDataProvider
from data.ingestion.providers.types import OddsPayload
from database.models.enums import DataQuality


class MockMarketProvider(MarketDataProvider):
    def __init__(self, seed: int = 13):
        self._seed = seed

    @property
    def provider_name(self) -> str:
        return "mock-market"

    def get_odds(self, match_external_ref: str) -> list[OddsPayload]:
        rng = random.Random(f"{self._seed}:{match_external_ref}")
        now = datetime.now(timezone.utc)
        home_price = round(rng.uniform(1.5, 3.5), 2)
        away_price = round(rng.uniform(1.5, 3.5), 2)
        return [
            OddsPayload(
                match_external_ref=match_external_ref,
                market="match_winner",
                selection="home",
                price=home_price,
                captured_at=now,
                data_quality=DataQuality.MOCK,
            ),
            OddsPayload(
                match_external_ref=match_external_ref,
                market="match_winner",
                selection="away",
                price=away_price,
                captured_at=now,
                data_quality=DataQuality.MOCK,
            ),
        ]
