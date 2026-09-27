# Data Sources

## Provider abstraction

Every external data category is accessed only through an interface in
`data/ingestion/providers/base.py`:

| Interface | Purpose |
|---|---|
| `CricketDataProvider` | live matches, ball-by-ball deliveries |
| `FootballDataProvider` | live fixtures, match events |
| `NewsDataProvider` | news articles |
| `WeatherDataProvider` | venue weather/conditions |
| `MarketDataProvider` | betting odds |

`data/ingestion/providers/registry.py` is the only place that picks a
concrete implementation, based on `DATA_PROVIDER_MODE` in `.env`
(`mock` | `live`). Nothing else in the codebase imports a concrete provider
class directly.

## Mock providers (default, no credentials required)

`mock_cricket.py`, `mock_football.py`, `mock_news.py`, `mock_weather.py`,
`mock_market.py` generate deterministic (seeded) synthetic data:

- Cricket: a phase-aware (powerplay/middle/death) random ball-by-ball T20
  simulator with realistic-shaped run and wicket distributions.
- Football: a Poisson goal process with per-match attack-strength noise —
  the same generative model the Dixon-Coles xG estimator assumes, so
  backtesting against it is a real test of the estimator.
- News/weather/market: simple deterministic generators covering the schema.

Every payload these providers return carries `data_quality=DataQuality.MOCK`,
which is threaded through normalization into every downstream row and
surfaced directly in the API/UI. Mock data is never mixed with data from a
real provider in the same database — the intended workflow is a dedicated
mock/dev database, never a shared one with production ingests.

## Adding a real provider

1. Implement the relevant interface (e.g. `CricketDataProvider`) against
   your vendor's API in a new file under `data/ingestion/providers/`.
2. Add a branch for it in `registry.py` alongside the existing
   `DATA_PROVIDER_MODE == "mock"` checks.
3. Add the vendor's base URL and API key to `.env` (see `.env.example` —
   `CRICKET_DATA_API_KEY`, `FOOTBALL_DATA_API_KEY`, etc.). **Never commit a
   real key** — `.env` is gitignored; only `.env.example` is tracked.
4. Set `data_quality` on every payload you return based on what the vendor
   actually guarantees (`high`/`medium`/`low`) — never default to `high`
   just because the source is "real".

## Licensing requirements

- **Cricket/football match data**: most ball-by-ball or event-level
  providers (e.g. commercial cricket/football data vendors) require a paid
  license; check your vendor's terms before ingesting their data into any
  system that serves predictions, especially if redistributed.
- **News**: many news APIs restrict redistribution of full article text;
  `news_articles.summary` is intended for a short, license-compliant
  excerpt, not a full-text mirror — verify your provider's terms.
- **Weather**: most public weather APIs (rate-limited free tiers or paid)
  are fine for non-commercial use; check commercial terms if this platform
  is monetized.
- **Market/odds data**: odds/market data is typically the most tightly
  licensed and sometimes jurisdiction-restricted (gambling-data
  regulations vary by country/state). `MarketDataProvider` defaults to
  disabled (`get_market_provider()` returns `None` unless explicitly
  configured) specifically so this platform never ships with betting-odds
  ingestion silently enabled. Confirm you're legally permitted to ingest
  and display odds data in your jurisdiction before enabling it.

## Known limitations of the mock corpus

- Mock player/team names are synthetic and carry no real-world identity or
  historical record — they exist only to exercise the schema and models.
- The mock cricket/football generators do not model correlated team
  strength across a "season" (each match's parameters are drawn
  independently) — this is sufficient for testing the pipeline and
  validating calibration/backtesting mechanics, but insufficient for
  claiming any real predictive skill. See `docs/MODEL_LIMITATIONS.md`.
