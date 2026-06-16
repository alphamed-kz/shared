"""Align existing database tables with current client API models.

Revision ID: 20260616_2019
Revises: 9fe7951d61a0
Create Date: 2026-06-16 20:19:00.000000
"""
from __future__ import annotations

from alembic import op

revision = "20260616_2019"
down_revision = "9fe7951d61a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regtype('recordingstatus') IS NULL THEN
                CREATE TYPE recordingstatus AS ENUM (
                    'SAVED',
                    'TRANSCRIBING',
                    'TRANSCRIBED',
                    'ANALYZING',
                    'ANALYZED',
                    'FAILED'
                );
            END IF;
        END
        $$;
        """
    )

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS name text")
    op.execute("UPDATE devices SET name = 'Legacy pharmacy PC' WHERE name IS NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN name SET NOT NULL")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS location text")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS api_key_hash text")
    op.execute("UPDATE devices SET api_key_hash = '' WHERE api_key_hash IS NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN api_key_hash SET NOT NULL")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS license_key_hash text")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS machine_fingerprint_hash text")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS status text")
    op.execute("UPDATE devices SET status = 'active' WHERE status IS NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN status SET NOT NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN status SET DEFAULT 'active'")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS app_version text")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS revoked boolean")
    op.execute("UPDATE devices SET revoked = false WHERE revoked IS NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN revoked SET NOT NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN revoked SET DEFAULT false")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_heartbeat_at timestamptz")

    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS registered_at timestamptz")
    op.execute("UPDATE devices SET registered_at = now() WHERE registered_at IS NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN registered_at SET NOT NULL")
    op.execute("ALTER TABLE devices ALTER COLUMN registered_at SET DEFAULT now()")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS device_id uuid")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS s3_key text")
    op.execute("UPDATE recordings SET s3_key = filename WHERE s3_key IS NULL")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS recorded_at timestamptz")
    op.execute(
        "UPDATE recordings SET recorded_at = COALESCE(created_at, now()) WHERE recorded_at IS NULL"
    )
    op.execute("ALTER TABLE recordings ALTER COLUMN recorded_at SET NOT NULL")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS uploaded_at timestamptz")
    op.execute(
        "UPDATE recordings SET uploaded_at = COALESCE(created_at, now()) WHERE uploaded_at IS NULL"
    )
    op.execute("ALTER TABLE recordings ALTER COLUMN uploaded_at SET NOT NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN uploaded_at SET DEFAULT now()")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS status recordingstatus")
    op.execute("UPDATE recordings SET status = 'SAVED'::recordingstatus WHERE status IS NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN status SET NOT NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN status SET DEFAULT 'SAVED'::recordingstatus")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS locked_until timestamptz")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS retry_count integer")
    op.execute("UPDATE recordings SET retry_count = 0 WHERE retry_count IS NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN retry_count SET NOT NULL")
    op.execute("ALTER TABLE recordings ALTER COLUMN retry_count SET DEFAULT 0")

    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS error_message text")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS transcription text")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS transcribed_at timestamptz")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS is_rejection boolean")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS rejection_explanation text")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS possible_drug_name text")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS analysis text")
    op.execute("ALTER TABLE recordings ADD COLUMN IF NOT EXISTS analyzed_at timestamptz")

    op.execute("CREATE INDEX IF NOT EXISTS ix_recordings_status ON recordings (status)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_recordings_status")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS analyzed_at")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS analysis")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS possible_drug_name")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS rejection_explanation")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS is_rejection")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS transcribed_at")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS transcription")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS error_message")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS retry_count")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS locked_until")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS uploaded_at")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS recorded_at")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS s3_key")
    op.execute("ALTER TABLE recordings DROP COLUMN IF EXISTS device_id")

    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS registered_at")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_heartbeat_at")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS revoked")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS app_version")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS status")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS machine_fingerprint_hash")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS license_key_hash")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS api_key_hash")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS location")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS name")
