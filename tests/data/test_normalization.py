import pytest
from sqlalchemy import select

from data.ingestion.providers.mock_cricket import MockCricketProvider
from data.ingestion.providers.mock_football import MockFootballProvider
from data.normalization.cricket import ingest_cricket_match
from data.normalization.football import ingest_football_match
from data.validation.exceptions import DuplicateDataError
from database.models.cricket import Delivery, Innings
from database.models.football import FootballEvent


def test_ingest_cricket_match_creates_innings_and_deliveries(db_session):
    provider = MockCricketProvider(seed=1)
    result = provider.generate_match("test-cricket-1")

    match = ingest_cricket_match(db_session, provider.provider_name, result.match, result.deliveries)
    db_session.flush()

    innings = db_session.scalars(select(Innings).where(Innings.match_id == match.id)).all()
    deliveries = db_session.scalars(select(Delivery).where(Delivery.innings_id.in_([i.id for i in innings]))).all()

    assert len(innings) == 2
    assert len(deliveries) == len(result.deliveries)

    second_innings = next(i for i in innings if i.innings_number == 2)
    assert second_innings.target == result.first_innings_runs + 1


def test_ingest_cricket_match_rejects_duplicate(db_session):
    provider = MockCricketProvider(seed=2)
    result = provider.generate_match("test-cricket-2")
    ingest_cricket_match(db_session, provider.provider_name, result.match, result.deliveries)
    db_session.flush()

    with pytest.raises(DuplicateDataError):
        ingest_cricket_match(db_session, provider.provider_name, result.match, result.deliveries)


def test_ingest_football_match_creates_events(db_session):
    provider = MockFootballProvider(seed=1)
    result = provider.generate_match("test-football-1")

    match = ingest_football_match(db_session, provider.provider_name, result.match, result.events)
    db_session.flush()

    events = db_session.scalars(select(FootballEvent).where(FootballEvent.match_id == match.id)).all()
    assert len(events) == len(result.events)

    goal_events = [e for e in events if e.event_type == "goal"]
    assert len(goal_events) == result.home_goals + result.away_goals
