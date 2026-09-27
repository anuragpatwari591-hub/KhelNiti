"""Raw football provider payloads -> normalized database rows."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from data.ingestion.providers.types import FootballEventPayload, MatchSummaryPayload
from data.normalization.common import get_or_create_competition, get_or_create_player, get_or_create_team, get_or_create_venue
from data.validation.exceptions import DuplicateDataError
from data.validation.schema_checks import validate_football_event
from database.models.core import Match, MatchEvent
from database.models.enums import MatchStatus, Sport
from database.models.football import FootballEvent

_STATUS_MAP = {
    "scheduled": MatchStatus.SCHEDULED,
    "live": MatchStatus.LIVE,
    "completed": MatchStatus.COMPLETED,
    "abandoned": MatchStatus.ABANDONED,
    "postponed": MatchStatus.POSTPONED,
}

_MATCH_EVENT_TYPES = {"goal", "red_card", "penalty"}


def ingest_football_match(
    session: Session,
    data_source: str,
    match_summary: MatchSummaryPayload,
    events: list[FootballEventPayload],
) -> Match:
    existing = session.scalar(
        select(Match).where(Match.data_source == data_source, Match.external_ref == match_summary.external_ref)
    )
    if existing is not None:
        raise DuplicateDataError(
            f"Match {data_source}:{match_summary.external_ref} has already been ingested (id={existing.id})"
        )

    home_team = get_or_create_team(session, Sport.FOOTBALL, match_summary.home_team_name)
    away_team = get_or_create_team(session, Sport.FOOTBALL, match_summary.away_team_name)
    venue = get_or_create_venue(session, match_summary.venue_name) if match_summary.venue_name else None
    competition = get_or_create_competition(session, Sport.FOOTBALL, match_summary.competition_name)

    match = Match(
        sport=Sport.FOOTBALL,
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

    team_by_name = {match_summary.home_team_name: home_team, match_summary.away_team_name: away_team}

    for e in events:
        validate_football_event(e, match_summary.scheduled_start)
        team = team_by_name[e.team_name]
        player = get_or_create_player(session, Sport.FOOTBALL, e.player_name) if e.player_name else None
        related_player = (
            get_or_create_player(session, Sport.FOOTBALL, e.related_player_name) if e.related_player_name else None
        )

        session.add(
            FootballEvent(
                match_id=match.id,
                event_type=e.event_type,
                minute=e.minute,
                added_time=e.added_time,
                team_id=team.id,
                player_id=player.id if player else None,
                related_player_id=related_player.id if related_player else None,
                shot_x=e.shot_x,
                shot_y=e.shot_y,
                event_time=e.event_time,
            )
        )

        if e.event_type in _MATCH_EVENT_TYPES:
            session.add(
                MatchEvent(
                    match_id=match.id,
                    sport=Sport.FOOTBALL,
                    event_type=e.event_type,
                    event_time=e.event_time,
                    team_id=team.id,
                    player_id=player.id if player else None,
                    payload={"minute": e.minute},
                )
            )

    session.flush()
    return match
