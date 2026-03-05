# XPlain

Web application for visually describing complex processes using interactive diagrams, subprocess maps, and infographics.

## What Is Already Defined

- Project goals and scope: [docs/PROJECT_VISION.md](docs/PROJECT_VISION.md)
- Functional requirements: [docs/FUNCTIONAL_REQUIREMENTS.md](docs/FUNCTIONAL_REQUIREMENTS.md)
- Architecture, agent roles, and data model: [docs/ARCHITECTURE_AND_AGENTS.md](docs/ARCHITECTURE_AND_AGENTS.md)
- Pipeline decision and selection criteria: [docs/PIPELINE_DECISION.md](docs/PIPELINE_DECISION.md)
- Implementation plan (MVP -> Production): [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- Agent team structure and escalation rules: [docs/AGENT_TEAM_STRUCTURE.md](docs/AGENT_TEAM_STRUCTURE.md)
- Agent registry (machine-readable): [agents/registry.yaml](agents/registry.yaml)
- Lead Orchestrator (main agent): [docs/LEAD_ORCHESTRATOR.md](docs/LEAD_ORCHESTRATOR.md)
- Required agent branches (before development): [agents/branches/README.md](agents/branches/README.md)
- Task card/state log standard: [docs/TASK_RUNBOOK.md](docs/TASK_RUNBOOK.md)

## Current Stage Goal

Establish project documentation and an execution plan to start implementation without ambiguity in architecture, process, or agent ownership.

## Bootstrap Status

Phase 0 and initial Phase 1 backend persistence are initialized:

- `apps/web` - Next.js frontend baseline.
- `apps/api` - FastAPI backend with process CRUD, PostgreSQL storage, and graph generation endpoint.
- `packages/shared` - shared JSON schema contracts.
- `docs/tasks/TASK-20260306-001.md` - first task card and state log.
- `docs/tasks/TASK-20260306-002.md` - phase 1 minimal CRUD task.
- `docs/tasks/TASK-20260306-005.md` - visual explanation MVP (`text -> graph`) task.

## Repository Structure

```text
XPlain/
  agents/
  apps/
    web/
    api/
  packages/
    shared/
  docs/
    tasks/
  docker-compose.yml
```

## Local Start (Bootstrap)

1. Frontend (`apps/web`):
   - Install dependencies with `npm install`
   - Run with `npm run dev:web` from repo root
2. Backend (`apps/api`):
   - Create virtual environment
   - Install `requirements.txt`
   - Set `XPLAIN_STORAGE=postgres` and `DATABASE_URL=postgresql+psycopg://xplain:xplain@localhost:5432/xplain`
   - Run migrations: `alembic upgrade head`
   - Run `uvicorn app.main:app --reload --port 8000`
3. Full stack via Docker Compose (recommended):
   - `docker compose up -d`

## Fast Readiness Check

Use the fast probe script instead of long manual loops:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/wait-url.ps1 -Url http://localhost:8000/health
powershell -ExecutionPolicy Bypass -File scripts/wait-url.ps1 -Url http://localhost:3000
```
