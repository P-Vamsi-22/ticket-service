from datetime import datetime, timedelta, timezone

import jwt

from app import config
from app.security import decode_access_token
from tests.conftest import PASSWORD


def test_login_returns_jwt_with_user_id_and_role(client, ada):
    resp = client.post("/auth/token", data={"username": ada.email, "password": PASSWORD})
    assert resp.status_code == 200
    claims = decode_access_token(resp.json()["access_token"])
    assert claims["sub"] == str(ada.id)
    assert claims["role"] == "EMPLOYEE"
    assert claims["exp"] - claims["iat"] == 30 * 60


def test_login_email_is_case_insensitive(client, ada):
    resp = client.post("/auth/token", data={"username": "ADA@example.com", "password": PASSWORD})
    assert resp.status_code == 200


def test_wrong_password_401_problem_details(client, ada):
    resp = client.post("/auth/token", data={"username": ada.email, "password": "wrong-pass"})
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"
    assert resp.json()["title"] == "Unauthorized"


def test_unknown_email_same_401(client):
    resp = client.post("/auth/token", data={"username": "ghost@example.com", "password": "x" * 10})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"


def test_lockout_after_5_failed_logins(client, ada):
    for _ in range(5):
        client.post("/auth/token", data={"username": ada.email, "password": "wrong-pass"})
    resp = client.post("/auth/token", data={"username": ada.email, "password": PASSWORD})
    assert resp.status_code == 429


def test_me(client, agent):
    resp = client.get("/auth/me", headers=agent.headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "AGENT"


def _token(sub, secret=None, alg="HS256", minutes=30, past=False):
    now = datetime.now(timezone.utc) - (timedelta(hours=2) if past else timedelta(0))
    claims = {"sub": sub, "role": "AGENT", "iat": now, "exp": now + timedelta(minutes=minutes)}
    key = None if alg == "none" else (secret or config.JWT_SECRET)
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm=alg)}"}


def test_expired_token_401(client, ada):
    assert client.get("/tickets", headers=_token(str(ada.id), past=True)).status_code == 401


def test_forged_token_wrong_secret_401(client, ada):
    forged = _token(str(ada.id), secret="attacker-secret-attacker-secret-123")
    assert client.get("/tickets", headers=forged).status_code == 401


def test_alg_none_token_401(client, ada):
    assert client.get("/tickets", headers=_token(str(ada.id), alg="none")).status_code == 401


def test_token_for_unknown_user_401(client, ada):
    assert client.get("/tickets", headers=_token("999")).status_code == 401


def test_role_in_token_is_not_trusted(client, ada, bob):
    # Ada's token says role=AGENT (signed with the real secret, e.g. issued before a demotion):
    # the server re-reads the role from the DB, so she still can't see Bob's ticket.
    bob_ticket = client.post("/tickets", json={"title": "b", "description": "d"}, headers=bob.headers)
    resp = client.get(f"/tickets/{bob_ticket.json()['id']}", headers=_token(str(ada.id)))
    assert resp.status_code == 403
