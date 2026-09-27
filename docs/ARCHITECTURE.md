# Architecture

## Design principles

1. **Provider abstraction, always.** The frontend and API never talk to an
   external sports/news/weather/market provider directly. Everything goes
   through an interface (`data/ingestion/providers/*`) so a provider can be
   swapped, mocked for tests, or added later without touching consumers.
2. **Leakage safety is structural, not a code-review habit.** Every feature
   row carries a `feature_timestamp`. The feature-store read path
   (`data/validation/leakage.py`) rejects any feature whose timestamp is
   after the prediction timestamp it would be used for. Backtests use
   chronological splits, never random shuffling.
3. **Every prediction is an audited artifact.** A prediction is never just
   a number returned to a client — it is a row in `predictions` /
   `prediction_features` / `prediction_results`, tagged with a
   `model_version` and `feature_version`/`data_version`, kept whether it
   turns out right or wrong.
4. **Mock and production data never mix.** Mock providers set
   `data_quality = "mock"` on everything they produce, which propagates
   into the `data_quality` field on predictions and is surfaced in the UI.
5. **Modules over a monolith of convenience.** Code is organized by
   bounded context (matches, players, predictions, news, markets, live)
   even where, today, it runs inside one FastAPI process. The `services/`
   directory documents where each context would be extracted into its own
   deployable when load or team boundaries justify it.

## Current system shape

```
                     ┌──────────────────┐
                     │   apps/web        │  Next.js dashboard
                     └────────┬─────────┘
                              │ HTTPS / WSS
                     ┌────────▼─────────┐
                     │  backend/app      │  FastAPI: auth, matches, players,
                     │  (single service) │  teams, predictions, news, markets,
                     └───┬─────────┬────┘  websocket
                         │         │
              ┌──────────▼──┐   ┌─▼───────────────┐
              │  database/   │   │  ml/             │
              │  (Postgres   │   │  cricket, football,
              │  via SQLA)   │   │  calibration,     │
              └──────────────┘   │  backtesting      │
                                  └────────┬──────────┘
                                           │
                                  ┌────────▼──────────┐
                                  │ data/ingestion/     │
                                  │ providers (mock today,
                                  │ real provider slot   │
                                  │ documented)          │
                                  └──────────────────────┘
```

`backend/app` currently hosts what the spec calls out as separate
`services/` (live-score-service, prediction-service, news-service,
market-service, notification-service) as in-process modules behind the same
interfaces those services would expose. This keeps the system runnable and
testable end-to-end without standing up a message broker and five
deployables before there is real load or team ownership requiring the
split. The module boundaries mirror the eventual service boundaries
exactly, so extraction is a deployment change, not a rewrite — each
`services/*` directory contains a README pointing at the backend module it
would take over.

## Scope and roadmap

The full master specification for this project is extremely broad — a
production platform spanning two sports, live ingestion, ML, news NLP,
market intelligence, a native mobile app, and a full observability/security
stack. Building all of it to production depth is a multi-quarter effort.
This repository is being built incrementally and honestly against that
spec. Current status:

### Implemented (real, working, tested)
- Normalized Postgres schema for the full data model in the spec.
- Provider interfaces for cricket, football, news, weather, and market
  data, each with a mock development implementation.
- Data validation: duplicate detection, timestamp sanity checks, leakage
  guard.
- Cricket: feature engineering, Monte Carlo innings simulation, a
  calibrated win-probability ensemble (logistic regression blended with
  simulation output), player run/wicket projection scaffolding.
- Football: Dixon-Coles expected-goals model, Monte Carlo match simulation
  for home/draw/away and scorelines.
- Calibration metrics (Brier score, log loss, reliability buckets) and a
  temporal backtesting framework, with results persisted to
  `backtest_runs`.
- FastAPI backend: JWT auth, rate limiting, CORS, REST endpoints for
  matches/players/teams/predictions, a WebSocket live channel that
  recomputes predictions on synthetic match events and logs a
  prediction-change audit trail with a plain-language "why" explanation
  generated from the actual feature deltas (never invented).
- Next.js dashboard: Home, Cricket Match Centre, Football Match Centre,
  Player page, with a shared `ProbabilityCard` component that enforces the
  spec's display rule (probability + timestamp + model version + data
  quality, never a bare number).
- Test suites for leakage, duplicate data, probability bounds, auth, and
  the predictions API.

### Explicitly not built yet (tracked, not hidden)
- **Real external providers.** No live cricket/football/news/weather/odds
  vendor integration is wired in — that requires a licensed API key the
  operator must supply (see `docs/DATA_SOURCES.md`). The provider
  interface is ready to receive one.
- **News NLP pipeline** (entity extraction, injury/selection
  classification, confirmed/reported/unverified tagging) — the schema and
  ingestion interface exist; the classifier is not implemented.
- **Market intelligence beyond schema + separation guarantee** — odds
  storage and the model-vs-market divergence calculation are implemented;
  a real odds feed is not connected.
- **Mobile app** (`apps/mobile`) — placeholder only.
- **Microservice extraction** — see above; documented, not yet split.
- **Full observability stack** (metrics/tracing backend, dashboards) —
  structured logging and `/health` endpoints exist; Prometheus/Grafana-style
  aggregation does not.
- **In-app AI assistant** — not implemented.
- **XGBoost/LightGBM/Bayesian/time-series model variants** — the ensemble
  currently uses logistic regression + Monte Carlo + Dixon-Coles Poisson,
  chosen because they are honest, interpretable baselines that don't
  require large real datasets to validate; heavier models are a natural
  next step once backtesting shows they add calibrated skill over the
  baseline (see `docs/MODEL_LIMITATIONS.md`).

Anything marked "not built yet" is absent, not faked — there is no
placeholder that pretends to be a real classifier or a real odds feed.

## Module reference

| Path | Responsibility |
|---|---|
| `backend/app/authentication` | user model, password hashing, JWT issuance/refresh |
| `backend/app/matches` | match/fixture CRUD + read endpoints |
| `backend/app/players` | player profile, stats, matchup endpoints |
| `backend/app/teams` | team profile, form, head-to-head endpoints |
| `backend/app/predictions` | prediction request/response, audit endpoints |
| `backend/app/news` | news ingestion/read endpoints (schema-ready, classifier pending) |
| `backend/app/markets` | odds storage + divergence endpoints (schema-ready, feed pending) |
| `backend/app/websocket` | live connection manager, event-driven recompute |
| `data/ingestion/providers` | `CricketDataProvider`, `FootballDataProvider`, `NewsDataProvider`, `WeatherDataProvider`, `MarketDataProvider` interfaces + mocks |
| `data/normalization` | raw provider payload → normalized DB rows |
| `data/validation` | leakage guard, duplicate detection, schema/timestamp validation |
| `ml/cricket`, `ml/football` | feature engineering, models, Monte Carlo |
| `ml/calibration` | Brier score, log loss, reliability diagrams |
| `ml/backtesting` | temporal split runner, metrics persistence |
| `database` | SQLAlchemy models, Alembic migrations, mock seed data |
| `apps/web` | Next.js dashboard |
