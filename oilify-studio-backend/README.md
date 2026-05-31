## Database Migrations

This backend now uses Alembic for schema changes.

From the backend directory:

```bash
uv run alembic upgrade head
```

For an existing database that was previously created with `Base.metadata.create_all`, you may need to run the first upgrade once, then use Alembic for all future schema changes.

