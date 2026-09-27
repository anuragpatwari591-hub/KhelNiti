# API Reference

Base URL: `http://localhost:8000` (local). Interactive OpenAPI docs at
`/docs`, raw schema at `/openapi.json`.

## Authentication

JWT bearer tokens. `POST /auth/login` returns `access_token`; send it as
`Authorization: Bearer <token>` on any endpoint marked "auth required".

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Create a user (bcrypt-hashed password) |
| POST | `/auth/login` | — | Exchange email/password for a JWT |
| GET | `/auth/me` | required | Current user |

## Matches / Teams / Players (read)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/matches` | — | List matches (`?sport=`, `?status=`, `?limit=`) |
| GET | `/matches/{id}` | — | Match detail |
| GET | `/teams/{id}` | — | Team detail |
| GET | `/teams/{id}/matches` | — | A team's recent matches |
| GET | `/players/{id}` | — | Player detail |
| GET | `/players/{id}/match-stats` | — | A player's per-match stats |

## Predictions

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/matches/{id}/predictions/win-probability` | required | Computes a fresh cricket win-probability prediction from the match's current deliveries and persists it (`predictions` + `prediction_features`) |
| GET | `/matches/{id}/predictions` | — | Prediction history for a match (the audit trail) |
| GET | `/predictions/{id}/features` | — | The exact feature snapshot behind one prediction |
| GET | `/matches/{id}/predictions/change` | — | "Why did the prediction change?" — diff between the two most recent predictions |

Every `PredictionOut` includes `prediction_time`, `model_name`,
`model_version`, and `data_quality` alongside `probabilities` — the API
cannot return a probability without that context, matching the spec's
display rule.

## Live events / WebSocket

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/matches/{id}/events` | required | Records a match event; if it's a trigger event (wicket, boundary, over_complete, innings_break, toss for cricket), recomputes the prediction and broadcasts the update |
| WS | `/ws/live/{id}` | — | Subscribes to live prediction updates for a match |

A `POST /matches/{id}/events` call and a connected `/ws/live/{id}` client
demonstrate the same event → recompute → broadcast → audit pipeline
described in `docs/ARCHITECTURE.md`.

## News / Markets (read)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/news` | — | News articles (`?category=`, `?verification_status=`) |
| GET | `/matches/{id}/markets/odds` | — | Raw odds snapshots |
| GET | `/matches/{id}/markets/movements` | — | Model-vs-market divergence |

## System

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |

## Rate limiting

Every route is subject to the default limiter
(`API_RATE_LIMIT_PER_MINUTE`, default 120/minute per client IP —
`backend/app/core/rate_limit.py`). Exceeding it returns `429`.

## Errors

Errors are returned as `{"detail": "..."}` with a standard HTTP status:
`401` (bad/missing credentials), `403` (insufficient role), `404` (not
found), `409` (duplicate registration), `422` (insufficient live data for
a prediction — e.g. no deliveries recorded yet), `503` (no active trained
model — run the relevant `ml/training/*` script first).
