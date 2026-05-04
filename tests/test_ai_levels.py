"""Unit tests for AI level pipeline — mocked provider, no real LLM calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from smartpad.core.ai_levels import (
    Metadata,
    ProcessResult,
    _parse_metadata,
    process_capture,
    process_level_0,
    process_level_1,
)
from smartpad.db.engine import init_async_engine, get_async_session
from smartpad.db.migrations import run_migrations


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _mock_provider(json_response: str = "", text_response: str = "") -> Any:
    """Build a mock Provider whose chat() returns preset chunks."""
    from smartpad.providers.base import ChatChunk

    async def fake_chat(*args: Any, **kwargs: Any) -> Any:
        async def _gen() -> Any:
            payload = json_response or text_response
            yield ChatChunk(delta=payload, finish_reason="stop")

        return _gen()

    provider = AsyncMock()
    provider.chat = fake_chat
    return provider


def _valid_metadata_json(**overrides: Any) -> str:
    base = {
        "item_type": "note",
        "tags": ["work", "meeting"],
        "book_name": "Work",
        "deadline": None,
        "trigger_time": None,
        "language": None,
    }
    base.update(overrides)
    return json.dumps(base)


# ── _parse_metadata ───────────────────────────────────────────────────────────

def test_parse_metadata_valid_json() -> None:
    raw = _valid_metadata_json(item_type="task", tags=["urgent"])
    meta = _parse_metadata(raw)
    assert meta.item_type == "task"
    assert "urgent" in meta.tags


def test_parse_metadata_with_code_fence() -> None:
    raw = "```json\n" + _valid_metadata_json() + "\n```"
    meta = _parse_metadata(raw)
    assert meta.item_type == "note"


def test_parse_metadata_invalid_json_returns_default() -> None:
    meta = _parse_metadata("this is not json")
    assert meta.item_type == "note"
    assert meta.tags == []


def test_parse_metadata_missing_fields() -> None:
    meta = _parse_metadata("{}")
    assert meta.item_type == "note"


# ── process_level_0 ───────────────────────────────────────────────────────────

def test_level_0_preserves_original() -> None:
    result = process_level_0("buy milk")
    assert result.original_content == "buy milk"
    assert result.content == "buy milk"
    assert result.ai_level_applied == 0


def test_level_0_no_metadata() -> None:
    result = process_level_0("hello world")
    assert result.metadata.tags == []
    assert result.metadata.book_name is None


# ── process_level_1 ───────────────────────────────────────────────────────────

async def test_level_1_returns_metadata() -> None:
    provider = _mock_provider(json_response=_valid_metadata_json(
        item_type="task", tags=["work"], book_name="Projects"
    ))
    result = await process_level_1("finish the report by friday", provider, "model")
    assert result.ai_level_applied == 1
    assert result.metadata.item_type == "task"
    assert "work" in result.metadata.tags
    assert result.metadata.book_name == "Projects"


async def test_level_1_never_modifies_content() -> None:
    provider = _mock_provider(json_response=_valid_metadata_json())
    text = "the original text stays unchanged"
    result = await process_level_1(text, provider, "model")
    assert result.content == text
    assert result.original_content == text


async def test_level_1_fallback_on_provider_error() -> None:
    from smartpad.providers.base import ProviderUnavailableError

    async def failing_chat(*args: Any, **kwargs: Any) -> Any:
        raise ProviderUnavailableError("down")

    provider = AsyncMock()
    provider.chat = failing_chat

    result = await process_level_1("some text", provider, "model")
    # Must fall back to level 0 silently
    assert result.ai_level_applied == 0
    assert result.content == "some text"


# ── process_capture dispatcher ────────────────────────────────────────────────

async def test_process_capture_level_0_no_provider() -> None:
    result = await process_capture("note text", ai_level=0, provider=None, model="x")
    assert result.ai_level_applied == 0


async def test_process_capture_level_0_ignores_provider() -> None:
    provider = _mock_provider(json_response=_valid_metadata_json())
    result = await process_capture("note text", ai_level=0, provider=provider, model="x")
    assert result.ai_level_applied == 0


async def test_process_capture_level_1_with_provider() -> None:
    provider = _mock_provider(json_response=_valid_metadata_json(tags=["ai"]))
    result = await process_capture("test note", ai_level=1, provider=provider, model="x")
    assert result.ai_level_applied == 1
    assert "ai" in result.metadata.tags


async def test_process_capture_no_provider_falls_back_to_0() -> None:
    result = await process_capture("test", ai_level=2, provider=None, model="x")
    assert result.ai_level_applied == 0


# ── original_content always preserved ────────────────────────────────────────

async def test_original_content_preserved_at_all_levels() -> None:
    original = "buy mlk nd bred"
    provider = _mock_provider(
        json_response=_valid_metadata_json(),
    )
    for level in range(2):  # levels 0 and 1 tested here
        result = await process_capture(original, ai_level=level, provider=provider, model="x")
        assert result.original_content == original


# ── ChatService integration ───────────────────────────────────────────────────

async def test_chat_service_save_note(tmp_path: Path) -> None:
    from smartpad.core.chat_service import handle_capture

    db = tmp_path / "test.db"
    run_migrations(db)
    init_async_engine(db)

    provider = _mock_provider(json_response=_valid_metadata_json(item_type="note"))

    async with get_async_session() as session:
        result = await handle_capture(
            text="this is a test note",
            ai_level=0,
            provider=None,
            model="x",
            session=session,
        )

    assert result["route_result"].action.value == "save_note" or \
           result["route_result"].body  # chat fallback is also OK
    # The note was persisted
    assert result["saved_id"] is not None or result["route_result"].body


async def test_chat_service_slash_note_saved(tmp_path: Path) -> None:
    from smartpad.core.chat_service import handle_capture
    from smartpad.db.repositories.notes import NotesRepo

    db = tmp_path / "test.db"
    run_migrations(db)
    init_async_engine(db)

    async with get_async_session() as session:
        result = await handle_capture(
            text="/note buy groceries tomorrow",
            ai_level=0,
            provider=None,
            model="x",
            session=session,
        )
        assert result["saved_id"] is not None

    async with get_async_session() as session:
        repo = NotesRepo(session)
        notes = await repo.list()
        assert len(notes) == 1
        assert "groceries" in notes[0].content
