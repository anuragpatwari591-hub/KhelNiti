"""Raw cricket provider payloads -> normalized database rows.

Enforces duplicate-match detection, delivery ordering, and per-delivery
sanity checks (data/validation) before anything is written.
"""
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from data.ingestion.providers.types import DeliveryPayload, MatchSummaryPayload
from data.normalization.common import get_or_create_competition, get_or_create_team, get_or_create_venue
from data.validation.exceptions import DuplicateDataError
from data.validation.schema_checks import validate_delivery, validate_delivery_sequence_monotonic
from database.models.core import Match
from database.models.cricket import Delivery, Innings
from database.models.enums import DataQuality, MatchStatus, Sport

_STATUS_MAP = {
    "scheduled": MatchStatus.SCHEDULED,
    "live": MatchStatus.LIVE,
    "completed": MatchStatus.COMPLETED,
    "abandoned": MatchStatus.ABANDONED,
    "postponed": MatchStatus.POSTPONED,
}


def ingest_cricket_match(
    session: Session,
    data_source: str,
    match_summary: MatchSummaryPayload,
    deliveries: list[DeliveryPayload],
) -> Match:
    existing = session.scalar(
        select(Match).where(Match.data_source == data_source, Match.external_ref == match_summary.external_ref)
    )
    if existing is not None:
        raise DuplicateDataError(
            f"Match {data_source}:{match_summary.external_ref} has already been ingested (id={existing.id})"
        )

    home_team = get_or_create_team(session, Sport.CRICKET, match_summary.home_team_name)
    away_team = get_or_create_team(session, Sport.CRICKET, match_summary.away_team_name)
    venue = get_or_create_venue(session, match_summary.venue_name) if match_summary.venue_name else None
    competition = get_or_create_competition(session, Sport.CRICKET, match_summary.competition_name)

    match = Match(
        sport=Sport.CRICKET,
        competition_id=competition.id,
        venue_id=venue.id if venue else None,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        scheduled_start=match_summary.scheduled_start,
        status=_STATUS_MAP[match_summary.status],
        data_source=data_source,
        data_quality=match_summary.data_quality,
        external_ref=match_summary.external_ref,
    )
    session.add(match)
    session.flush()

    by_innings: dict[int, list[DeliveryPayload]] = defaultdict(list)
    for d in deliveries:
        by_innings[d.innings_number].append(d)

    for innings_number, innings_deliveries in sorted(by_innings.items()):
        validate_delivery_sequence_monotonic(innings_deliveries)
        for d in innings_deliveries:
            validate_delivery(d, match_summary.scheduled_start)

        batting_team = home_team if innings_number == 1 else away_team
        bowling_team = away_team if innings_number == 1 else home_team
        last = innings_deliveries[-1]
        total_runs = last.score_before_ball + last.runs_batter + last.runs_extras
        total_wickets = last.wickets_before_ball + (1 if last.is_wicket else 0)

        innings = Innings(
            match_id=match.id,
            innings_number=innings_number,
            batting_team_id=batting_team.id,
            bowling_team_id=bowling_team.id,
            total_runs=total_runs,
            total_wickets=total_wickets,
            total_overs_bowled=innings_deliveries[-1].over_number + 1,
            is_completed=match_summary.status == "completed",
        )
        session.add(innings)
        session.flush()

        player_cache: dict[str, int] = {}

        def player_id(name: str | None) -> int | None:
            if not name:
                return None
            if name not in player_cache:
                from data.normalization.common import get_or_create_player

                player_cache[name] = get_or_create_player(session, Sport.CRICKET, name).id
            return player_cache[name]

        for d in innings_deliveries:
            session.add(
                Delivery(
                    innings_id=innings.id,
                    sequence=d.sequence,
                    over_number=d.over_number,
                    ball_number=d.ball_number,
                    batter_id=player_id(d.batter_name),
                    bowler_id=player_id(d.bowler_name),
                    non_striker_id=player_id(d.non_striker_name),
                    runs_batter=d.runs_batter,
                    runs_extras=d.runs_extras,
                    extras_type=d.extras_type,
                    is_wicket=d.is_wicket,
                    dismissal_type=d.dismissal_type,
                    dismissed_player_id=player_id(d.dismissed_player_name),
                    is_boundary=d.runs_batter in (4, 6),
                    is_four=d.runs_batter == 4,
                    is_six=d.runs_batter == 6,
                    score_before_ball=d.score_before_ball,
                    wickets_before_ball=d.wickets_before_ball,
                    batting_position=None,
                    bowling_phase="powerplay" if d.over_number < 6 else ("middle" if d.over_number < 16 else "death"),
                    delivery_time=d.delivery_time,
                )
            )

    session.flush()
    return match
