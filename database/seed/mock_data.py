"""Loads a handful of mock cricket and football matches into the database
for local development — every row this creates is tagged
`data_quality=mock` (see data/ingestion/providers/mock_*.py).

Run: python -m database.seed.mock_data

Never run this against a database configured with APP_ENV=production.
"""
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from data.ingestion.providers.mock_cricket import MockCricketProvider
from data.ingestion.providers.mock_football import MockFootballProvider
from data.normalization.cricket import ingest_cricket_match
from data.normalization.football import ingest_football_match
from data.validation.exceptions import DuplicateDataError

N_CRICKET_MATCHES = 5
N_FOOTBALL_MATCHES = 5


def main():
    if os.environ.get("APP_ENV") == "production":
        print("Refusing to seed mock data: APP_ENV=production", file=sys.stderr)
        sys.exit(1)

    database_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg2://khelniti:khelniti@localhost:5432/khelniti"
    )
    engine = create_engine(database_url)

    cricket_provider = MockCricketProvider()
    football_provider = MockFootballProvider()

    created = 0
    with Session(engine) as session:
        for i in range(N_CRICKET_MATCHES):
            result = cricket_provider.generate_match(f"seed-cricket-{i:03d}")
            try:
                ingest_cricket_match(session, cricket_provider.provider_name, result.match, result.deliveries)
                created += 1
            except DuplicateDataError:
                pass  # already seeded — safe to re-run

        for i in range(N_FOOTBALL_MATCHES):
            result = football_provider.generate_match(f"seed-football-{i:03d}")
            try:
                ingest_football_match(session, football_provider.provider_name, result.match, result.events)
                created += 1
            except DuplicateDataError:
                pass

        session.commit()

    print(f"Seed complete: {created} new mock matches (duplicates from a prior run were skipped).")


if __name__ == "__main__":
    main()
