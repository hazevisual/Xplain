# Session Report System

## Goal

Standardize per-session reporting using a single command and a fixed markdown structure.

## Trigger Command

- Primary: `npm run report:session`
- Alias: `npm run Отчет`

Both commands generate a report file in `docs/reports/`.

## Optional Parameters

You can pass script params after `--`:

```powershell
npm run report:session -- -TaskId TASK-20260306-007 -Since "2026-03-06 00:00:00"
```

Supported params:

- `-TaskId` - bind report to task card.
- `-Since` - start of reporting window for commit/file aggregation.
- `-CommandLabel` - override command label (default: `Отчет`).
- `-OutputPath` - custom output path (default: `docs/reports/SESSION-YYYYMMDD-HHMMSS.md`).

Default reporting window:

- if previous `SESSION-*.md` exists -> from the latest report timestamp;
- otherwise -> from local day start (`00:00:00`).

## Report Structure

Generated report includes:

1. Session metadata (time, branch, HEAD, task, window start).
2. Manual sections:
   - Summary
   - Completed
   - In Progress
   - Risks / Blockers
   - Validation
   - Next Actions
3. Auto sections:
   - Commits in window
   - Files changed in window
   - Working tree snapshot

## Team Rule

At the end of each work session, run `Отчет` command and commit the generated file under `docs/reports/`.
