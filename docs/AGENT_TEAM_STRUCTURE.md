# Agent Team Structure

## Goal

Define specialized agents by project branch and assign a `Lead Agent` to orchestrate invocations and execution order.

## Core Operating Model

- `Lead Agent` receives a task from user/system.
- `Lead Agent` decomposes it into subtasks.
- `Lead Agent` invokes specialized agents as needed.
- Each specialized agent returns:
  - result;
  - status (`done|blocked|needs_review`);
  - risks and dependencies.
- `Lead Agent` aggregates outputs and decides on next calls or escalation.

## Lead

### `Lead Agent`

Responsibilities:

- route tasks between agents;
- prioritize and control SLA;
- manage dependencies across branches (`front/back/database/devops`);
- assemble final solution and return status;
- escalate conflicts to manual review.

Specialist invocation triggers:

- complex or high-risk tasks requiring decomposition -> `Planning Agent`;
- UI/UX changes -> `Frontend Agent`;
- API/business logic changes -> `Backend Agent`;
- schema/migration changes -> `Database Agent`;
- infrastructure/deploy/CI changes -> `DevOps Agent`;
- test coverage/regression needs -> `QA Agent`;
- security/access risks -> `Security Agent`;
- AI pipeline/prompt changes -> `AI Pipeline Agent`;
- project docs updates -> `Documentation Agent`.

## Specialist Agents

### `Planning Agent`

- Scope: task decomposition, sequencing, risk-aware execution plan.
- Input: high-level requests, constraints, and deadlines.
- Output: subtask plan, branch dependencies, and mitigation strategy.

### `Frontend Agent`

- Scope: UI, interactive visualization, client performance, accessibility.
- Input: interface and UX tasks.
- Output: UI changes, acceptance criteria, risks.

### `Backend Agent`

- Scope: API, domain logic, integrations, background jobs.
- Input: service logic and contract tasks.
- Output: API/service changes and updated contracts.

### `Database Agent`

- Scope: schema, indexes, migrations, data integrity.
- Input: domain model and storage changes.
- Output: migrations, DDL updates, rollback plan.

### `DevOps Agent`

- Scope: CI/CD, containerization, environments, monitoring.
- Input: build, deploy, and operations tasks.
- Output: pipeline configs, runbooks, alerts.

### `QA Agent`

- Scope: test plan, e2e/regression, release quality.
- Input: any merged candidate.
- Output: risk report, defect list, verdict.

### `Security Agent`

- Scope: RBAC, secrets, dependency vulnerabilities, audit trail.
- Input: auth/data/infra changes.
- Output: security checklist, findings, remediation steps.

### `AI Pipeline Agent`

- Scope: agent pipeline, prompt/chain orchestration, generation quality.
- Input: AI logic and process extraction quality changes.
- Output: updated pipeline steps and quality metrics.

### `Documentation Agent`

- Scope: requirements, ADR, runbooks, technical docs.
- Input: architecture and process changes.
- Output: updated docs and change log.

## Collaboration Rules

- Every task goes through `Lead Agent`.
- Direct specialist calls without lead routing are not allowed.
- `Planning Agent` is mandatory for complex tasks before implementation starts.
- `QA Agent` is mandatory before final task closure.
- `Documentation Agent` is mandatory if behavior/contracts changed.
- Agent conflicts are resolved in this order:
  1. Align contracts (`API`, `Schema`, `Events`).
  2. Prioritize security and data integrity requirements.
  3. If unresolved -> manual review.

## SLA (Baseline)

- Initial triage by lead: up to 15 minutes.
- Specialist response for a standard task: up to 60 minutes.
- Escalation of blocked tasks: up to 30 minutes from detection.

## Definition of Done

- Changes are implemented across all affected branches.
- Tests and quality checks are passing.
- Documentation is updated when contract/behavior changed.
- `Lead Agent` marks final status as `done`.
- Task card/state log is updated in `docs/TASK_RUNBOOK.md` format.
- For complex tasks, planning gate is completed with approved subtask breakdown.
