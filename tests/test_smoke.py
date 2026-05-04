"""Smoke tests: import, DB creation, migrations, basic CRUD, FTS5."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

import smartpad
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Message


def test_import() -> None:
    assert smartpad is not None


def test_migrations_run(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    run_migrations(db)
    assert db.exists()


def test_tables_exist(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    run_migrations(db)

    engine = create_engine(f"sqlite:///{db}")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected = {
        "messages", "notes", "tasks", "reminders",
        "snippets", "books", "providers", "settings", "paired_devices",
    }
    assert expected.issubset(tables)


def test_fts5_table_exists(tmp_path: Path) -> None:
    db = tmp_path / "test.db"
    run_migrations(db)

    engine = create_engine(f"sqlite:///{db}")
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='search_index'")
        )
        row = result.fetchone()
    assert row is not None, "search_index FTS5 table not found"


def test_insert_and_read_message(tmp_path: Path) -> None:
    from datetime import datetime, timezone

    db = tmp_path / "test.db"
    run_migrations(db)

    from smartpad.db.engine import init_engine, get_session

    init_engine(db)

    msg_id = "test-message-001"
    with get_session() as session:
        msg = Message(
            id=msg_id,
            role="user",
            content="Hello, SmartPad!",
            kind="chat",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(msg)

    with get_session() as session:
        from sqlalchemy import select

        found = session.execute(select(Message).where(Message.id == msg_id)).scalar_one()
        assert found.content == "Hello, SmartPad!"
        assert found.role == "user"
        assert found.kind == "chat"


def test_main_prints(capsys: pytest.CaptureFixture[str]) -> None:
    from smartpad.__main__ import main

    main()
    captured = capsys.readouterr()
    assert "SmartPad starting..." in captured.out
