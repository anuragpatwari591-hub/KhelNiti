# KhelNiti — Cricket & Football Sports Intelligence Platform

KhelNiti is a scientifically structured sports intelligence system for
cricket and football. It ingests historical and live match data, engineers
leakage-safe features, trains and calibrates statistical/ML models, runs
Monte Carlo simulations, and serves explainable, auditable, uncertainty-aware
probability estimates through an API and web dashboard.

**KhelNiti never claims certainty about future sporting events.** Every
probability shown to a user carries a timestamp, a model version, and a
data-quality indicator, and every prediction is stored for later audit
regardless of outcome.

## Project status

This repository is under active, incremental development against the
[master build specification](docs/ARCHITECTURE.md#scope-and-roadmap). It is
**not** a finished, fully-featured production platform — see
[docs/MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md) and the roadmap in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for exactly what is implemented
today versus planned. What *is* implemented is real, working code with no
fabricated statistics: development/test environments use explicitly-labeled
mock data providers; nothing pretends to be production data unless a real,
licensed provider has been wired in.

## What's implemented today

- **Database**: normalized PostgreSQL schema (SQLAlchemy models + Alembic
  migration) covering users, teams, players, venues, competitions, matches,
  deliveries/innings (cricket), football events/stats, news, market/odds
  snapshots, and a full prediction-audit trail (`predictions`,
  `prediction_features`, `prediction_results`, `model_versions`,
  `model_metrics`, `backtest_runs`).
- **Provider abstraction**: `CricketDataProvider`, `FootballDataProvider`,
  `NewsDataProvider`, `WeatherDataProvider`, `MarketDataProvider` interfaces
  with mock, clearly-labeled development implementations. No real provider
  credentials are required to run the platform in `mock` mode.
- **Feature engineering with leakage guards**: every feature is timestamped
  and validated against `feature_timestamp <= prediction_timestamp` before
  it can be used in a prediction.
- **Cricket models**: a calibrated logistic-regression + Monte Carlo
  innings-simulation ensemble for live win probability and score
  projection, using genuine (if currently synthetic/mock-sourced) delivery
  data shaped exactly like the production schema.
- **Football models**: a Dixon-Coles style Poisson expected-goals model with
  Monte Carlo match simulation for home/draw/away and scoreline
  distributions.
- **Calibration & backtesting**: Brier score, log loss, and reliability
  bucket computation; a temporal (non-shuffled) backtesting framework that
  stores every run.
- **API**: FastAPI backend with JWT authentication, rate limiting, CORS,
  and REST endpoints for matches, players, teams, and predictions; a
  WebSocket live channel that recomputes and broadcasts predictions on
  match events and records a "why did the prediction change" audit trail.
- **Frontend**: a Next.js dashboard (Home, Cricket/Football Match Centre,
  Player page) that renders probabilities the way the spec requires —
  always with a timestamp, model version, and data-quality label, never as
  a bare number.
- **Tests**: pytest coverage for future-data leakage, duplicate
  match/delivery detection, probability bounds/sum-to-one, auth, and the
  predictions API.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for what is *not* yet built
(news NLP pipeline, live odds ingestion, mobile app, microservice split,
observability stack) and why.

## Repository layout

```
apps/
  web/              Next.js dashboard
  mobile/           placeholder — see docs/ARCHITECTURE.md roadmap
backend/
  app/              FastAPI app: api, authentication, matches, players,
                     teams, predictions, news, markets, websocket
ml/
  cricket/          feature engineering, Monte Carlo, win-probability model
  football/         expected-goals model, Monte Carlo
  feature_engineering/, training/, evaluation/, calibration/, backtesting/
data/
  ingestion/providers/   provider interfaces + mock implementations
  normalization/, validation/, pipelines/
database/
  models (SQLAlchemy), migrations/ (Alembic), seed/ (mock seed data)
services/           future microservice extraction points (documented, not
                     yet split out of backend/app — see ARCHITECTURE.md)
tests/              backend, ml, data, frontend test suites
docs/               architecture, database, ML, data sources, API,
                     deployment, backtesting, limitations, security,
                     contributing
scripts/            setup, migrate, seed, train
```

## Quickstart (local, no Docker)

Requirements: Python 3.11+, Node 20+, PostgreSQL 16 (or Docker for it).

```bash
cp .env.example .env

# --- Database ---
# Option A: run Postgres yourself and point DATABASE_URL at it.
# Option B: docker compose up -d postgres

# --- Backend ---
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed_mock_data   # optional: loads mock dev data, clearly labeled
uvicorn app.main:app --reload --port 8000

# --- Frontend (new terminal) ---
cd apps/web
npm install
npm run dev
```

Visit `http://localhost:3000`. The API is at `http://localhost:8000`
(`/docs` for the OpenAPI schema, `/health` for liveness).

## Quickstart (Docker)

```bash
cp .env.example .env
docker compose up --build
```

This starts Postgres, the backend API, and the web frontend.

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest ../tests/backend ../tests/data -v

cd ../ml
pip install -r ../backend/requirements.txt
pytest ../tests/ml -v
```

## Training / backtesting models

```bash
cd ml
python -m training.train_cricket_win_probability
python -m backtesting.run_backtest --sport cricket --model win_probability
```

Every trained model is versioned (`model_versions` table) and every
backtest run is persisted (`backtest_runs`) — nothing is thrown away, wins
or losses.

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design, module
  boundaries, roadmap and what's not built yet
- [DATABASE.md](docs/DATABASE.md) — full schema reference
- [ML.md](docs/ML.md) — models, features, ensembles, Monte Carlo
- [DATA_SOURCES.md](docs/DATA_SOURCES.md) — provider interfaces, licensing
  requirements, mock-vs-real data policy
- [API.md](docs/API.md) — endpoint reference
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — local/Docker/production deployment
- [BACKTESTING.md](docs/BACKTESTING.md) — methodology and how to run it
- [MODEL_LIMITATIONS.md](docs/MODEL_LIMITATIONS.md) — known weaknesses,
  assumptions, what NOT to trust these models for
- [SECURITY.md](docs/SECURITY.md) — auth, secrets, reporting
  vulnerabilities
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) — development workflow

## Core principles (non-negotiable)

1. No future-data leakage in features or training splits.
2. No fabricated data — mock data is always clearly labeled and never
   mixed with production data.
3. No fake accuracy claims — every metric shown is computed from stored,
   reproducible backtest runs.
4. No guaranteed predictions — everything is a probability estimate with
   uncertainty and a data-quality indicator.
5. Every prediction is timestamped, versioned, and auditable, including
   failed predictions.
6. Market odds are informative, never treated as ground truth, and stored
   separately from independent model features.

## License

MIT — see [LICENSE](LICENSE).
