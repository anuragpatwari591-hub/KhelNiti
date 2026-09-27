# Database

PostgreSQL 16, accessed through SQLAlchemy 2.0 ORM models in
`database/models/`, versioned with Alembic (`alembic.ini`,
`database/migrations/`). The schema is verified against a live Postgres
instance in CI-equivalent local testing — `alembic upgrade head` from a
clean database creates all 30 tables below with no manual intervention.

## Conventions

- Every table has `created_at` / `updated_at` (`database/models/base.py:TimestampMixin`).
- Enum columns are Python `str, enum.Enum` classes mapped once via
  `Base.type_annotation_map` (`database/models/base.py`) to a single named
  Postgres `ENUM` type, so `Mapped[Sport]` anywhere in the schema resolves
  consistently.
- Any row sourced from a provider carries `data_quality`
  (`high | medium | low | mock`, see `database/models/enums.py`). `mock` is
  never presented to a user as production data.
- `Match.data_source` + `Match.external_ref` is a unique key so re-ingesting
  the same fixture from the same provider is idempotent.

## Tables

### Reference / core (`database/models/core.py`)
- `users` — auth identity, `role` (user/admin), hashed password only.
- `teams`, `players`, `venues`, `competitions`, `seasons` — reference data,
  shared across both sports (`sport` discriminator on `teams`/`players`/`competitions`).
- `matches` — one row per fixture; `status`, `toss_winner_team_id` /
  `toss_decision` (cricket), `result_summary` (JSON).
- `lineups` — playing XI / starting lineup, shared shape (`batting_order`
  for cricket, `formation_position` for football).
- `match_events` — sport-agnostic event timeline (toss, wicket, goal, card,
  half-time, ...). This is the trigger table the live engine watches.

### Cricket (`database/models/cricket.py`)
- `innings` — one row per team-innings; `target`, running totals.
- `deliveries` — ball-by-ball; `sequence` is the monotonic ordering key
  within an innings used for leakage-safe "as of this ball" feature reads;
  carries `score_before_ball`, `wickets_before_ball`, run rates, phase.
- `player_match_stats`, `team_match_stats` — per-match aggregates.
- `player_venue_stats`, `player_competition_stats`, `player_opponent_stats`,
  `player_bowler_matchups` — cross-match aggregates, each with a `stats`
  JSON blob, a `sample_size`, and `data_quality`. `sample_size` is what the
  ML layer shrinks small-sample aggregates against (see `docs/ML.md`).

### Football (`database/models/football.py`)
- `football_events` — granular event stream (shot coordinates, assists,
  substitutions) — the football analogue of `deliveries`.
- `football_player_stats`, `football_team_stats` — per-match aggregates
  (shots, possession, passes, cards, formation).

### Context (`database/models/context.py`)
- `weather_snapshots` — per-match weather at capture time.
- `news_articles` / `news_entities` — ingested news, `category`
  (injury/suspension/selection/...), `verification_status`
  (confirmed/reported/unverified), deduplicated via `dedupe_hash`.
- `odds_snapshots` — raw market price observations.
- `market_movements` — derived opening-vs-current price movement and
  model-vs-market divergence. Kept structurally separate from
  `prediction_features` (see `docs/ML.md#market-data-separation`).

### Predictions & model governance (`database/models/predictions.py`)
- `model_versions` — one row per trained model artifact; `is_active` flags
  the version currently serving.
- `model_metrics` — Brier score / log loss / accuracy / ECE per model
  version, optionally sliced by competition/season.
- `predictions` — every prediction ever served: `model_version_id`,
  `feature_version`, `data_version`, `probabilities` (JSON,
  mutually-consistent and 0..1 by construction — see `ml/calibration`),
  `data_quality`, `model_confidence`, `explanation`, `result_status`.
- `prediction_features` — the exact feature snapshot used, each with its
  own `feature_timestamp`, so leakage can be re-verified after the fact.
- `prediction_results` — actual outcome once the match resolves;
  `is_correct` / `brier_contribution`. A prediction row is never deleted
  when a result is unfavorable — this table is append-only history.
- `backtest_runs` — one row per backtest execution: the exact
  train/validation/test date ranges used and the resulting metrics JSON.

## Migrations

```bash
# create a new migration after changing database/models/*
alembic revision --autogenerate -m "describe the change"

# apply
alembic upgrade head

# roll back one step
alembic downgrade -1
```

`alembic.ini` lives at the repo root; `DATABASE_URL` (from `.env`) is read
by `database/migrations/env.py` at migration time, so no URL is hard-coded
in version-controlled config.

## Seed data

`database/seed/mock_data.py` inserts a small, internally-consistent set of
mock teams/players/venues/matches/deliveries — everything tagged
`data_quality=mock` — purely so the API and frontend have something to
render in local development without any provider credentials. It is never
run against a database configured with `APP_ENV=production`.
