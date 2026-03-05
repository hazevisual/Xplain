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

Phase 0 scaffold is initialized:

- `apps/web` - Next.js frontend baseline.
- `apps/api` - FastAPI backend baseline.
- `packages/shared` - shared JSON schema contracts.
- `docs/tasks/TASK-20260306-001.md` - first task card and state log.

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
   - Run `uvicorn app.main:app --reload --port 8000`
3. Infra services (optional):
   - `docker compose up -d`
