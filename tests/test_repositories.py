"""Integration tests: all repositories — CRUD, soft-delete, sync fields, FTS5."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.engine import init_async_engine, get_async_session
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Book, Message, Note, Provider, Reminder, Setting, Snippet, Task
from smartpad.db.repositories.books import BooksRepo
from smartpad.db.repositories.chat import ChatRepo
from smartpad.db.repositories.notes import NotesRepo
from smartpad.db.repositories.providers import ProvidersRepo
from smartpad.db.repositories.reminders import RemindersRepo
from smartpad.db.repositories.settings import SettingsRepo
from smartpad.db.repositories.snippets import SnippetsRepo
from smartpad.db.repositories.tasks import TasksRepo


@pytest_asyncio.fixture
async def db(tmp_path: Path) -> AsyncSession:
    """Fresh migrated DB + async session for each test."""
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)
    async with get_async_session() as session:
        yield session


# ── Notes ─────────────────────────────────────────────────────────────────────

async def test_notes_save_and_get(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    note = Note(
        content="Hello world",
        original_content="Hello world",
        created_at=datetime.now(UTC),
        sync_version=0,
    )
    saved = await repo.save(note)
    assert saved.id is not None
    assert saved.sync_version == 1
    assert saved.updated_at is not None

    fetched = await repo.get(saved.id)
    assert fetched is not None
    assert fetched.content == "Hello world"


async def test_notes_list_filters(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    n1 = await repo.save(Note(content="A", original_content="A", created_at=datetime.now(UTC), pinned=True, sync_version=0))
    n2 = await repo.save(Note(content="B", original_content="B", created_at=datetime.now(UTC), pinned=False, sync_version=0))

    pinned = await repo.list(pinned=True)
    assert any(n.id == n1.id for n in pinned)
    assert all(n.pinned for n in pinned)

    all_notes = await repo.list()
    ids = {n.id for n in all_notes}
    assert n1.id in ids and n2.id in ids


async def test_notes_soft_delete(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    note = await repo.save(Note(content="bye", original_content="bye", created_at=datetime.now(UTC), sync_version=0))
    deleted = await repo.soft_delete(note.id)
    assert deleted is True

    # Must not appear in active list
    active = await repo.list()
    assert not any(n.id == note.id for n in active)

    # Must still exist when include_deleted=True
    all_notes = await repo.list(include_deleted=True)
    found = next((n for n in all_notes if n.id == note.id), None)
    assert found is not None
    assert found.deleted_at is not None


async def test_notes_soft_delete_idempotent(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    note = await repo.save(Note(content="x", original_content="x", created_at=datetime.now(UTC), sync_version=0))
    assert await repo.soft_delete(note.id) is True
    assert await repo.soft_delete(note.id) is False


async def test_notes_fts_search(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    await repo.save(Note(content="python asyncio coroutine", original_content="python asyncio coroutine", created_at=datetime.now(UTC), sync_version=0))
    await repo.save(Note(content="unrelated topic here", original_content="unrelated topic here", created_at=datetime.now(UTC), sync_version=0))
    await db.commit()

    results = await repo.search("asyncio")
    assert len(results) == 1
    assert "asyncio" in results[0].content


async def test_notes_fts_removed_on_soft_delete(db: AsyncSession) -> None:
    repo = NotesRepo(db)
    note = await repo.save(Note(content="searchable text", original_content="searchable text", created_at=datetime.now(UTC), sync_version=0))
    await db.commit()
    assert len(await repo.search("searchable")) == 1
    await repo.soft_delete(note.id)
    await db.commit()
    assert len(await repo.search("searchable")) == 0


# ── Tasks ─────────────────────────────────────────────────────────────────────

async def test_tasks_save_and_get(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    task = Task(content="Buy milk", created_at=datetime.now(UTC), sync_version=0)
    saved = await repo.save(task)
    assert saved.status == "todo"
    assert saved.sync_version == 1

    fetched = await repo.get(saved.id)
    assert fetched is not None
    assert fetched.content == "Buy milk"


async def test_tasks_mark_done(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    task = await repo.save(Task(content="Finish report", created_at=datetime.now(UTC), sync_version=0))
    done = await repo.mark_done(task.id)
    assert done is not None
    assert done.status == "done"
    assert done.completed_at is not None


async def test_tasks_list_by_status(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    t1 = await repo.save(Task(content="Todo task", created_at=datetime.now(UTC), sync_version=0))
    t2 = await repo.save(Task(content="Done task", created_at=datetime.now(UTC), sync_version=0))
    await repo.mark_done(t2.id)

    todos = await repo.list(status="todo")
    assert any(t.id == t1.id for t in todos)
    assert not any(t.id == t2.id for t in todos)


async def test_tasks_soft_delete(db: AsyncSession) -> None:
    repo = TasksRepo(db)
    task = await repo.save(Task(content="Delete me", created_at=datetime.now(UTC), sync_version=0))
    assert await repo.soft_delete(task.id) is True
    active = await repo.list()
    assert not any(t.id == task.id for t in active)


# ── Reminders ─────────────────────────────────────────────────────────────────

async def test_reminders_save_and_get(db: AsyncSession) -> None:
    repo = RemindersRepo(db)
    trigger = datetime.now(UTC) + timedelta(hours=1)
    reminder = Reminder(content="Call dentist", trigger_at=trigger, created_at=datetime.now(UTC), sync_version=0)
    saved = await repo.save(reminder)
    assert saved.notified is False
    assert saved.sync_version == 1


async def test_reminders_get_due(db: AsyncSession) -> None:
    repo = RemindersRepo(db)
    past = datetime.now(UTC) - timedelta(minutes=5)
    future = datetime.now(UTC) + timedelta(hours=2)
    await repo.save(Reminder(content="Past reminder", trigger_at=past, created_at=datetime.now(UTC), sync_version=0))
    await repo.save(Reminder(content="Future reminder", trigger_at=future, created_at=datetime.now(UTC), sync_version=0))

    due = await repo.get_due()
    assert len(due) == 1
    assert due[0].content == "Past reminder"


async def test_reminders_mark_notified(db: AsyncSession) -> None:
    repo = RemindersRepo(db)
    past = datetime.now(UTC) - timedelta(minutes=1)
    reminder = await repo.save(Reminder(content="Do thing", trigger_at=past, created_at=datetime.now(UTC), sync_version=0))
    notified = await repo.mark_notified(reminder.id)
    assert notified is not None
    assert notified.notified is True
    assert notified.notified_at is not None
    # Must not appear in due list
    assert len(await repo.get_due()) == 0


async def test_reminders_soft_delete(db: AsyncSession) -> None:
    repo = RemindersRepo(db)
    future = datetime.now(UTC) + timedelta(days=1)
    reminder = await repo.save(Reminder(content="Future", trigger_at=future, created_at=datetime.now(UTC), sync_version=0))
    assert await repo.soft_delete(reminder.id) is True
    assert len(await repo.list()) == 0


# ── Snippets ──────────────────────────────────────────────────────────────────

async def test_snippets_save_and_get(db: AsyncSession) -> None:
    repo = SnippetsRepo(db)
    snippet = Snippet(content="git log --oneline", language="bash", created_at=datetime.now(UTC), sync_version=0)
    saved = await repo.save(snippet)
    assert saved.use_count == 0
    assert saved.sync_version == 1


async def test_snippets_increment_use_count(db: AsyncSession) -> None:
    repo = SnippetsRepo(db)
    snippet = await repo.save(Snippet(content="ls -la", language="bash", created_at=datetime.now(UTC), sync_version=0))
    updated = await repo.increment_use_count(snippet.id)
    assert updated is not None
    assert updated.use_count == 1
    assert updated.last_used_at is not None


async def test_snippets_list_by_language(db: AsyncSession) -> None:
    repo = SnippetsRepo(db)
    await repo.save(Snippet(content="print(1)", language="python", created_at=datetime.now(UTC), sync_version=0))
    await repo.save(Snippet(content="echo hi", language="bash", created_at=datetime.now(UTC), sync_version=0))

    py = await repo.list(language="python")
    assert all(s.language == "python" for s in py)
    assert len(py) == 1


async def test_snippets_search(db: AsyncSession) -> None:
    repo = SnippetsRepo(db)
    await repo.save(Snippet(content="kubectl get pods", description="list k8s pods", language="bash", created_at=datetime.now(UTC), sync_version=0))
    await repo.save(Snippet(content="unrelated", description="nothing", language="bash", created_at=datetime.now(UTC), sync_version=0))
    await db.commit()

    results = await repo.search("kubectl")
    assert len(results) == 1


async def test_snippets_soft_delete(db: AsyncSession) -> None:
    repo = SnippetsRepo(db)
    snippet = await repo.save(Snippet(content="gone", language="bash", created_at=datetime.now(UTC), sync_version=0))
    assert await repo.soft_delete(snippet.id) is True
    assert len(await repo.list()) == 0


# ── Books ─────────────────────────────────────────────────────────────────────

async def test_books_get_or_create(db: AsyncSession) -> None:
    repo = BooksRepo(db)
    book1 = await repo.get_or_create("Work")
    book2 = await repo.get_or_create("Work")
    assert book1.id == book2.id  # Same book returned


async def test_books_list_and_soft_delete(db: AsyncSession) -> None:
    repo = BooksRepo(db)
    b = await repo.save(Book(name="Personal", created_at=datetime.now(UTC), sync_version=0))
    assert len(await repo.list()) >= 1
    assert await repo.soft_delete(b.id) is True
    active = [bk for bk in await repo.list() if bk.id == b.id]
    assert len(active) == 0


async def test_books_sync_version_increments(db: AsyncSession) -> None:
    repo = BooksRepo(db)
    book = await repo.save(Book(name="First save", created_at=datetime.now(UTC), sync_version=0))
    v1 = book.sync_version
    book.name = "Updated"
    book2 = await repo.save(book)
    assert book2.sync_version == v1 + 1


# ── Chat ──────────────────────────────────────────────────────────────────────

async def test_chat_save_and_get(db: AsyncSession) -> None:
    repo = ChatRepo(db)
    msg = Message(role="user", content="Hello", kind="chat", created_at=datetime.now(UTC), sync_version=0)
    saved = await repo.save(msg)
    fetched = await repo.get(saved.id)
    assert fetched is not None
    assert fetched.content == "Hello"


async def test_chat_get_conversation_order(db: AsyncSession) -> None:
    repo = ChatRepo(db)
    t0 = datetime.now(UTC)
    await repo.save(Message(role="user", content="first", kind="chat", created_at=t0, sync_version=0))
    await repo.save(Message(role="assistant", content="second", kind="chat", created_at=t0 + timedelta(seconds=1), sync_version=0))
    await repo.save(Message(role="user", content="third", kind="chat", created_at=t0 + timedelta(seconds=2), sync_version=0))

    conv = await repo.get_conversation()
    assert conv[0].content == "first"
    assert conv[-1].content == "third"


async def test_chat_soft_delete(db: AsyncSession) -> None:
    repo = ChatRepo(db)
    msg = await repo.save(Message(role="user", content="bye", kind="chat", created_at=datetime.now(UTC), sync_version=0))
    assert await repo.soft_delete(msg.id) is True
    active = await repo.list()
    assert not any(m.id == msg.id for m in active)


# ── Providers ─────────────────────────────────────────────────────────────────

async def test_providers_set_active(db: AsyncSession) -> None:
    repo = ProvidersRepo(db)
    p1 = await repo.save(Provider(name="openai", type="OpenAICompatibleProvider", is_active=False, enabled=True, created_at=datetime.now(UTC)))
    p2 = await repo.save(Provider(name="local", type="ManagedLocalProvider", is_active=False, enabled=True, created_at=datetime.now(UTC)))

    active = await repo.set_active(p1.id)
    assert active is not None
    assert active.is_active is True

    # Set second as active; first must become inactive
    await repo.set_active(p2.id)
    p1_refetch = await repo.get(p1.id)
    assert p1_refetch is not None
    assert p1_refetch.is_active is False

    current = await repo.get_active()
    assert current is not None
    assert current.id == p2.id


async def test_providers_hard_delete(db: AsyncSession) -> None:
    repo = ProvidersRepo(db)
    p = await repo.save(Provider(name="temp", type="OpenAICompatibleProvider", created_at=datetime.now(UTC)))
    assert await repo.delete(p.id) is True
    assert await repo.get(p.id) is None


# ── Settings ──────────────────────────────────────────────────────────────────

async def test_settings_set_and_get(db: AsyncSession) -> None:
    repo = SettingsRepo(db)
    await repo.set("ai_level", 2)
    val = await repo.get("ai_level")
    assert val == 2


async def test_settings_upsert(db: AsyncSession) -> None:
    repo = SettingsRepo(db)
    await repo.set("theme", "dark")
    await repo.set("theme", "light")
    val = await repo.get("theme")
    assert val == "light"


async def test_settings_get_all(db: AsyncSession) -> None:
    repo = SettingsRepo(db)
    await repo.set("a", 1)
    await repo.set("b", 2)
    all_settings = await repo.get_all()
    assert all_settings["a"] == 1
    assert all_settings["b"] == 2


async def test_settings_delete(db: AsyncSession) -> None:
    repo = SettingsRepo(db)
    await repo.set("temp_key", "value")
    assert await repo.delete("temp_key") is True
    assert await repo.get("temp_key") is None
    assert await repo.delete("temp_key") is False  # idempotent
