"""Tests for SearchService — SPEC.md section 7."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.core.search_service import SearchResult, search, search_personal_query
from smartpad.db.engine import get_async_session, init_async_engine
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Note, Reminder, Task
from smartpad.db.repositories.notes import NotesRepo
from smartpad.db.repositories.reminders import RemindersRepo
from smartpad.db.repositories.tasks import TasksRepo


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncSession:
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)
    async with get_async_session() as session:
        yield session


# ── FTS5 search ───────────────────────────────────────────────────────────────


async def test_fts_search_returns_correct_results(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    await repo.save(
        Note(
            content="python asyncio tutorial",
            original_content="python asyncio tutorial",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await repo.save(
        Note(
            content="completely unrelated topic",
            original_content="completely unrelated topic",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    results = await search("asyncio", db)
    assert len(results) == 1
    assert results[0].item_type == "note"
    assert "asyncio" in results[0].snippet


async def test_fts_search_empty_results(db: AsyncSession) -> None:
    results = await search("zzz_no_match_xyz", db)
    assert results == []


async def test_fts_search_empty_query(db: AsyncSession) -> None:
    results = await search("", db)
    assert results == []


async def test_fts_search_result_has_entity(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    note = await repo.save(
        Note(
            content="searchable content here",
            original_content="searchable content here",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    results = await search("searchable", db)
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].entity is not None
    assert results[0].entity.id == note.id


async def test_fts_search_snippet_max_100_chars(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    long_content = "findme " + ("x" * 200)
    await repo.save(
        Note(
            content=long_content,
            original_content=long_content,
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    results = await search("findme", db)
    assert len(results) == 1
    assert len(results[0].snippet) <= 100


# ── Personal queries ──────────────────────────────────────────────────────────


async def test_personal_query_tasks_today(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    now = datetime.now(UTC)
    today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    await repo.save(
        Task(
            content="Buy groceries",
            deadline=today_noon,
            created_at=now,
            sync_version=0,
        )
    )
    await db.commit()

    result = await search_personal_query("what tasks do I have today", db)
    assert "Buy groceries" in result


async def test_personal_query_tasks_today_empty(db: AsyncSession) -> None:
    result = await search_personal_query("what tasks do I have today", db)
    assert "no tasks" in result.lower()


async def test_personal_query_reminders_due(db: AsyncSession) -> None:
    repo = RemindersRepo(db)
    now = datetime.now(UTC)
    await repo.save(
        Reminder(
            content="Call dentist",
            trigger_at=now + timedelta(hours=2),
            created_at=now,
            sync_version=0,
        )
    )
    await db.commit()

    result = await search_personal_query("any reminders due today", db)
    assert "Call dentist" in result


async def test_personal_query_empty_reminders(db: AsyncSession) -> None:
    result = await search_personal_query("any reminders due", db)
    assert "no reminder" in result.lower() or "0 reminder" in result.lower()


async def test_personal_query_general_task_list(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    now = datetime.now(UTC)
    await repo.save(Task(content="Write report", created_at=now, sync_version=0))
    await db.commit()

    result = await search_personal_query("show my tasks", db)
    assert "Write report" in result


async def test_personal_query_fallback_fts(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    await repo.save(
        Note(
            content="unique_term_xyz special note",
            original_content="unique_term_xyz special note",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    # This query doesn't match any personal-query pattern, falls back to FTS
    result = await search_personal_query("unique_term_xyz", db)
    assert "unique_term_xyz" in result or "1 result" in result
