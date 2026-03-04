# Repository Guidelines

## Project Structure & Module Organization
- `app/`: primary FastAPI backend.
- `app/api/`: HTTP and WebSocket routes.
- `app/services/`: orchestration/business logic (workflow execution, tool registry, workspace access).
- `app/core/`: engine, executor, config, platform/permission utilities.
- `app/database/`: SQLite initialization and migration helpers.
- `src/`: legacy/auxiliary workflow node implementations used by backend execution.
- `config/tools/*.json`: tool definitions consumed by registry/execution flows.
- `tests/`: pytest suite and fixtures (`tests/fixtures/`).
- `scripts/`: operational scripts (migration, seeding, execution checks).
- `data/` and `logs/`: runtime artifacts; do not commit generated contents.

- `docs`  documents on our workflow system's design, and we should always updates


## Build, Test, and Development Commands
- Install deps: `uv sync`
- Start backend locally: `uv run python -m app.main`
- Initialize DB: `uv run python -c "from app.database.init_db import initialize_database; initialize_database()"`
- Run all tests: `uv run pytest`
- Run focused workflow test: `uv run pytest tests/test_workflow_execution.py -v`
- Coverage (recommended before PR): `uv run pytest --cov=app --cov-report=term-missing`

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, UTF-8 source files.
- Follow PEP 8 and keep type hints on service/API boundaries.
- Naming: `snake_case` for functions/files/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules cohesive by layer (`api` -> `services` -> `core`/`database`).
- Formatting tools available in repo dependencies: `black`, `isort`, `mypy` (run via `uv run` when relevant).

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio`.
- Test discovery (from `pytest.ini`): `test_*.py`, `Test*` classes, `test_*` functions.
- Markers available: `unit`, `integration`, `e2e`, `slow`, `requires_docker`, `requires_network`.
- Add or update tests for every behavior change, especially workflow execution and API contracts.

## Commit & Pull Request Guidelines
- Current history uses short, direct subjects (English or Chinese) without strict Conventional Commit prefixes.
- Prefer one-line imperative subjects under 72 chars, scoped to one change.
- PRs should include: purpose, key design/behavior changes, test evidence (commands + results), and linked issue/change ticket.
- For API changes, include example request/response payloads.

## Security & Configuration Tips
- Keep secrets and local overrides out of git; use environment variables or untracked local config.
- Validate tool paths and filesystem permissions when editing `config/tools/*.json` or workspace logic.
