# API App

Backend application for XPlain (`FastAPI`).

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Planned Scope

- Process/version CRUD.
- Agent orchestration endpoints.
- Async task tracking and review workflow APIs.
