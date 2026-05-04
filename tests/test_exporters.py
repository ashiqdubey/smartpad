"""Tests for export utilities — SPEC.md section 20."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.engine import get_async_session, init_async_engine
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Note, Task
from smartpad.db.repositories.notes import NotesRepo
from smartpad.db.repositories.tasks import TasksRepo
from smartpad.utils.exporters import export_all, export_notes, export_tasks


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncSession:
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)
    async with get_async_session() as session:
        yield session


# ── export_notes ──────────────────────────────────────────────────────────────


async def test_markdown_export_contains_content(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    await repo.save(
        Note(
            content="This is a note about pandas",
            original_content="This is a note about pandas",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    result = await export_notes(db, fmt="markdown")
    assert "pandas" in result
    assert "Note" in result or "note" in result.lower()


async def test_json_export_is_valid_json(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    await repo.save(
        Note(
            content="JSON test note",
            original_content="JSON test note",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    result = await export_notes(db, fmt="json")
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["content"] == "JSON test note"


async def test_export_notes_empty_returns_valid_structure(db: AsyncSession) -> None:
    result_md = await export_notes(db, fmt="markdown")
    assert isinstance(result_md, str)

    result_json = await export_notes(db, fmt="json")
    parsed = json.loads(result_json)
    assert isinstance(parsed, list)
    assert len(parsed) == 0


async def test_export_notes_date_filter(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    now = datetime.now(UTC)
    old = now - timedelta(days=10)
    recent = now - timedelta(days=1)

    await repo.save(
        Note(
            content="Old note",
            original_content="Old note",
            created_at=old,
            sync_version=0,
        )
    )
    await repo.save(
        Note(
            content="Recent note",
            original_content="Recent note",
            created_at=recent,
            sync_version=0,
        )
    )
    await db.commit()

    # Only export notes from last 5 days
    cutoff = now - timedelta(days=5)
    result = await export_notes(db, fmt="json", date_from=cutoff)
    parsed = json.loads(result)
    assert len(parsed) == 1
    assert parsed[0]["content"] == "Recent note"


# ── export_tasks ──────────────────────────────────────────────────────────────


async def test_export_tasks_markdown(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    await repo.save(Task(content="Write tests", created_at=datetime.now(UTC), sync_version=0))
    await db.commit()

    result = await export_tasks(db, fmt="markdown")
    assert "Write tests" in result


async def test_export_tasks_json(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    await repo.save(Task(content="Deploy app", created_at=datetime.now(UTC), sync_version=0))
    await db.commit()

    result = await export_tasks(db, fmt="json")
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert any(t["content"] == "Deploy app" for t in parsed)


async def test_export_tasks_status_filter(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    t1 = await repo.save(
        Task(content="Todo item", created_at=datetime.now(UTC), sync_version=0)
    )
    t2 = await repo.save(
        Task(content="Done item", created_at=datetime.now(UTC), sync_version=0)
    )
    await repo.mark_done(t2.id)
    await db.commit()

    result = await export_tasks(db, fmt="json", status="todo")
    parsed = json.loads(result)
    assert all(t["status"] == "todo" for t in parsed)
    contents = [t["content"] for t in parsed]
    assert "Todo item" in contents
    assert "Done item" not in contents


# ── export_all ────────────────────────────────────────────────────────────────


async def test_export_all_markdown(db: AsyncSession) -> None:
    notes_repo = NotesRepo(db)
    tasks_repo = TasksRepo(db)
    await notes_repo.save(
        Note(
            content="A note",
            original_content="A note",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await tasks_repo.save(
        Task(content="A task", created_at=datetime.now(UTC), sync_version=0)
    )
    await db.commit()

    result = await export_all(db, fmt="markdown")
    assert "A note" in result
    assert "A task" in result


async def test_export_all_json(db: AsyncSession) -> None:
    notes_repo = NotesRepo(db)
    await notes_repo.save(
        Note(
            content="Export all test",
            original_content="Export all test",
            created_at=datetime.now(UTC),
            sync_version=0,
        )
    )
    await db.commit()

    result = await export_all(db, fmt="json")
    parsed = json.loads(result)
    assert "notes" in parsed
    assert isinstance(parsed["notes"], list)
    assert any(n["content"] == "Export all test" for n in parsed["notes"])


async def test_export_all_empty_returns_valid(db: AsyncSession) -> None:
    result_json = await export_all(db, fmt="json")
    parsed = json.loads(result_json)
    assert "notes" in parsed
    assert "tasks" in parsed

    result_md = await export_all(db, fmt="markdown")
    assert isinstance(result_md, str)
