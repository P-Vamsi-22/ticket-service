# Ticket API

FastAPI + SQLAlchemy 2.0 + Alembic + SQLite ticket tracker.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```powershell
uv sync
```

## Run

```powershell
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Seed fake data

```powershell
uv run python seed.py
```

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

## Endpoints

### Users
- `POST /users` — create user `{name, email}` → 201 / 409 duplicate email / 422
- `GET /users/{id}` — get user → 200 / 404

### Tickets
- `POST /tickets` — create `{title, description, status?, priority?, created_by}` → 201 / 404 bad user / 422
- `GET /tickets?page=1&size=20&status=&priority=` — paginated list with filters
- `GET /tickets/{id}` — get ticket → 200 / 404
- `PATCH /tickets/{id}` — partial update `{title?, description?, status?, priority?}` → 200 / 404 / 409 invalid status transition / 422
- `DELETE /tickets/{id}` — delete ticket (cascades comments) → 204 / 404

### Comments
- `POST /tickets/{id}/comments` — `{author_id, body}` → 201 / 404 bad ticket or author / 422
- `GET /tickets/{id}/comments` — list comments → 200 / 404

Errors use RFC 7807 Problem Details JSON (`type`, `title`, `status`, `detail`).
