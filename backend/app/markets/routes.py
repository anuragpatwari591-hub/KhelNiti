from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.markets.schemas import MarketMovementOut, OddsSnapshotOut
from database.models.context import MarketMovement, OddsSnapshot

router = APIRouter(prefix="/matches/{match_id}/markets", tags=["markets"])


@router.get("/odds", response_model=list[OddsSnapshotOut])
def list_odds(match_id: int, db: Session = Depends(get_db)):
    stmt = select(OddsSnapshot).where(OddsSnapshot.match_id == match_id).order_by(OddsSnapshot.captured_at.desc())
    return db.scalars(stmt).all()


@router.get("/movements", response_model=list[MarketMovementOut])
def list_market_movements(match_id: int, db: Session = Depends(get_db)):
    """Model-vs-market divergence — computed separately from the
    independent model's own features (see docs/ML.md#market-data-separation).
    """
    stmt = (
        select(MarketMovement).where(MarketMovement.match_id == match_id).order_by(MarketMovement.computed_at.desc())
    )
    return db.scalars(stmt).all()
