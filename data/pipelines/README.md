# Data pipelines (not yet built)

Reserved for scheduled/orchestrated ingestion pipelines (e.g. "poll the
live-match provider every N seconds and run it through
`data/normalization`") once a real provider is wired in. Today,
ingestion is invoked directly — `database/seed/mock_data.py` for
mock data, or a one-off script calling `data/normalization/*` — rather
than through a scheduler. See
[docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md#scope-and-roadmap).
