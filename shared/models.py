"""SQLAlchemy ORM models shared across all server components.

Two tables (schema controlled by DB_SCHEMA env var, default "alphamed"):
  devices    — registered pharmacy PCs with hashed API keys
  recordings — one row per audio utterance, drives the worker pipeline via status
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, Boolean, DateTime, Float, Integer, MetaData, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from shared.config import settings


class RecordingStatus(str, enum.Enum):
    SAVED = "SAVED"
    TRANSCRIBING = "TRANSCRIBING"
    TRANSCRIBED = "TRANSCRIBED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.db_schema or None)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_hash: Mapped[str] = mapped_column(Text, nullable=False)
    license_key_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    machine_fingerprint_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    app_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    # recorded_at is parsed from the filename timestamp — accurate even during offline periods
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status: Mapped[RecordingStatus] = mapped_column(
        SAEnum(
            RecordingStatus,
            name="recordingstatus",
            schema=settings.db_schema or None,
        ),
        nullable=False,
        default=RecordingStatus.SAVED,
        index=True,
    )
    # Set when a worker claims the row; reaper resets rows where locked_until < NOW()
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Populated by TranscriptionWorker
    transcription: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Populated by LLMWorker
    is_rejection: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rejection_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    possible_drug_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
