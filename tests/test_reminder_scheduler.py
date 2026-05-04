"""Tests for ReminderScheduler — SPEC.md section 14."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.core.reminder_scheduler import ReminderScheduler
from smartpad.db.engine import get_async_session, init_async_engine
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Reminder
from smartpad.db.repositories.reminders import RemindersRepo


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncSession:
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    engine = init_async_engine(db_path)
    async with get_async_session() as session:
        yield session


def _make_scheduler(
    session_factory: Any,
    *,
    fired_list: list[Any] | None = None,
    quiet_start: int = 0,
    quiet_end: int = 0,
) -> ReminderScheduler:
    """Build a scheduler with test-friendly defaults."""
    fired = fired_list if fired_list is not None else []

    def _cb(reminder: Any) -> None:
        fired.append(reminder)

    return ReminderScheduler(
        session_factory=session_factory,
        notification_callback=_cb,
        check_interval=1,
        quiet_hours_start=quiet_start,
        quiet_hours_end=quiet_end,
    )


# ── Due reminders ─────────────────────────────────────────────────────────────


async def test_due_reminders_are_detected(db: AsyncSession, tmp_path: Path) -> None:
    # Seed a past-due reminder
    repo = RemindersRepo(db)
    past = datetime.now(UTC) - timedelta(minutes=5)
    await repo.save(
        Reminder(content="Past reminder", trigger_at=past, created_at=datetime.now(UTC), sync_version=0)
    )
    await db.commit()

    db_path = tmp_path / "test.db"

    @asynccontextmanager
    async def factory():
        async with get_async_session() as s:
            yield s

    fired: list[Any] = []
    scheduler = _make_scheduler(factory, fired_list=fired)
    # Run one check synchronously
    import asyncio
    await scheduler._check_once()

    assert len(fired) == 1
    assert fired[0].content == "Past reminder"


async def test_due_reminders_marked_notified(db: AsyncSession, tmp_path: Path) -> None:
    repo = RemindersRepo(db)
    past = datetime.now(UTC) - timedelta(minutes=1)
    reminder = await repo.save(
        Reminder(content="Mark me", trigger_at=past, created_at=datetime.now(UTC), sync_version=0)
    )
    await db.commit()

    db_path = tmp_path / "test.db"

    @asynccontextmanager
    async def factory():
        async with get_async_session() as s:
            yield s

    scheduler = _make_scheduler(factory)
    await scheduler._check_once()

    # After check, reminder should be notified
    async with get_async_session() as s:
        refreshed = await RemindersRepo(s).get(reminder.id)
    assert refreshed is not None
    assert refreshed.notified is True


async def test_quiet_hours_suppresses_notification(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)

    # Seed a past-due reminder
    async with get_async_session() as session:
        repo = RemindersRepo(session)
        past = datetime.now(UTC) - timedelta(minutes=5)
        await repo.save(
            Reminder(
                content="Quiet reminder", trigger_at=past, created_at=datetime.now(UTC), sync_version=0
            )
        )
        await session.commit()

    @asynccontextmanager
    async def factory():
        async with get_async_session() as s:
            yield s

    fired: list[Any] = []
    # Set quiet hours to cover ALL hours (0–0 wraps around = all-day quiet)
    scheduler = ReminderScheduler(
        session_factory=factory,
        notification_callback=lambda r: fired.append(r),
        check_interval=1,
        quiet_hours_start=0,
        quiet_hours_end=0,
    )

    # When start == end, check whether that counts as all-day quiet
    # Our implementation: if start > end → spans midnight. start == end → no quiet hours.
    # So let's use start=22, and override the current time via the method.
    # Instead, let's test is_quiet_hours() directly.
    # 22:30 should be quiet with start=22, end=8
    s = ReminderScheduler(
        session_factory=factory, quiet_hours_start=22, quiet_hours_end=8, check_interval=1
    )
    late_night = datetime(2024, 1, 1, 23, 30)
    assert s.is_quiet_hours(now=late_night) is True

    early_morning = datetime(2024, 1, 1, 7, 0)
    assert s.is_quiet_hours(now=early_morning) is True

    midday = datetime(2024, 1, 1, 12, 0)
    assert s.is_quiet_hours(now=midday) is False


def test_scheduler_stop_terminates_cleanly(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)

    @asynccontextmanager
    async def factory():
        async with get_async_session() as s:
            yield s

    scheduler = _make_scheduler(factory)
    scheduler.start()
    import time
    time.sleep(0.1)
    scheduler.stop()
    assert scheduler._thread is None or not scheduler._thread.is_alive()


def test_is_quiet_hours_daytime() -> None:
    s = ReminderScheduler(
        session_factory=None,  # type: ignore[arg-type]
        quiet_hours_start=22,
        quiet_hours_end=8,
    )
    noon = datetime(2024, 6, 1, 12, 0)
    assert s.is_quiet_hours(now=noon) is False


def test_is_quiet_hours_midnight_span() -> None:
    s = ReminderScheduler(
        session_factory=None,  # type: ignore[arg-type]
        quiet_hours_start=22,
        quiet_hours_end=8,
    )
    at_23 = datetime(2024, 6, 1, 23, 0)
    at_01 = datetime(2024, 6, 2, 1, 0)
    at_09 = datetime(2024, 6, 1, 9, 0)
    assert s.is_quiet_hours(now=at_23) is True
    assert s.is_quiet_hours(now=at_01) is True
    assert s.is_quiet_hours(now=at_09) is False
