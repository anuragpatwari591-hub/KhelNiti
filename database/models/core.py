"""Core reference entities: users, teams, players, venues, competitions,
seasons, matches, lineups, and the sport-agnostic match event timeline.
"""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, TimestampMixin
from database.models.enums import DataQuality, MatchStatus, Sport, UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Team(Base, TimestampMixin):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(Enum(Sport, name="sport"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (UniqueConstraint("sport", "name", name="uq_team_sport_name"),)


class Player(Base, TimestampMixin):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(Enum(Sport, name="sport"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    # Cricket-specific, nullable for football players.
    batting_style: Mapped[str | None] = mapped_column(String(50))
    bowling_style: Mapped[str | None] = mapped_column(String(50))
    # Football-specific, nullable for cricket players.
    primary_position: Mapped[str | None] = mapped_column(String(50))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(Enum(Sport, name="sport"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    tier: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (UniqueConstraint("sport", "name", name="uq_competition_sport_name"),)


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)

    competition: Mapped["Competition"] = relationship()

    __table_args__ = (UniqueConstraint("competition_id", "name", name="uq_season_competition_name"),)


class Match(Base, TimestampMixin):
    """A single fixture, cricket or football.

    `external_ref` + `data_source` uniquely identify the same match from a
    given provider, so re-ingestion is idempotent and duplicate-detection
    (see data/validation) has a clean key to check against.
    """

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[Sport] = mapped_column(Enum(Sport, name="sport"), nullable=False, index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), index=True)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"), index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)

    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status"), default=MatchStatus.SCHEDULED, nullable=False, index=True
    )
    result_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Cricket-only, nullable for football.
    toss_winner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    toss_decision: Mapped[str | None] = mapped_column(String(20))

    data_source: Mapped[str] = mapped_column(String(100), nullable=False)
    data_quality: Mapped[DataQuality] = mapped_column(
        Enum(DataQuality, name="data_quality"), default=DataQuality.MOCK, nullable=False
    )
    external_ref: Mapped[str] = mapped_column(String(255), nullable=False)

    competition: Mapped["Competition"] = relationship()
    venue: Mapped["Venue | None"] = relationship()
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id])

    __table_args__ = (UniqueConstraint("data_source", "external_ref", name="uq_match_source_ref"),)


class Lineup(Base, TimestampMixin):
    """Playing XI / starting lineup entry, shared shape across both sports."""

    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    is_playing_xi: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_wicketkeeper: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    batting_order: Mapped[int | None] = mapped_column(Integer)  # cricket
    formation_position: Mapped[str | None] = mapped_column(String(20))  # football, e.g. "RB", "CM"

    __table_args__ = (UniqueConstraint("match_id", "player_id", name="uq_lineup_match_player"),)


class MatchEvent(Base, TimestampMixin):
    """Sport-agnostic timeline of notable in-match events.

    This is the trigger source for the live prediction engine: each row
    written here should cause `services/live` to recompute and broadcast an
    updated prediction (see data/validation and the websocket module).
    """

    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    sport: Mapped[Sport] = mapped_column(Enum(Sport, name="sport"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
