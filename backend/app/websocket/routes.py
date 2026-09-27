from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.authentication.deps import get_current_user
from backend.app.database import get_db
from backend.app.websocket.live_engine import explain_change, latest_two_predictions, process_match_event
from backend.app.websocket.manager import manager
from database.models.core import Match, MatchEvent, User

router = APIRouter(tags=["live"])


class MatchEventIn(BaseModel):
    event_type: str
    team_id: int | None = None
    player_id: int | None = None
    payload: dict = {}


@router.post("/matches/{match_id}/events", status_code=status.HTTP_201_CREATED)
async def record_match_event(
    match_id: int,
    payload: MatchEventIn,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Records a live match event and, if it's a trigger event, recomputes
    and broadcasts an updated prediction to any connected `/ws/live/{match_id}`
    clients — the event-driven core of the live engine.
    """
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")

    event = MatchEvent(
        match_id=match_id,
        sport=match.sport,
        event_type=payload.event_type,
        event_time=datetime.now(timezone.utc),
        team_id=payload.team_id,
        player_id=payload.player_id,
        payload=payload.payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    update = process_match_event(db, event)
    if update is not None:
        await manager.broadcast(match_id, update)

    return {"event_id": event.id, "event_type": event.event_type, "prediction_update": update}


@router.get("/matches/{match_id}/predictions/change")
def get_latest_prediction_change(match_id: int, db: Session = Depends(get_db)):
    """Standalone read of the same "why did it change" data the live
    WebSocket pushes — for clients that polled instead of subscribing.
    """
    current, previous = latest_two_predictions(db, match_id, "win_probability")
    if current is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No predictions recorded for this match yet")
    return explain_change(previous, current, event_type="unknown")


@router.websocket("/ws/live/{match_id}")
async def live_match_socket(websocket: WebSocket, match_id: int):
    await manager.connect(match_id, websocket)
    try:
        while True:
            # Clients don't need to send anything; this just detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)
