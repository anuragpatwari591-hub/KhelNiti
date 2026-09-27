"""In-process WebSocket connection registry, keyed by match id.

A single-process in-memory manager is sufficient for one backend instance;
scaling to multiple instances would need a shared pub/sub (Redis, etc.) —
noted in docs/ARCHITECTURE.md as a documented-not-yet-built piece.
"""
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, match_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[match_id].append(websocket)

    def disconnect(self, match_id: int, websocket: WebSocket) -> None:
        if websocket in self._connections[match_id]:
            self._connections[match_id].remove(websocket)

    async def broadcast(self, match_id: int, message: dict) -> None:
        stale = []
        for connection in self._connections[match_id]:
            try:
                await connection.send_json(message)
            except Exception:
                stale.append(connection)
        for connection in stale:
            self.disconnect(match_id, connection)


manager = ConnectionManager()
