from data.ingestion.providers.mock_cricket import MockCricketProvider
from data.normalization.cricket import ingest_cricket_match


def _seed_match(db_session, external_ref="matches-api-test-1"):
    provider = MockCricketProvider(seed=3)
    result = provider.generate_match(external_ref)
    match = ingest_cricket_match(db_session, provider.provider_name, result.match, result.deliveries)
    db_session.flush()
    return match


def test_list_matches_returns_seeded_match(client, db_session):
    match = _seed_match(db_session)
    resp = client.get("/matches")
    assert resp.status_code == 200
    ids = [m["id"] for m in resp.json()]
    assert match.id in ids


def test_get_match_returns_full_detail(client, db_session):
    match = _seed_match(db_session, external_ref="matches-api-test-2")
    resp = client.get(f"/matches/{match.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sport"] == "cricket"
    assert body["home_team"]["name"]
    assert body["data_quality"] == "mock"


def test_get_nonexistent_match_returns_404(client, db_session):
    resp = client.get("/matches/999999")
    assert resp.status_code == 404


def test_list_matches_filters_by_sport(client, db_session):
    _seed_match(db_session, external_ref="matches-api-test-3")
    resp = client.get("/matches?sport=football")
    assert resp.status_code == 200
    assert all(m["sport"] == "football" for m in resp.json())
