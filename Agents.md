# AGENTS.md – ticket-service

## Stack
- Python 3.12+, managed with uv
- pytest + pytest-cov for tests
- No web framework; this is a plain Python service layer

## Commands
- Install: `uv sync`
- Run tests: `uv run pytest -v`
- Coverage: `uv run pytest --cov=src --cov-report=term-missing`

## Structure
- `src/tickets/models.py` – Ticket dataclass, Status and Priority enums
- `src/tickets/errors.py` – custom exceptions
- `src/tickets/repository.py` – repository interface + in-memory implementation
- `src/tickets/service.py` – service functions (create, list, filter, update_status)
- `tests/` – pytest tests

## Conventions
- Type hints on every function
- No new dependencies without asking
- Only change files listed in the approved plan
- Invalid status changes must raise InvalidStatusTransitionError
- Run tests after every change; all must pass and coverage must be >= 80%