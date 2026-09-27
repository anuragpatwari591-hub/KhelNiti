from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.database import get_db
from backend.app.matches.schemas import MatchOut, TeamSummary
from database.models.core import Match

router = APIRouter(prefix="/matches", tags=["matches"])


def _to_match_out(match: Match) -> MatchOut:
    return MatchOut(
        id=match.id,
        sport=match.sport.value,
        status=match.status.value,
        scheduled_start=match.scheduled_start,
        home_team=TeamSummary.model_validate(match.home_team),
        away_team=TeamSummary.model_validate(match.away_team),
        venue_name=match.venue.name if match.venue else None,
        competition_name=match.competition.name,
        data_quality=match.data_quality.value,
        result_summary=match.result_summary,
    )


@router.get("", response_model=list[MatchOut])
def list_matches(
    sport: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Match).options(
        selectinload(Match.home_team), selectinload(Match.away_team),
        selectinload(Match.venue), selectinload(Match.competition),
    ).order_by(Match.scheduled_start.desc()).limit(limit)
    if sport:
        stmt = stmt.where(Match.sport == sport)
    if status_filter:
        stmt = stmt.where(Match.status == status_filter)
    matches = db.scalars(stmt).all()
    return [_to_match_out(m) for m in matches]


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = db.get(
        Match, match_id,
        options=[selectinload(Match.home_team), selectinload(Match.away_team),
                 selectinload(Match.venue), selectinload(Match.competition)],
    )
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return _to_match_out(match)
