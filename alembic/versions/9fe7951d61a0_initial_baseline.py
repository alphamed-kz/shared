"""Initial baseline schema.

Revision ID: 9fe7951d61a0
Revises:
Create Date: 2026-06-16 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9fe7951d61a0"
down_revision = None
branch_labels = None
depends_on = None


recording_status = postgresql.ENUM(
    "SAVED",
    "TRANSCRIBING",
    "TRANSCRIBED",
    "ANALYZING",
    "ANALYZED",
    "FAILED",
    name="recordingstatus",
    create_type=False,
)


def upgrade() -> None:
    recording_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "devices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("api_key_hash", sa.Text(), nullable=False),
        sa.Column("license_key_hash", sa.Text(), nullable=True),
        sa.Column("machine_fingerprint_hash", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("app_version", sa.Text(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recordings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("s3_key", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("duration_s", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", recording_status, nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("transcribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_rejection", sa.Boolean(), nullable=True),
        sa.Column("rejection_explanation", sa.Text(), nullable=True),
        sa.Column("possible_drug_name", sa.Text(), nullable=True),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recordings_status", "recordings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_recordings_status", table_name="recordings")
    op.drop_table("recordings")
    op.drop_table("devices")
    recording_status.drop(op.get_bind(), checkfirst=True)
