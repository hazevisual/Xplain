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

## Lifecycle Workflow

- Process statuses: `draft -> in_review -> approved`.
- Transition endpoint: `POST /api/v1/processes/{id}/status`.
- Graph generation and manual updates are allowed only in `draft`.

## Review Comments

- List comments: `GET /api/v1/processes/{id}/comments`
- Add comment: `POST /api/v1/processes/{id}/comments`
- Supported targets:
  - `process` (no `targetId`)
  - `node` (`targetId` must match current graph node id)
  - `edge` (`targetId` must match current graph edge id)
- Invalid node/edge target ids return:
  - HTTP `400`
  - `error.code = "invalid_comment_target"`

## Explain Narrative

- Generate structured in-app narrative: `POST /api/v1/processes/{id}/generate-narrative`
- Returns deterministic sections:
  - `summary`
  - `steps[]`
  - `keyDependencies[]`
  - `references[]`
  - `qualityNotes[]`
- If graph is not generated yet:
  - HTTP `400`
  - `error.code = "graph_missing"`

## Planned Scope

- Process/version CRUD.
- Agent orchestration endpoints.
- Async task tracking and review workflow APIs.
