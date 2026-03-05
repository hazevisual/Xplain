# API App

Backend application for XPlain (`FastAPI`).

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment

```bash
XPLAIN_STORAGE=postgres
DATABASE_URL=postgresql+psycopg://xplain:xplain@localhost:5432/xplain
```

- Use `XPLAIN_STORAGE=inmemory` for local fallback mode.
- In `postgres` mode, run migrations before starting API.

## Migrations

```bash
alembic upgrade head
alembic current
```

## Tests

```bash
pytest tests -q
```

## Error Contract

All API errors return a stable envelope:

```json
{
  "error": {
    "code": "validation_error|process_not_found|source_text_empty|...",
    "message": "Human-readable message",
    "details": {}
  }
}
```

## Planned Scope

- Process/version CRUD.
- Agent orchestration endpoints.
- Async task tracking and review workflow APIs.
