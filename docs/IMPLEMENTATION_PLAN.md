# Implementation Plan

## Current Delivery Snapshot (2026-03-06)

- Completed in current baseline:
  - MVP process CRUD and text-to-graph generation.
  - Graph quality metrics and warnings contract.
  - Workspace filters, node drill-down, insights.
  - Revision history and version compare.
  - Lifecycle moderation (`draft -> in_review -> approved`).
  - Review comments for process/node/edge.
  - Unified regression runner and release checklist.
- Pending tracks for next delivery:
  - auth/RBAC,
  - export pipeline,
  - async workers,
  - CI/CD automation,
  - large-graph performance hardening.

## Phase 0. Foundation Setup (1-2 days)

- Initialize monorepo: `apps/web`, `apps/api`, `packages/shared`.
- Configure linters, formatter, and pre-commit hooks.
- Define `ProcessGraph` JSON Schema.

## Phase 1. MVP Core (1 week)

- Backend: process and version CRUD.
- Frontend: base graph canvas + node detail card.
- Text import and manual node/edge editing.

## Phase 2. AI Pipeline (1-2 weeks)

- Integrate agents:
  - Ingestion
  - Decomposition
  - Component Mapping
  - Visualization Spec
  - QA
- Async jobs via Redis/Celery.
- Task statuses and progress in UI.

## Phase 3. Moderation and Quality (1 week)

- State workflow: Draft -> Review -> Approved.
- Reviewer comments.
- Pre-publish diagram validation.

## Phase 4. Infographics and Export (1 week)

- Analytics blocks (bottlenecks, dependencies, role matrices).
- PDF/PNG export.
- Shareable link.

## Phase 5. Production Readiness (1 week)

- Load testing.
- Metrics, alerts, and tracing.
- CI/CD: lint/test/build/deploy.

## MVP Deliverables

- Working app with L1/L2/L3 visualization.
- AI decomposition pipeline with manual verification.
- Baseline analytics and export.
- Architecture and development process documentation.
