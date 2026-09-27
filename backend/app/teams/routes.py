from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.database import get_db
from backend.app.matches.schemas import MatchOut
from backend.app.matches.routes import _to_match_out
from backend.app.teams.schemas import TeamOut
from database.models.core import Match, Team

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team


@router.get("/{team_id}/matches", response_model=list[MatchOut])
def get_team_matches(team_id: int, limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    team = db.get(Team, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    stmt = (
        select(Match)
        .where(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
        .options(
            selectinload(Match.home_team), selectinload(Match.away_team),
            selectinload(Match.venue), selectinload(Match.competition),
        )
        .order_by(Match.scheduled_start.desc())
        .limit(limit)
    )
    matches = db.scalars(stmt).all()
    return [_to_match_out(m) for m in matches]
