# Alembic Migrations

This folder contains database migrations for the XPlain API.

## Commands

From `apps/api`:

```bash
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

Use `DATABASE_URL` from environment to target the correct database.
