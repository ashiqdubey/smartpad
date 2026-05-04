"""Reminder scheduler — SPEC.md section 14.

Background thread that checks for due reminders every 30 seconds.
Core logic is pure Python (no PyQt imports). A Qt wrapper may be
added in ui/ as a thin shim.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from loguru import logger


class ReminderScheduler:
    """Polls for due reminders and fires a callback for each one.

    Usage::

        def on_reminder(reminder):
            print("Due:", reminder.content)

        scheduler = ReminderScheduler(
            session_factory=my_session_factory,
            notification_callback=on_reminder,
        )
        scheduler.start()
        # ... later ...
        scheduler.stop()

    Args:
        session_factory: Async context-manager factory returning an AsyncSession.
        notification_callback: Called with each due Reminder ORM object.
        check_interval: Seconds between checks (default 30).
        quiet_hours_start: Hour (24h) when quiet hours begin (default 22).
        quiet_hours_end: Hour (24h) when quiet hours end (default 8).
    """

    def __init__(
        self,
        *,
        session_factory: Any,
        notification_callback: Callable[[Any], None] | None = None,
        check_interval: int = 30,
        quiet_hours_start: int = 22,
        quiet_hours_end: int = 8,
    ) -> None:
        self._session_factory = session_factory
        self._notification_callback = notification_callback
        self._check_interval = check_interval
        self._quiet_hours_start = quiet_hours_start
        self._quiet_hours_end = quiet_hours_end

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # For test inspection — fired reminders accumulate here
        self.fired: list[Any] = []

    # ── lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("ReminderScheduler already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="ReminderScheduler",
        )
        self._thread.start()
        logger.info("ReminderScheduler started (interval={}s).", self._check_interval)

    def stop(self) -> None:
        """Signal the polling thread to stop and wait for it to terminate."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._check_interval + 5)
            if self._thread.is_alive():
                logger.warning("ReminderScheduler thread did not stop cleanly.")
            else:
                logger.info("ReminderScheduler stopped.")
        self._thread = None

    # ── internal ──────────────────────────────────────────────────────────────

    def _run_loop(self) -> None:
        """Main thread loop — runs an asyncio event loop per iteration."""
        while not self._stop_event.is_set():
            try:
                asyncio.run(self._check_once())
            except Exception as exc:  # noqa: BLE001
                logger.error("ReminderScheduler check error: {}", exc)
            # Wait for interval or until stop is requested
            self._stop_event.wait(timeout=self._check_interval)

    async def _check_once(self) -> None:
        """Single polling cycle — fetch due reminders and fire callbacks."""
        if self.is_quiet_hours():
            logger.debug("ReminderScheduler: quiet hours, skipping check.")
            return

        from smartpad.db.repositories.reminders import RemindersRepo  # lazy import

        async with self._session_factory() as session:
            repo = RemindersRepo(session)
            due = await repo.get_due(as_of=datetime.now(UTC))
            for reminder in due:
                logger.info("Reminder due: id={} content={!r}", reminder.id, reminder.content)
                self.fired.append(reminder)
                if self._notification_callback is not None:
                    try:
                        self._notification_callback(reminder)
                    except Exception as exc:  # noqa: BLE001
                        logger.error("Notification callback error: {}", exc)
                # Mark as notified
                await repo.mark_notified(reminder.id)
            await session.commit()

    def is_quiet_hours(self, *, now: datetime | None = None) -> bool:
        """Return True if current local time falls within quiet hours."""
        local_now = (now or datetime.now()).replace(tzinfo=None)
        hour = local_now.hour
        start = self._quiet_hours_start
        end = self._quiet_hours_end
        if start > end:
            # Spans midnight (e.g. 22 – 8)
            return hour >= start or hour < end
        return start <= hour < end

    def check_once_sync(self) -> list[Any]:
        """Synchronous helper for tests — runs one check and returns fired list.

        Returns:
            List of Reminder objects that fired this cycle.
        """
        before = len(self.fired)
        asyncio.run(self._check_once())
        return self.fired[before:]
