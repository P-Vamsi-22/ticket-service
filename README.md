# Ticket API

FastAPI + SQLAlchemy 2.0 + Alembic + SQLite ticket tracker.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```powershell
uv sync
copy .env.example .env    # then set JWT_SECRET and SEED_PASSWORD in .env
```

## Run

```powershell
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8001
```

API docs: http://localhost:8001/docs (click **Authorize**, log in with an email + password)

## Seed fake data

```powershell
uv run python seed.py
```

All seeded users use the password from `SEED_PASSWORD`. `user0@example.com` is an **AGENT**; `user1`–`user7@example.com` are **EMPLOYEES**.

## Tests

```powershell
uv run pytest -v
```

## Reset the database

```powershell
uv run alembic downgrade base
uv run alembic upgrade head
uv run python seed.py
```

## Security (Day 12)

- Login: `POST /auth/token` (OAuth2 password form; `username` = email) returns a 30-minute JWT (HS256). Send it as `Authorization: Bearer <token>`.
- Passwords are stored only as Argon2id hashes (pwdlib). 5 failed logins in 5 minutes → 429.
- The JWT secret comes from `.env` / environment variables, never from code. `.env` and `ticket.db` are git-ignored.
- Roles: **EMPLOYEE** sees and edits only their own tickets; **AGENT** sees and edits all tickets and is the only role that can delete.
- No token → **401**. Logged in but not allowed → **403**. The role is always re-read from the database, not trusted from the token.
- `created_by` and `author_id` are taken from the token, never from the request body.
- Full authorization matrix: `tests/test_authz.py`.

## Endpoints

Everything except `POST /users`, `POST /auth/token` and `GET /health` needs a Bearer token.

### Auth
- `POST /auth/token` — form `username` (email), `password` → 200 `{access_token, token_type}` / 401 / 429
- `GET /auth/me` — the logged-in user

### Users
- `POST /users` — public sign-up `{name, email, password}` → 201 (always EMPLOYEE) / 409 duplicate email / 422
- `GET /users/{id}` — own profile, or any profile for agents → 200 / 403 / 404

### Tickets
- `POST /tickets` — create `{title, description, status?, priority?}`; owner = logged-in user → 201 / 422
- `GET /tickets?page=1&size=20&status=&priority=` — paginated list (employees: own tickets only; agents: all)
- `GET /tickets/{id}` — 200 / 403 not yours / 404
- `PATCH /tickets/{id}` — partial update `{title?, description?, status?, priority?}` → 200 / 403 / 404 / 409 invalid status transition / 422
- `DELETE /tickets/{id}` — agents only (cascades comments) → 204 / 403 / 404

### Comments
- `POST /tickets/{id}/comments` — `{body}`; author = logged-in user → 201 / 403 / 404 / 422
- `GET /tickets/{id}/comments` — list comments → 200 / 403 / 404

Errors use RFC 7807 Problem Details JSON (`type`, `title`, `status`, `detail`).
