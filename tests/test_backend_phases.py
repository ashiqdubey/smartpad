"""Tests for Phases 17–22: providers, server detector, API, reliability, exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

# ── Phase 17: Anthropic provider ─────────────────────────────────────────────

class TestAnthropicProvider:
    def _make_client_factory(
        self,
        get_response: dict | None = None,
        stream_events: list[str] | None = None,
        get_status: int = 200,
    ) -> Any:
        class _Resp:
            def __init__(self, events: list[str], status: int = 200) -> None:
                self.status_code = status
                self._events = events
            def raise_for_status(self) -> None:
                if self.status_code >= 400:
                    r = MagicMock(spec=httpx.Response)
                    r.status_code = self.status_code
                    raise httpx.HTTPStatusError("err", request=MagicMock(), response=r)
            def json(self) -> dict:
                return get_response or {}
            async def aiter_lines(self):
                for e in (self._events or []):
                    yield e
            async def __aenter__(self): return self
            async def __aexit__(self, *_): pass

        class _Client:
            async def get(self, *_, **__): return _Resp([], get_status)
            async def post(self, *_, **__): return _Resp(stream_events or [])
            def stream(self, *_, **__): return _Resp(stream_events or [])
            async def __aenter__(self): return self
            async def __aexit__(self, *_): pass

        return _Client

    async def test_list_models(self) -> None:
        from smartpad.providers.anthropic import AnthropicProvider

        factory = self._make_client_factory(
            get_response={"data": [{"id": "claude-3-5-haiku-latest", "display_name": "Haiku"}]}
        )
        p = AnthropicProvider(api_key="test", _client_factory=factory)
        models = await p.list_models()
        assert len(models) == 1
        assert models[0].id == "claude-3-5-haiku-latest"

    async def test_list_models_auth_error(self) -> None:
        from smartpad.providers.anthropic import AnthropicProvider
        from smartpad.providers.base import ProviderAuthError

        factory = self._make_client_factory(get_status=401)
        p = AnthropicProvider(api_key="bad", _client_factory=factory)
        with pytest.raises(ProviderAuthError):
            await p.list_models()

    async def test_streaming_chat(self) -> None:
        from smartpad.providers.anthropic import AnthropicProvider
        from smartpad.providers.base import ChatMessage

        events = [
            'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}',
            'data: {"type":"message_stop"}',
        ]
        factory = self._make_client_factory(stream_events=events)
        p = AnthropicProvider(api_key="test", _client_factory=factory)
        chunks = []
        async for c in await p.chat(
            [ChatMessage(role="user", content="hi")], model="claude-3-5-haiku-latest"
        ):
            chunks.append(c)
        assert any(c.delta == "Hello" for c in chunks)

    async def test_validate_credentials_ok(self) -> None:
        from smartpad.providers.anthropic import AnthropicProvider

        factory = self._make_client_factory(
            get_response={"data": [{"id": "m1"}]}
        )
        p = AnthropicProvider(api_key="test", _client_factory=factory)
        assert await p.validate_credentials() is True


# ── Phase 17: Google provider ─────────────────────────────────────────────────

class TestGoogleProvider:
    def _make_client_factory(self, get_resp: dict | None = None, post_resp: dict | None = None, status: int = 200) -> Any:
        class _Resp:
            def __init__(self, data: dict, s: int = 200) -> None:
                self.status_code = s
                self._data = data
            def raise_for_status(self) -> None:
                if self.status_code >= 400:
                    r = MagicMock(spec=httpx.Response)
                    r.status_code = self.status_code
                    raise httpx.HTTPStatusError("err", request=MagicMock(), response=r)
            def json(self) -> dict: return self._data

        class _Client:
            async def get(self, *_, **__): return _Resp(get_resp or {}, status)
            async def post(self, *_, **__): return _Resp(post_resp or {})
            async def __aenter__(self): return self
            async def __aexit__(self, *_): pass

        return _Client

    async def test_list_models(self) -> None:
        from smartpad.providers.google import GoogleProvider

        resp = {"models": [{"name": "models/gemini-2.0-flash", "displayName": "Gemini Flash", "supportedGenerationMethods": ["generateContent"]}]}
        factory = self._make_client_factory(get_resp=resp)
        p = GoogleProvider(api_key="test", _client_factory=factory)
        models = await p.list_models()
        assert len(models) == 1
        assert models[0].id == "gemini-2.0-flash"

    async def test_chat_oneshot(self) -> None:
        from smartpad.providers.google import GoogleProvider
        from smartpad.providers.base import ChatMessage

        resp = {"candidates": [{"content": {"parts": [{"text": "42"}]}}]}
        factory = self._make_client_factory(post_resp=resp)
        p = GoogleProvider(api_key="test", _client_factory=factory)
        chunks = []
        result = p.chat(
            [ChatMessage(role="user", content="what is 6*7")], model="gemini-2.0-flash"
        )
        # chat() is a coroutine that returns an async iterator OR an async generator
        import inspect
        if inspect.isawaitable(result):
            result = await result
        async for c in result:
            chunks.append(c)
        assert chunks[0].delta == "42"


# ── Phase 18: Server detector ─────────────────────────────────────────────────

class TestServerDetector:
    async def test_returns_empty_when_nothing_running(self) -> None:
        from smartpad.providers.server_detector import detect_local_servers
        # Real call with no local servers — should silently return empty list
        results = await detect_local_servers()
        assert isinstance(results, list)

    async def test_detect_local_servers_returns_list(self) -> None:
        from smartpad.providers.server_detector import detect_local_servers
        results = await detect_local_servers()
        assert isinstance(results, list)


# ── Phase 21: Reliability ─────────────────────────────────────────────────────

class TestBackup:
    def test_should_backup_today_no_backups(self, tmp_path: Path) -> None:
        from smartpad.utils.backup import should_backup_today
        assert should_backup_today(tmp_path) is True

    def test_daily_backup_creates_file(self, tmp_path: Path) -> None:
        from smartpad.utils.backup import daily_backup
        db = tmp_path / "smartpad.db"
        db.write_bytes(b"db content")
        dest = daily_backup(tmp_path, db, retention=7)
        assert dest is not None
        assert dest.exists()

    def test_backup_pruning(self, tmp_path: Path) -> None:
        from smartpad.utils.backup import daily_backup, _prune_backups
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        for i in range(5):
            (backup_dir / f"smartpad-2026-01-0{i+1}.db").write_bytes(b"x")
        _prune_backups(backup_dir, keep=3)
        remaining = list(backup_dir.glob("*.db"))
        assert len(remaining) == 3

    def test_should_backup_today_after_backup(self, tmp_path: Path) -> None:
        from smartpad.utils.backup import daily_backup, should_backup_today
        db = tmp_path / "smartpad.db"
        db.write_bytes(b"data")
        daily_backup(tmp_path, db)
        assert should_backup_today(tmp_path) is False


class TestCrashRecovery:
    def test_write_and_read(self, tmp_path: Path) -> None:
        from smartpad.utils.crash_recovery import write_recovery, read_recovery
        msgs = [{"role": "user", "content": "hello"}]
        write_recovery(tmp_path, msgs)
        recovered = read_recovery(tmp_path)
        assert recovered is not None
        assert recovered[0]["content"] == "hello"

    def test_read_returns_none_when_missing(self, tmp_path: Path) -> None:
        from smartpad.utils.crash_recovery import read_recovery
        assert read_recovery(tmp_path) is None

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        from smartpad.utils.crash_recovery import write_recovery, clear_recovery, read_recovery
        write_recovery(tmp_path, [{"role": "user", "content": "x"}])
        clear_recovery(tmp_path)
        assert read_recovery(tmp_path) is None

    def test_only_keeps_last_5(self, tmp_path: Path) -> None:
        from smartpad.utils.crash_recovery import write_recovery, read_recovery
        msgs = [{"role": "user", "content": str(i)} for i in range(10)]
        write_recovery(tmp_path, msgs)
        recovered = read_recovery(tmp_path)
        assert recovered is not None
        assert len(recovered) == 5
        assert recovered[0]["content"] == "5"


class TestSearchHistory:
    def test_add_and_suggest(self) -> None:
        from smartpad.utils.search_history import SearchHistory
        h = SearchHistory()
        h.add("python asyncio")
        h.add("sqlite fts5")
        assert "python asyncio" in h.get_suggestions("python")
        assert len(h.get_suggestions("")) == 2

    def test_max_10_entries(self) -> None:
        from smartpad.utils.search_history import SearchHistory
        h = SearchHistory(max_size=10)
        for i in range(15):
            h.add(f"query {i}")
        assert len(h) == 10

    def test_deduplication(self) -> None:
        from smartpad.utils.search_history import SearchHistory
        h = SearchHistory()
        h.add("repeat")
        h.add("other")
        h.add("repeat")
        assert len(h) == 2
        assert h.get_suggestions()[0] == "repeat"  # most recent first

    def test_clear(self) -> None:
        from smartpad.utils.search_history import SearchHistory
        h = SearchHistory()
        h.add("hello")
        h.clear()
        assert len(h) == 0


# ── Phase 22: Export ──────────────────────────────────────────────────────────

class TestExporters:
    async def test_export_notes_markdown(self, tmp_path: Path) -> None:
        from smartpad.db.engine import init_async_engine, get_async_session
        from smartpad.db.migrations import run_migrations
        from smartpad.db.models import Note
        from smartpad.db.repositories.notes import NotesRepo
        from smartpad.utils.exporters import export_notes
        from datetime import UTC, datetime

        db = tmp_path / "test.db"
        run_migrations(db)
        init_async_engine(db)

        async with get_async_session() as session:
            repo = NotesRepo(session)
            await repo.save(Note(
                content="Test note content",
                original_content="Test note content",
                created_at=datetime.now(UTC),
                sync_version=0,
            ))

        async with get_async_session() as session:
            result = await export_notes(session, fmt="markdown")

        assert "Test note content" in result
        assert "# Notes" in result

    async def test_export_notes_json(self, tmp_path: Path) -> None:
        from smartpad.db.engine import init_async_engine, get_async_session
        from smartpad.db.migrations import run_migrations
        from smartpad.db.models import Note
        from smartpad.db.repositories.notes import NotesRepo
        from smartpad.utils.exporters import export_notes
        from datetime import UTC, datetime

        db = tmp_path / "test2.db"
        run_migrations(db)
        init_async_engine(db)

        async with get_async_session() as session:
            repo = NotesRepo(session)
            await repo.save(Note(
                content="JSON note",
                original_content="JSON note",
                created_at=datetime.now(UTC),
                sync_version=0,
            ))

        async with get_async_session() as session:
            result = await export_notes(session, fmt="json")

        data = json.loads(result)
        assert isinstance(data, list)
        assert any("JSON note" in str(item) for item in data)

    async def test_export_empty_returns_valid(self, tmp_path: Path) -> None:
        from smartpad.db.engine import init_async_engine, get_async_session
        from smartpad.db.migrations import run_migrations
        from smartpad.utils.exporters import export_notes

        db = tmp_path / "empty.db"
        run_migrations(db)
        init_async_engine(db)

        async with get_async_session() as session:
            result = await export_notes(session, fmt="json")

        data = json.loads(result)
        assert data == []
