"""Shared pytest fixtures.

Database-backed tests (data normalization, backend API) run against a real
PostgreSQL database (`DATABASE_URL_TEST`, default `khelniti_test` — see
.env.example) rather than SQLite, so the schema/constraints under test are
the exact ones the application runs against in production. Each test runs
inside a transaction that is rolled back afterward, so tests never leak
state into each other regardless of order.
"""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.models import Base

TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL_TEST", "postgresql+psycopg2://khelniti:khelniti@localhost:5432/khelniti_test"
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    try:
        eng.connect().close()
    except Exception as exc:  # pragma: no cover - environment guard
        pytest.skip(f"Test database not reachable at {TEST_DATABASE_URL}: {exc}")
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient

    from backend.app.database import get_db
    from backend.app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
