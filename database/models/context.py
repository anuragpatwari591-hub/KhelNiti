"""Contextual signal tables: weather, news, and market/odds data.

Market data is intentionally kept in its own tables (`odds_snapshots`,
`market_movements`) rather than folded into `prediction_features`, so that
experiments can measure whether market information improves the
independent model rather than silently depending on it (see
docs/ML.md#market-data-separation).
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, TimestampMixin
from database.models.enums import DataQuality, NewsCategory, NewsVerificationStatus, Sport


class WeatherSnapshot(Base, TimestampMixin):
    __tablename__ = "weather_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    humidity_pct: Mapped[float | None] = mapped_column(Float)
    wind_speed_kph: Mapped[float | None] = mapped_column(Float)
    precipitation_mm: Mapped[float | None] = mapped_column(Float)
    condition: Mapped[str | None] = mapped_column(String(50))
    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)


class NewsArticle(Base, TimestampMixin):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(4000))
    category: Mapped[NewsCategory] = mapped_column(default=NewsCategory.OTHER, nullable=False, index=True)
    verification_status: Mapped[NewsVerificationStatus] = mapped_column(
        default=NewsVerificationStatus.UNVERIFIED, nullable=False, index=True
    )
    sport: Mapped[Sport | None] = mapped_column()
    reliability_score: Mapped[float | None] = mapped_column(Float)
    dedupe_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class NewsEntity(Base, TimestampMixin):
    """Links a news article to the player/team/competition it concerns.

    Only entities linked from a `confirmed` or corroborated `reported`
    article should ever be allowed to influence a prediction's features —
    the feature layer checks `verification_status` before consuming this.
    """

    __tablename__ = "news_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # player | team | competition
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"))


class OddsSnapshot(Base, TimestampMixin):
    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. match_winner, total_runs
    selection: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Team A", "Over 2.5"
    price: Mapped[float] = mapped_column(Float, nullable=False)  # decimal odds
    implied_probability: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class MarketMovement(Base, TimestampMixin):
    """Derived opening-vs-current price movement and model-vs-market
    divergence, computed periodically from `odds_snapshots` — never treated
    as a model feature by default (see docs/ML.md).
    """

    __tablename__ = "market_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    selection: Mapped[str] = mapped_column(String(100), nullable=False)
    opening_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    market_implied_probability: Mapped[float] = mapped_column(Float, nullable=False)
    model_probability: Mapped[float | None] = mapped_column(Float)
    divergence: Mapped[float | None] = mapped_column(Float)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("match_id", "market", "selection", "computed_at", name="uq_market_movement"),
    )
