# Release Readiness Checklist

This checklist is the baseline gate for marking a delivery as release-ready.

## Single-Command Regression

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-regression.ps1
```

Shortcut:

```powershell
npm run qa:regression
```

Optional fast mode (skip web production build):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run-regression.ps1 -SkipWebBuild
```

## Required Pass Criteria

1. Docker stack is up (`postgres`, `redis`, `api`, `web`).
2. Readiness checks are `UP`:
   - `http://localhost:8000/health`
   - `http://localhost:3000`
3. API migration head is applied (`alembic current` equals latest revision).
4. API contract tests pass (`pytest tests -q`).
5. Frontend checks pass:
   - `npm run lint:web`
   - `npm run build --workspace @xplain/web` (unless explicitly skipped for local fast sweep)
6. Integration smoke scenario passes end-to-end:
   - process create
   - graph generation
   - revision list
   - comments on process/node/edge
   - status transition `draft -> in_review`
   - locked graph generation returns `409 process_locked`

## Release Decision

- `PASS`: all required criteria above pass in one run.
- `FAIL`: any step fails; release is blocked until remediation and rerun.
