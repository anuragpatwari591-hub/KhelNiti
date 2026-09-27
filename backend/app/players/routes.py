from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.players.schemas import PlayerMatchStatsOut, PlayerOut
from database.models.core import Player
from database.models.cricket import PlayerMatchStats

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")
    return player


@router.get("/{player_id}/match-stats", response_model=list[PlayerMatchStatsOut])
def get_player_match_stats(player_id: int, limit: int = Query(default=10, le=50), db: Session = Depends(get_db)):
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found")

    stmt = (
        select(PlayerMatchStats)
        .where(PlayerMatchStats.player_id == player_id)
        .order_by(PlayerMatchStats.id.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()
