# AlphaMed Shared Database

This package owns the shared SQLAlchemy models and Alembic migrations for production services.
Alembic stores its version table in `DB_SCHEMA` (`alphamed` by default) as
`alphamed.alembic_version`, so it does not collide with other projects that share the same database.

## Existing Production Database

The initial migration represents the schema that already exists in production. For an existing
database, do not run `upgrade` first. Mark it as already applied:

```bash
cd alphamed_prod/shared
uv sync --group migration
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB uv run alembic stamp 9fe7951d61a0
```

If an older run created `public.alembic_version`, leave it alone until you know no other project uses
it. The AlphaMed migration state now lives in `alphamed.alembic_version`.

After stamping, future migrations can be applied normally:

```bash
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB uv run alembic upgrade head
```

For a new empty database, run:

```bash
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB uv run alembic upgrade head
```

The migration currently matches the ORM models' default-schema tables: `devices`, `recordings`, and
the PostgreSQL enum `recordingstatus`.

`DATABASE_URL` may be provided as `postgres://...`, `postgresql://...`, or
`postgresql+asyncpg://...`; shared config normalizes it to the async SQLAlchemy driver.
