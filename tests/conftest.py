import os

# Test-only secret, set before the app is imported. The real one lives in .env (git-ignored).
os.environ["JWT_SECRET"] = "test-secret-for-pytest-only-0123456789abcdef"

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole
from app.routers import auth as auth_router

PASSWORD = "test-pass-123"


@dataclass
class Actor:
    id: int
    email: str
    headers: dict[str, str]


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_login_lockout():
    auth_router._failed_logins.clear()
    yield
    auth_router._failed_logins.clear()


def login(client, email, password=PASSWORD) -> dict[str, str]:
    resp = client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def make_user(client, session_factory):
    """Sign up through the API (always EMPLOYEE); agents are promoted directly in the DB, like seed.py."""

    def _make(name: str, email: str, role: UserRole = UserRole.EMPLOYEE) -> Actor:
        resp = client.post("/users", json={"name": name, "email": email, "password": PASSWORD})
        assert resp.status_code == 201, resp.text
        user_id = resp.json()["id"]
        if role is UserRole.AGENT:
            with session_factory() as db:
                db.get(User, user_id).role = UserRole.AGENT
                db.commit()
        return Actor(user_id, email, login(client, email))

    return _make


@pytest.fixture()
def ada(make_user) -> Actor:
    return make_user("Ada", "ada@example.com")


@pytest.fixture()
def bob(make_user) -> Actor:
    return make_user("Bob", "bob@example.com")


@pytest.fixture()
def agent(make_user) -> Actor:
    return make_user("Agnes Agent", "agent@example.com", UserRole.AGENT)


def new_ticket(client, actor: Actor, **overrides) -> dict:
    payload = {"title": "Bug report", "description": "Something is broken"}
    payload.update(overrides)
    resp = client.post("/tickets", json=payload, headers=actor.headers)
    assert resp.status_code == 201, resp.text
    return resp.json()
