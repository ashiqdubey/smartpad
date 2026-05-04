"""Tests for ContextManager — SPEC.md section 8."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from smartpad.core.context_manager import ContextManager, _estimate_tokens
from smartpad.providers.base import ChatMessage


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_messages(n: int, *, content: str = "x") -> list[ChatMessage]:
    return [ChatMessage(role="user", content=content) for _ in range(n)]


def _make_mock_provider(summary_text: str = "Summary text.") -> MagicMock:
    """Return a mock provider whose chat() yields one ChatChunk with delta=summary."""
    from smartpad.providers.base import ChatChunk

    chunk = ChatChunk(delta=summary_text, finish_reason="stop")

    async def _chat_gen(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield chunk

    provider = MagicMock()
    provider.chat = AsyncMock(return_value=_chat_gen())
    return provider


# ── needs_summarisation ────────────────────────────────────────────────────────


def test_needs_summarisation_false_below_thresholds() -> None:
    cm = ContextManager(strategy="sliding_summary", trigger_messages=30, trigger_tokens=6000)
    msgs = _make_messages(10, content="short")
    assert cm.needs_summarisation(msgs) is False


def test_needs_summarisation_true_on_message_count() -> None:
    cm = ContextManager(strategy="sliding_summary", trigger_messages=30)
    msgs = _make_messages(31)
    assert cm.needs_summarisation(msgs) is True


def test_needs_summarisation_true_on_token_count() -> None:
    # Each message has content of 40 chars → ~10 tokens
    # 601 messages × 10 tokens = 6010 > 6000
    cm = ContextManager(strategy="sliding_summary", trigger_tokens=6000)
    # 601 messages with content that gives >6000 estimated tokens
    msgs = _make_messages(1, content="a" * 24004)  # 24004 / 4 = 6001 tokens
    assert cm.needs_summarisation(msgs) is True


def test_needs_summarisation_none_strategy_never() -> None:
    cm = ContextManager(strategy="none", trigger_messages=1)
    msgs = _make_messages(100)
    assert cm.needs_summarisation(msgs) is False


def test_needs_summarisation_empty_list() -> None:
    cm = ContextManager(strategy="sliding_summary", trigger_messages=5)
    assert cm.needs_summarisation([]) is False


# ── truncate strategy ─────────────────────────────────────────────────────────


async def test_truncate_keeps_recent() -> None:
    cm = ContextManager(strategy="truncate", recent_kept=5)
    msgs = _make_messages(20, content="msg")
    # Give each message a distinct content so we can tell which are kept
    msgs = [ChatMessage(role="user", content=f"msg {i}") for i in range(20)]
    provider = MagicMock()
    result = await cm.summarise(msgs, provider, "model")
    assert len(result) == 5
    # Last 5 messages should be kept
    assert result[0].content == "msg 15"
    assert result[-1].content == "msg 19"


async def test_truncate_empty_list() -> None:
    cm = ContextManager(strategy="truncate", recent_kept=5)
    result = await cm.summarise([], MagicMock(), "model")
    assert result == []


# ── sliding_summary strategy ──────────────────────────────────────────────────


async def test_sliding_summary_replaces_oldest_chunk() -> None:
    cm = ContextManager(
        strategy="sliding_summary",
        messages_per_summary=3,
        recent_kept=2,
    )
    msgs = [ChatMessage(role="user", content=f"msg {i}") for i in range(6)]

    from smartpad.providers.base import ChatChunk

    async def _gen(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield ChatChunk(delta="Summary of old msgs.", finish_reason="stop")

    provider = MagicMock()
    provider.chat = AsyncMock(return_value=_gen())

    result = await cm.summarise(msgs, provider, "model-x")

    # First message should be a system summary
    assert result[0].role == "system"
    assert "Summary" in result[0].content or "Earlier" in result[0].content
    # Remaining messages (indices 3-5) should follow
    assert len(result) == 1 + 3  # 1 summary + 3 kept


async def test_sliding_summary_none_strategy_passthrough() -> None:
    cm = ContextManager(strategy="none")
    msgs = _make_messages(100)
    result = await cm.summarise(msgs, MagicMock(), "model")
    assert result is msgs  # exact same object returned


async def test_sliding_summary_small_list_returns_unchanged() -> None:
    cm = ContextManager(strategy="sliding_summary", recent_kept=15)
    msgs = _make_messages(5)
    result = await cm.summarise(msgs, MagicMock(), "model")
    assert result == msgs


# ── token estimation ──────────────────────────────────────────────────────────


def test_estimate_tokens_heuristic() -> None:
    msgs = [ChatMessage(role="user", content="a" * 40)]
    assert _estimate_tokens(msgs) == 10  # 40 // 4


def test_estimate_tokens_empty() -> None:
    assert _estimate_tokens([]) == 0
