# Security

## Authentication & authorization

- Passwords are hashed with bcrypt via passlib (`backend/app/core/security.py`)
  — never stored or logged in plain text.
- Sessions are stateless JWTs (`python-jose`, HS256, `JWT_SECRET_KEY`),
  with a configurable expiry (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
- `require_admin` (`backend/app/authentication/deps.py`) gates
  admin-only actions by `User.role`.
- Prediction-triggering and event-recording endpoints require a valid
  token; all read endpoints (matches, teams, players, news, market data)
  are intentionally public — there's no user data behind them.

## Secrets

- `.env` is gitignored; only `.env.example` (with placeholder values) is
  committed. **Never commit a populated `.env`.**
- `JWT_SECRET_KEY` and `APP_SECRET_KEY` default to an obviously-fake
  development value (`dev-only-insecure-key-change-me`) — this must be
  overridden with a real random value before any non-local deployment.
  `backend/app/config.py` does not enforce this at startup today; treat
  that as a deployment-checklist item, not something the code guarantees.
- Provider API keys (`.env.example`'s `*_API_KEY` variables) are read only
  by the provider implementation that needs them and are never logged.

## API hardening

- **Rate limiting**: `slowapi`, default `API_RATE_LIMIT_PER_MINUTE`
  (120/minute per client IP) applied globally (`backend/app/core/rate_limit.py`).
- **CORS**: restricted to `CORS_ALLOWED_ORIGINS` (comma-separated), not a
  wildcard, in `backend/app/main.py`.
- **Input validation**: every request body is a Pydantic model
  (`backend/app/*/schemas.py`) — invalid types/missing fields are
  rejected by FastAPI before a handler runs.
- **SQL injection**: all database access goes through SQLAlchemy's ORM
  query builder (`select(...)`) — no raw string-interpolated SQL anywhere
  in the codebase.

## Database

- The app connects as a dedicated `khelniti` role, not a superuser
  (`docker-compose.yml`, `.env.example`).
- Migrations are explicit and reviewed (`alembic revision --autogenerate`
  followed by a manual read of the generated file) rather than
  auto-applied from ORM model state in production.

## Audit logging

- Every prediction, its full feature snapshot, and (once a match
  resolves) its actual outcome are persisted permanently
  (`predictions`, `prediction_features`, `prediction_results`) — this is
  itself an audit log of every probability the system ever surfaced.
- Application-level request/action audit logging (who changed what,
  admin action logs) beyond the prediction trail is not yet implemented —
  see `docs/ARCHITECTURE.md#roadmap`.

## Known gaps (tracked, not hidden)

- No refresh-token rotation — access tokens simply expire
  (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`); a refresh-token flow is not yet
  implemented despite `.env.example` reserving
  `JWT_REFRESH_TOKEN_EXPIRE_DAYS` for it.
- No email verification on registration.
- No account lockout / brute-force login throttling beyond the general
  API rate limit.
- `JWT_SECRET_KEY`/`APP_SECRET_KEY` defaults are not validated at startup
  to differ from the development placeholder in production mode.

## Reporting a vulnerability

This is a development-stage project; if you find a security issue, open
an issue describing it (avoid posting exploit details in a public issue
if the deployment in question is live) or contact the maintainers
directly.
