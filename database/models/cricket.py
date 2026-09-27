"""Cricket-specific delivery-level data model and derived aggregate tables."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base, TimestampMixin
from database.models.enums import DataQuality


class Innings(Base, TimestampMixin):
    __tablename__ = "innings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    innings_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batting_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    bowling_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    target: Mapped[int | None] = mapped_column(Integer)
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_wickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_overs_bowled: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("match_id", "innings_number", name="uq_innings_match_number"),)


class Delivery(Base, TimestampMixin):
    """One ball. `sequence` is the monotonic over*6+ball_in_over ordering key
    within an innings, used for leakage-safe "as of this ball" feature reads.
    """

    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    over_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ball_number: Mapped[int] = mapped_column(Integer, nullable=False)

    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    bowler_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    non_striker_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    runs_batter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runs_extras: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extras_type: Mapped[str | None] = mapped_column(String(20))  # wide, no_ball, bye, leg_bye, penalty

    is_wicket: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dismissal_type: Mapped[str | None] = mapped_column(String(30))
    dismissed_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))

    is_boundary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_four: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_six: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    score_before_ball: Mapped[int] = mapped_column(Integer, nullable=False)
    wickets_before_ball: Mapped[int] = mapped_column(Integer, nullable=False)
    current_run_rate: Mapped[float | None] = mapped_column(Float)
    required_run_rate: Mapped[float | None] = mapped_column(Float)
    batting_position: Mapped[int | None] = mapped_column(Integer)
    bowling_phase: Mapped[str | None] = mapped_column(String(20))  # powerplay, middle, death

    delivery_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("innings_id", "sequence", name="uq_delivery_innings_sequence"),)


class PlayerMatchStats(Base, TimestampMixin):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    runs_scored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sixes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    strike_rate: Mapped[float | None] = mapped_column(Float)
    dismissal_type: Mapped[str | None] = mapped_column(String(30))

    overs_bowled: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wickets_taken: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    economy_rate: Mapped[float | None] = mapped_column(Float)

    catches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stumpings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    run_outs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    powerplay_runs: Mapped[int | None] = mapped_column(Integer)
    middle_overs_runs: Mapped[int | None] = mapped_column(Integer)
    death_overs_runs: Mapped[int | None] = mapped_column(Integer)

    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)

    __table_args__ = (UniqueConstraint("match_id", "player_id", name="uq_pms_match_player"),)


class TeamMatchStats(Base, TimestampMixin):
    __tablename__ = "team_match_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), nullable=False, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_wickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_overs: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    run_rate: Mapped[float | None] = mapped_column(Float)
    powerplay_runs: Mapped[int | None] = mapped_column(Integer)
    powerplay_wickets: Mapped[int | None] = mapped_column(Integer)
    middle_overs_runs: Mapped[int | None] = mapped_column(Integer)
    death_overs_runs: Mapped[int | None] = mapped_column(Integer)
    extras: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)

    __table_args__ = (UniqueConstraint("match_id", "team_id", name="uq_tms_match_team"),)


class _AggregateStatsMixin(TimestampMixin):
    """Shared shape for the cross-sport aggregate/matchup tables.

    `sample_size` is the number of underlying matches/deliveries the
    aggregate is built from — the ML layer uses it to shrink small-sample
    aggregates toward a population prior rather than trusting them at face
    value (see ml/feature_engineering/shrinkage.py).
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_quality: Mapped[DataQuality] = mapped_column(default=DataQuality.MOCK, nullable=False)


class PlayerVenueStats(Base, _AggregateStatsMixin):
    __tablename__ = "player_venue_stats"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("player_id", "venue_id", name="uq_pvs_player_venue"),)


class PlayerCompetitionStats(Base, _AggregateStatsMixin):
    __tablename__ = "player_competition_stats"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("player_id", "competition_id", name="uq_pcs_player_competition"),)


class PlayerOpponentStats(Base, _AggregateStatsMixin):
    __tablename__ = "player_opponent_stats"

    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    opponent_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("player_id", "opponent_team_id", name="uq_pos_player_opponent"),)


class PlayerBowlerMatchup(Base, _AggregateStatsMixin):
    """Batter-vs-bowler head-to-head aggregate, cricket only."""

    __tablename__ = "player_bowler_matchups"

    batter_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    bowler_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("batter_id", "bowler_id", name="uq_matchup_batter_bowler"),)
