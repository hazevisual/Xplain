# MVP Handoff (2026-03-06)

This document is the final handoff package for the current autonomous delivery track (`TASK-20260306-006`).

## Delivery Status

- Overall status: `done`
- QA gate: `passed`
- Docs gate: `updated`
- Target branch: `main`

## Implemented Scope

1. Core process CRUD and graph generation (`text -> graph`).
2. Deterministic graph quality metrics:
   - coverage percent
   - naming consistency percent
   - dangling nodes.
3. Visual workspace improvements:
   - level/type filters
   - node detail drill-down
   - warning and quality panels
   - infographic insight cards.
4. Versioning and comparison:
   - revision persistence
   - revision list endpoint
   - version compare block in UI.
5. Workflow lifecycle:
   - `draft -> in_review -> approved`
   - edit/generation lock outside `draft`.
6. Review comments:
   - comments on process/node/edge
   - target validation and structured API errors.
7. Unified release-readiness regression runner.

## Key Commits

- `abea425` - API hardening, quality metrics, tests.
- `e3cc4ac` - graph filters and quality rendering.
- `4e2e3ad` - infographic insight cards.
- `0b2da11` - revision API and compare flow.
- `e7c0981` - node detail drill-down.
- `b7dba16` - lifecycle workflow.
- `43691c7` - comments workflow (API + UI).
- `38e6d1d` - regression runner + release-readiness docs.

## Release Verification Commands

Full gate:

```powershell
npm run qa:regression
```

Fast gate (skip web production build):

```powershell
npm run qa:regression -- -SkipWebBuild
```

## API Surface (Current)

- `GET /health`
- `GET /api/v1/meta`
- `GET /api/v1/processes`
- `POST /api/v1/processes`
- `GET /api/v1/processes/{id}`
- `PUT /api/v1/processes/{id}`
- `DELETE /api/v1/processes/{id}`
- `POST /api/v1/processes/{id}/generate-graph`
- `GET /api/v1/processes/{id}/revisions`
- `POST /api/v1/processes/{id}/status`
- `GET /api/v1/processes/{id}/comments`
- `POST /api/v1/processes/{id}/comments`

## Known Gaps (Out of Current Delivery)

1. Auth/RBAC and user management.
2. Export pipeline (PDF/PNG).
3. Async worker orchestration (Redis/Celery jobs).
4. Security hardening and vulnerability scan automation.
5. Dense-graph layout optimization for large process maps.

## Recommended Next Track

1. Add auth + role model and protect lifecycle endpoints.
2. Add export service and shareable artifact generation.
3. Add background job pipeline for large inputs.
4. Add CI pipeline for automatic `qa:regression` on PR.
