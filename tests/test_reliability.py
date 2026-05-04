"""Tests for reliability utilities — SPEC.md section 20.

Tests: backup, crash_recovery, search_history.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from smartpad.utils.backup import daily_backup, should_backup_today
from smartpad.utils.crash_recovery import clear_recovery, read_recovery, write_recovery
from smartpad.utils.search_history import SearchHistory


# ══════════════════════════════════════════════════════════════════════════════
# Auto-backup tests
# ══════════════════════════════════════════════════════════════════════════════


def test_daily_backup_creates_file(tmp_path: Path) -> None:
    """Backup creates a dated file in <data_dir>/backups/."""
    db_path = tmp_path / "smartpad.db"
    db_path.write_bytes(b"SQLITE")

    result = daily_backup(tmp_path, db_path)

    assert result is not None
    assert result.exists()
    assert result.suffix == ".db"
    assert "smartpad-" in result.name


def test_daily_backup_pruning(tmp_path: Path) -> None:
    """Backup pruning keeps only the requested number of files."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True)

    # Pre-create 8 fake backups with different dates
    for i in range(8):
        fake = backup_dir / f"smartpad-2024-01-{i + 1:02d}.db"
        fake.write_bytes(b"old")

    db_path = tmp_path / "smartpad.db"
    db_path.write_bytes(b"SQLITE")

    daily_backup(tmp_path, db_path, retention=7)

    backups = sorted(backup_dir.glob("smartpad-*.db"))
    assert len(backups) <= 7


def test_should_backup_today_no_backup_exists(tmp_path: Path) -> None:
    assert should_backup_today(tmp_path) is True


def test_should_backup_today_backup_exists(tmp_path: Path) -> None:
    db_path = tmp_path / "smartpad.db"
    db_path.write_bytes(b"SQLITE")

    daily_backup(tmp_path, db_path)
    # Now a backup exists for today → should_backup_today returns False
    assert should_backup_today(tmp_path) is False


def test_daily_backup_missing_db_returns_none(tmp_path: Path) -> None:
    db_path = tmp_path / "nonexistent.db"
    result = daily_backup(tmp_path, db_path)
    assert result is None


# ══════════════════════════════════════════════════════════════════════════════
# Crash recovery tests
# ══════════════════════════════════════════════════════════════════════════════


def test_write_then_read_recovery(tmp_path: Path) -> None:
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    write_recovery(tmp_path, messages)
    recovered = read_recovery(tmp_path)
    assert recovered == messages


def test_read_recovery_no_file(tmp_path: Path) -> None:
    assert read_recovery(tmp_path) is None


def test_clear_recovery(tmp_path: Path) -> None:
    write_recovery(tmp_path, [{"role": "user", "content": "test"}])
    assert read_recovery(tmp_path) is not None
    clear_recovery(tmp_path)
    assert read_recovery(tmp_path) is None


def test_clear_recovery_no_file_is_safe(tmp_path: Path) -> None:
    # Should not raise even if no file exists
    clear_recovery(tmp_path)


def test_write_recovery_truncates_to_5_messages(tmp_path: Path) -> None:
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(10)]
    write_recovery(tmp_path, messages)
    recovered = read_recovery(tmp_path)
    assert recovered is not None
    assert len(recovered) <= 5
    # Last 5 should be kept
    assert recovered[-1]["content"] == "msg 9"


# ══════════════════════════════════════════════════════════════════════════════
# SearchHistory tests
# ══════════════════════════════════════════════════════════════════════════════


def test_search_history_add_and_suggest() -> None:
    h = SearchHistory()
    h.add("python asyncio")
    h.add("fastapi tutorial")
    suggestions = h.get_suggestions("python")
    assert "python asyncio" in suggestions


def test_search_history_max_10() -> None:
    h = SearchHistory(max_size=10)
    for i in range(15):
        h.add(f"query {i}")
    assert len(h) == 10


def test_search_history_custom_max() -> None:
    h = SearchHistory(max_size=3)
    h.add("a")
    h.add("b")
    h.add("c")
    h.add("d")
    assert len(h) == 3


def test_search_history_deduplicates() -> None:
    h = SearchHistory()
    h.add("python")
    h.add("python")
    assert len(h) == 1


def test_search_history_most_recent_first() -> None:
    h = SearchHistory()
    h.add("first")
    h.add("second")
    h.add("third")
    suggestions = h.get_suggestions("")
    assert suggestions[0] == "third"


def test_search_history_clear() -> None:
    h = SearchHistory()
    h.add("query 1")
    h.add("query 2")
    h.clear()
    assert len(h) == 0
    assert h.get_suggestions("") == []


def test_search_history_empty_query_ignored() -> None:
    h = SearchHistory()
    h.add("")
    h.add("   ")
    assert len(h) == 0


def test_search_history_prefix_filter() -> None:
    h = SearchHistory()
    h.add("python tips")
    h.add("pytest tutorial")
    h.add("fastapi guide")
    results = h.get_suggestions("py")
    assert all(r.lower().startswith("py") for r in results)
    assert "fastapi guide" not in results


def test_search_history_no_match_returns_empty() -> None:
    h = SearchHistory()
    h.add("python")
    assert h.get_suggestions("zzz") == []
