SIGNUP = {"name": "Ada", "email": "ada@example.com", "password": "ada-pass-123"}


def test_create_user(client):
    resp = client.post("/users", json=SIGNUP)
    assert resp.status_code == 201
    data = resp.json()
    assert data == {"id": 1, "name": "Ada", "email": "ada@example.com", "role": "EMPLOYEE"}


def test_signup_cannot_choose_agent_role(client):
    resp = client.post("/users", json={**SIGNUP, "role": "AGENT"})
    assert resp.status_code == 201
    assert resp.json()["role"] == "EMPLOYEE"


def test_password_stored_as_argon2_hash(client, session_factory):
    from app.models import User

    client.post("/users", json=SIGNUP)
    with session_factory() as db:
        stored = db.get(User, 1).password_hash
    assert stored.startswith("$argon2") and "ada-pass-123" not in stored


def test_create_user_duplicate_email(client):
    client.post("/users", json=SIGNUP)
    resp = client.post("/users", json={**SIGNUP, "name": "Ada2"})
    assert resp.status_code == 409
    assert resp.json()["status"] == 409


def test_create_user_invalid_email(client):
    resp = client.post("/users", json={**SIGNUP, "email": "not-an-email"})
    assert resp.status_code == 422


def test_short_password_422_without_echoing_it(client):
    resp = client.post("/users", json={**SIGNUP, "password": "s3cr3t"})
    assert resp.status_code == 422
    assert "s3cr3t" not in resp.text


def test_get_own_profile(client, ada):
    resp = client.get(f"/users/{ada.id}", headers=ada.headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "ada@example.com"


def test_get_user_not_found(client, agent):
    resp = client.get("/users/999", headers=agent.headers)
    assert resp.status_code == 404
    assert "999" in resp.json()["detail"]
