"""Store recording status as text instead of a PostgreSQL enum.

Revision ID: 20260621_1219
Revises: 20260616_2059
Create Date: 2026-06-21 12:19:00.000000
"""
from __future__ import annotations

from alembic import op

from shared.config import settings

revision = "20260621_1219"
down_revision = "20260616_2059"
branch_labels = None
depends_on = None


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _qualified(name: str) -> str:
    schema = settings.db_schema.strip()
    if not schema:
        return _quote_identifier(name)
    return f"{_quote_identifier(schema)}.{_quote_identifier(name)}"


def upgrade() -> None:
    recordings = _qualified("recordings")
    recordingstatus = _qualified("recordingstatus")

    op.execute(f"ALTER TABLE {recordings} ALTER COLUMN status DROP DEFAULT")
    op.execute(f"ALTER TABLE {recordings} ALTER COLUMN status TYPE text USING status::text")
    op.execute(f"ALTER TABLE {recordings} ALTER COLUMN status SET DEFAULT 'SAVED'")
    op.execute(f"DROP TYPE IF EXISTS {recordingstatus}")


def downgrade() -> None:
    recordings = _qualified("recordings")
    recordingstatus = _qualified("recordingstatus")

    op.execute(
        f"""
        CREATE TYPE {recordingstatus} AS ENUM (
            'SAVED',
            'TRANSCRIBING',
            'TRANSCRIBED',
            'ANALYZING',
            'ANALYZED',
            'FAILED'
        )
        """
    )
    op.execute(f"ALTER TABLE {recordings} ALTER COLUMN status DROP DEFAULT")
    op.execute(
        f"ALTER TABLE {recordings} ALTER COLUMN status TYPE {recordingstatus} USING status::{recordingstatus}"
    )
    op.execute(f"ALTER TABLE {recordings} ALTER COLUMN status SET DEFAULT 'SAVED'::{recordingstatus}")
