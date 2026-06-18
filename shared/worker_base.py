"""Abstract base class for PostgreSQL-polling workers.

Pattern:
  SELECT id FROM recordings
  WHERE  status = :target AND (locked_until IS NULL OR locked_until < NOW())
  ORDER  BY recorded_at ASC
  LIMIT  1
  FOR UPDATE SKIP LOCKED;

Each worker subclass declares which status it polls for and implements process().
"""
from __future__ import annotations

import asyncio
import logging
import signal
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from shared.db import AsyncSessionLocal
from shared.models import Recording

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3


class AbstractWorker(ABC):
    """Poll the recordings table and process one row at a time.

    Subclasses must implement:
      - target_status()      the RecordingStatus value to poll for
      - in_progress_status() the RecordingStatus value set when claiming
      - lock_minutes()       how long locked_until is set (minutes)
      - process(row_id)      business logic for this worker
    """

    def __init__(self, poll_interval: float = 3.0) -> None:
        self.poll_interval = poll_interval
        self._running = False

    @abstractmethod
    def target_status(self) -> str: ...

    @abstractmethod
    def in_progress_status(self) -> str: ...

    @abstractmethod
    def lock_minutes(self) -> int: ...

    @abstractmethod
    async def process(self, row_id: uuid.UUID) -> None:
        """Process a single claimed recording. Raise on failure — caller handles retry."""
        ...

    async def run(self) -> None:
        """Main polling loop. Blocks until SIGTERM/SIGINT."""
        self._running = True
        self._install_signal_handlers()
        logger.info(
            "%s started — polling for status=%s every %.1fs",
            self.__class__.__name__,
            self.target_status(),
            self.poll_interval,
        )
        while self._running:
            try:
                claimed = await self._claim_next()
                if claimed:
                    await self._run_process(claimed)
                else:
                    await asyncio.sleep(self.poll_interval)
            except Exception:
                logger.exception("Unexpected error in polling loop")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        logger.info("%s stopping after current item.", self.__class__.__name__)

    # ------------------------------------------------------------------
    # Internal — implemented in Task 5
    # ------------------------------------------------------------------

    async def _claim_next(self) -> uuid.UUID | None:
        """Atomically claim the oldest unclaimed row for this worker's target status.

        Returns the row id if claimed, None if the queue is empty.
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(Recording)
                    .where(
                        Recording.status == self.target_status(),
                        (
                            Recording.locked_until.is_(None)
                            | (Recording.locked_until < datetime.now(timezone.utc))
                        ),
                    )
                    .order_by(Recording.recorded_at.asc())
                    .limit(1)
                    .with_for_update(skip_locked=True)
                )
                recording = result.scalar_one_or_none()
                if recording is None:
                    return None

                recording.status = self.in_progress_status()
                recording.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=self.lock_minutes()
                )
                session.add(recording)
                logger.info(
                    "Claimed recording %s: %s -> %s",
                    recording.id,
                    self.target_status(),
                    self.in_progress_status(),
                )
                return recording.id

    async def _run_process(self, row_id: uuid.UUID) -> None:
        """Call process(), update status on success, handle failure.

        The concrete process() implementation is responsible for setting the
        success status. On failure, leave the in-progress status and lock in
        place so the reaper/lock expiry policy can retry or fail the row.
        """
        try:
            await self.process(row_id)
        except Exception as exc:
            async with AsyncSessionLocal() as session:
                recording = await session.get(Recording, row_id)
                if recording is not None:
                    recording.error_message = str(exc)
                    session.add(recording)
                    await session.commit()
            logger.exception("Processing recording %s failed", row_id)
            return

        logger.info("Processed recording %s", row_id)

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
