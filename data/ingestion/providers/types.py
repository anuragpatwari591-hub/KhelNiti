"""Plain-data payload shapes returned by provider implementations.

These are intentionally provider-agnostic and pre-normalization: they use
`external_ref` strings rather than internal DB ids, because a provider has
no knowledge of KhelNiti's primary keys. `data/normalization` maps these
into ORM rows.
"""
from dataclasses import dataclass, field
from datetime import datetime

from database.models.enums import DataQuality


@dataclass(frozen=True)
class MatchSummaryPayload:
    external_ref: str
    sport: str
    competition_name: str
    home_team_name: str
    away_team_name: str
    venue_name: str | None
    scheduled_start: datetime
    status: str
    data_quality: DataQuality


@dataclass(frozen=True)
class DeliveryPayload:
    external_ref: str  # match external ref
    innings_number: int
    sequence: int
    over_number: int
    ball_number: int
    batter_name: str
    bowler_name: str
    non_striker_name: str | None
    runs_batter: int
    runs_extras: int
    extras_type: str | None
    is_wicket: bool
    dismissal_type: str | None
    dismissed_player_name: str | None
    score_before_ball: int
    wickets_before_ball: int
    delivery_time: datetime
    data_quality: DataQuality


@dataclass(frozen=True)
class FootballEventPayload:
    external_ref: str  # match external ref
    event_type: str
    minute: int
    added_time: int | None
    team_name: str
    player_name: str | None
    related_player_name: str | None
    shot_x: float | None
    shot_y: float | None
    event_time: datetime
    data_quality: DataQuality


@dataclass(frozen=True)
class NewsArticlePayload:
    source: str
    url: str | None
    published_at: datetime
    title: str
    summary: str | None
    category: str
    verification_status: str
    sport: str | None
    entities: list[str] = field(default_factory=list)  # team/player names mentioned
    data_quality: DataQuality = DataQuality.MOCK


@dataclass(frozen=True)
class WeatherPayload:
    venue_external_ref: str
    captured_at: datetime
    temperature_c: float | None
    humidity_pct: float | None
    wind_speed_kph: float | None
    precipitation_mm: float | None
    condition: str | None
    data_quality: DataQuality


@dataclass(frozen=True)
class OddsPayload:
    match_external_ref: str
    market: str
    selection: str
    price: float
    captured_at: datetime
    data_quality: DataQuality
