"""Mock weather data provider — development/test only."""
import random
from datetime import datetime, timezone

from data.ingestion.providers.base import WeatherDataProvider
from data.ingestion.providers.types import WeatherPayload
from database.models.enums import DataQuality


class MockWeatherProvider(WeatherDataProvider):
    def __init__(self, seed: int = 5):
        self._seed = seed

    @property
    def provider_name(self) -> str:
        return "mock-weather"

    def get_current_weather(self, venue_external_ref: str) -> WeatherPayload | None:
        rng = random.Random(f"{self._seed}:{venue_external_ref}")
        return WeatherPayload(
            venue_external_ref=venue_external_ref,
            captured_at=datetime.now(timezone.utc),
            temperature_c=round(rng.uniform(15, 34), 1),
            humidity_pct=round(rng.uniform(30, 90), 1),
            wind_speed_kph=round(rng.uniform(0, 25), 1),
            precipitation_mm=round(max(0.0, rng.gauss(0.5, 1.0)), 1),
            condition=rng.choice(["clear", "partly_cloudy", "overcast", "light_rain"]),
            data_quality=DataQuality.MOCK,
        )
