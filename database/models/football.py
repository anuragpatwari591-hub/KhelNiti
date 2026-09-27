"""Football-specific event and stats tables."""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import Base, TimestampMixin
from database.models.enums import DataQuality


class FootballEvent(Base, TimestampMixin):
    """Granular football event stream (goal, shot, card, substitution, ...).

    Distinct from the sport-agnostic `match_events` timeline (which drives
    the live-recompute trigger): this table holds the detailed per-event
    attributes (shot coordinates, related player for an assist/sub) that
    football-specific feature engineering needs.
    """

    __tablename__ = "football_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    added_time: Mapped[int | None] = mapped_column(Integer)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    related_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    shot_x: Mapped[float | None] = mapped_column(Float)
    shot_y: Mapped[float | None] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FootballPlayerStats(Base, TimestampMixin):
    __tablename__ = "football_player_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    minutes_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shots_on_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passes_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    key_passes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tackles: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interceptions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls_committed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls_suffered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)

    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)

    __table_args__ = (UniqueConstraint("match_id", "player_id", name="uq_fps_match_player"),)


class FootballTeamStats(Base, TimestampMixin):
    __tablename__ = "football_team_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    goals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shots_on_target: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    possession_pct: Mapped[float | None] = mapped_column(Float)
    passes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_accuracy: Mapped[float | None] = mapped_column(Float)
    corners: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fouls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    red_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    offsides: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    formation: Mapped[str | None] = mapped_column(String(20))

    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)

    __table_args__ = (UniqueConstraint("match_id", "team_id", name="uq_fts_match_team"),)
