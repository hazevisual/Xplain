# Task Runbook

This document defines the standard task card and state log format for the agent system.

## Purpose

- Ensure every task is traceable end-to-end.
- Standardize lead assignment, execution order, risks, and closure criteria.
- Enforce mandatory gates (`Planning`, `QA`, `Documentation`) where required.

## Mandatory Gates

- `Planning Agent` is mandatory for complex tasks before implementation starts.
- `QA Agent` is mandatory before task closure.
- `Documentation Agent` is mandatory when behavior or contracts changed.

## Task Lifecycle

1. `new`
2. `triaged`
3. `planning_gate` (if task is complex)
4. `in_progress`
5. `in_review`
6. `qa_gate`
7. `docs_gate` (if behavior/contracts changed)
8. `done | blocked | needs_review`

## Task Card Template

```md
## Task: <short title>

- Task ID: TASK-YYYYMMDD-###
- Requested by: <name/role>
- Created at: <UTC datetime>
- Lead Agent: lead
- Current status: new|triaged|planning_gate|in_progress|in_review|qa_gate|docs_gate|done|blocked|needs_review

### Scope
- Goal:
- In scope:
- Out of scope:
- Constraints:

### Agent Assignment
1. <agent_id> - <reason>
2. <agent_id> - <reason>

### Execution Order
1. <agent_id> -> <action>
2. <agent_id> -> <action>

### Risks and Dependencies
- Risks:
- Dependencies:
- Blockers:

### Gates
- Planning required: yes|no
- Planning status: pending|approved|n/a
- QA required: yes
- QA status: pending|passed|failed
- Docs required: yes|no
- Docs status: pending|updated|n/a

### Deliverables
- Files/Artifacts changed:
- Contracts changed: yes|no
- Behavior changed: yes|no

### Final Resolution
- Final status: done|blocked|needs_review
- Summary:
- Next actions:
- Closed at: <UTC datetime>
```

## State Log Rules

- Every status change must include timestamp and actor.
- Every blocker must include owner and ETA.
- If `Planning required: yes`, moving to `in_progress` without `Planning status: approved` is not allowed.
- Closure without `QA status: passed` is not allowed.
- If behavior/contracts changed, closure without docs update is not allowed.

## Runtime Check Rules

- Use `scripts/wait-url.ps1` for service readiness checks.
- Default timeout for readiness probes is `20s`.
- Avoid manual polling loops with `1s` sleep unless explicitly needed for diagnostics.
- Use `scripts/run-regression.ps1` as the default end-to-end QA gate before moving a complex task to closure.
- Use `scripts/session-report.ps1` (or `npm run Отчет`) to generate a standardized end-of-session report in `docs/reports/`.
