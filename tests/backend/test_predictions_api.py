from datetime import datetime, timezone

from sklearn.linear_model import LogisticRegression

from data.ingestion.providers.mock_cricket import MockCricketProvider
from data.normalization.cricket import ingest_cricket_match
from database.models.enums import Sport
from database.models.predictions import ModelVersion
from ml.cricket.features import build_match_state, extract_features, feature_vector
from ml.cricket.monte_carlo import estimate_phase_distributions
from ml.cricket.win_probability import CricketWinProbabilityEnsemble


def _register_and_get_token(client, email="predictor@example.com"):
    client.post("/auth/register", json={"email": email, "password": "correcthorse123", "full_name": "Predictor"})
    resp = client.post("/auth/login", json={"email": email, "password": "correcthorse123"})
    return resp.json()["access_token"]


def _seed_match_with_deliveries(db_session, external_ref="predictions-api-test-1"):
    provider = MockCricketProvider(seed=5)
    result = provider.generate_match(external_ref)
    match = ingest_cricket_match(db_session, provider.provider_name, result.match, result.deliveries)
    db_session.flush()
    return match


def _train_and_register_tiny_model(db_session, tmp_path):
    provider = MockCricketProvider(seed=55)
    corpus = provider.generate_training_corpus(n_matches=30)

    X, y = [], []
    for m in corpus:
        for innings_number in (1, 2):
            deliveries = [d for d in m.deliveries if d.innings_number == innings_number]
            if len(deliveries) < 30:
                continue
            target = m.first_innings_runs + 1 if innings_number == 2 else None
            state = build_match_state(deliveries[:30], innings_number, target)
            label = int(
                (innings_number == 1 and m.winner == "home") or (innings_number == 2 and m.winner == "away")
            )
            X.append(feature_vector(extract_features(state)))
            y.append(label)

    model = LogisticRegression(max_iter=500).fit(X, y)
    deliveries = [d for m in corpus for d in m.deliveries]
    distributions = estimate_phase_distributions(deliveries)
    ensemble = CricketWinProbabilityEnsemble(model, distributions, version="test-only")

    artifact_path = str(tmp_path / "test_model.joblib")
    ensemble.save(artifact_path)

    model_version = ModelVersion(
        sport=Sport.CRICKET,
        model_name="cricket_win_probability",
        version="test-only",
        trained_at=datetime.now(timezone.utc),
        artifact_path=artifact_path,
        is_active=True,
    )
    db_session.add(model_version)
    db_session.flush()
    return model_version


def test_predictions_requires_auth(client, db_session):
    match = _seed_match_with_deliveries(db_session)
    resp = client.post(f"/matches/{match.id}/predictions/win-probability")
    assert resp.status_code == 401


def test_predictions_no_active_model_returns_503(client, db_session):
    match = _seed_match_with_deliveries(db_session)
    token = _register_and_get_token(client)
    resp = client.post(
        f"/matches/{match.id}/predictions/win-probability", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 503


def test_predictions_insufficient_data_returns_422(client, db_session):
    # A match that exists but has no innings/deliveries recorded yet.
    from database.models.core import Competition, Match, Team
    from database.models.enums import MatchStatus

    home = Team(sport=Sport.CRICKET, name="Empty Home")
    away = Team(sport=Sport.CRICKET, name="Empty Away")
    competition = Competition(sport=Sport.CRICKET, name="Empty League")
    db_session.add_all([home, away, competition])
    db_session.flush()

    match = Match(
        sport=Sport.CRICKET,
        competition_id=competition.id,
        home_team_id=home.id,
        away_team_id=away.id,
        scheduled_start=datetime.now(timezone.utc),
        status=MatchStatus.SCHEDULED,
        data_source="test",
        external_ref="empty-match-1",
    )
    db_session.add(match)
    db_session.flush()

    token = _register_and_get_token(client, email="predictor2@example.com")
    resp = client.post(
        f"/matches/{match.id}/predictions/win-probability", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 422


def test_predictions_full_flow_returns_valid_probability_distribution(client, db_session, tmp_path):
    match = _seed_match_with_deliveries(db_session)
    _train_and_register_tiny_model(db_session, tmp_path)
    token = _register_and_get_token(client, email="predictor3@example.com")

    resp = client.post(
        f"/matches/{match.id}/predictions/win-probability", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["model_name"] == "cricket_win_probability"
    assert body["model_version"] == "test-only"
    assert body["data_quality"] == "mock"
    total = sum(body["probabilities"].values())
    assert abs(total - 1.0) < 1e-6
    assert all(0.0 <= p <= 1.0 for p in body["probabilities"].values())

    history_resp = client.get(f"/matches/{match.id}/predictions")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 1

    prediction_id = body["id"]
    features_resp = client.get(f"/predictions/{prediction_id}/features")
    assert features_resp.status_code == 200
    assert len(features_resp.json()) > 0
