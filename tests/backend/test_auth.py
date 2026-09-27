def test_register_and_login_flow(client):
    register_resp = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "correcthorse123", "full_name": "Alice"},
    )
    assert register_resp.status_code == 201
    body = register_resp.json()
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body

    login_resp = client.post("/auth/login", json={"email": "alice@example.com", "password": "correcthorse123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"


def test_register_duplicate_email_rejected(client):
    payload = {"email": "bob@example.com", "password": "correcthorse123", "full_name": "Bob"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_login_wrong_password_rejected(client):
    client.post(
        "/auth/register", json={"email": "carol@example.com", "password": "correcthorse123", "full_name": "Carol"}
    )
    resp = client.post("/auth/login", json={"email": "carol@example.com", "password": "wrong-password"})
    assert resp.status_code == 401


def test_me_without_token_rejected(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_garbage_token_rejected(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401
