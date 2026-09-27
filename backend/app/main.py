"""FastAPI application entrypoint.

Run: uvicorn backend.app.main:app --reload --port 8000 (from the repo root).
"""
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.authentication.routes import router as auth_router
from backend.app.config import get_settings
from backend.app.core.rate_limit import limiter
from backend.app.markets.routes import router as markets_router
from backend.app.matches.routes import router as matches_router
from backend.app.news.routes import router as news_router
from backend.app.players.routes import router as players_router
from backend.app.predictions.routes import router as predictions_router
from backend.app.teams.routes import router as teams_router
from backend.app.websocket.routes import router as websocket_router

settings = get_settings()

app = FastAPI(
    title="KhelNiti API",
    description="Cricket & football sports intelligence platform API.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(matches_router)
app.include_router(teams_router)
app.include_router(players_router)
app.include_router(predictions_router)
app.include_router(news_router)
app.include_router(markets_router)
app.include_router(websocket_router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat(), "env": settings.app_env}
