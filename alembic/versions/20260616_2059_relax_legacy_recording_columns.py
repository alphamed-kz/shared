"""Relax legacy recording columns for S3-backed ingest.

Revision ID: 20260616_2059
Revises: 20260616_2019
Create Date: 2026-06-16 20:59:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "20260616_2059"
down_revision = "20260616_2019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE recordings ALTER COLUMN audio_data DROP NOT NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN created_at DROP NOT NULL")


def downgrade() -> None:
    op.execute("UPDATE recordings SET audio_data = ''::bytea WHERE audio_data IS NULL")
    op.execute("UPDATE recordings SET created_at = uploaded_at WHERE created_at IS NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN audio_data SET NOT NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN created_at SET NOT NULL")
