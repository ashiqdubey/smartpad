"""Unit tests for provider layer — all HTTP mocked, no real network calls."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from smartpad.providers.base import (
    ChatMessage,
    ModelInfo,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ToolSchema,
)
from smartpad.providers.openai_compatible import OpenAICompatibleProvider
from smartpad.providers.registry import build_provider, get_active, set_active


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _make_models_response(model_ids: list[str]) -> dict[str, Any]:
    return {"data": [{"id": m, "object": "model"} for m in model_ids]}


class _FakeStreamResponse:
    """Simulates httpx streaming response for SSE."""

    def __init__(self, lines: list[str], status: int = 200) -> None:
        self.status_code = status
        self._lines = lines

    def raise_for_status(self) -> None:
        if self.status_code == 401:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 401
            raise httpx.HTTPStatusError("401", request=MagicMock(), response=resp)
        if self.status_code == 429:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 429
            raise httpx.HTTPStatusError("429", request=MagicMock(), response=resp)

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line

    async def __aenter__(self) -> _FakeStreamResponse:
        return self

    async def __aexit__(self, *_: object) -> None:
        pass


def _sse_line(content: str, finish: str | None = None) -> str:
    chunk = {
        "choices": [{"delta": {"content": content}, "finish_reason": finish}]
    }
    return f"data: {json.dumps(chunk)}"


def _make_client_factory(
    *,
    get_response: dict[str, Any] | None = None,
    post_response: dict[str, Any] | None = None,
    stream_lines: list[str] | None = None,
    get_status: int = 200,
    stream_status: int = 200,
) -> Any:
    """Build an injectable async client factory for tests."""

    class _FakeClient:
        async def get(self, url: str, **_: Any) -> httpx.Response:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = get_status
            resp.json.return_value = get_response or {}
            return resp

        async def post(self, url: str, **_: Any) -> httpx.Response:
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 200
            resp.json.return_value = post_response or {}
            return resp

        def stream(self, *_: Any, **__: Any) -> _FakeStreamResponse:
            return _FakeStreamResponse(stream_lines or [], status=stream_status)

        async def __aenter__(self) -> _FakeClient:
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    return _FakeClient


def _provider(**kwargs: Any) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="http://fake-openai.local",
        api_key="sk-test",
        **kwargs,
    )


# ── list_models ───────────────────────────────────────────────────────────────

async def test_list_models_returns_sorted_list() -> None:
    factory = _make_client_factory(
        get_response=_make_models_response(["gpt-4o", "gpt-3.5-turbo", "gpt-4"])
    )
    p = _provider(_client_factory=factory)
    models = await p.list_models()
    assert len(models) == 3
    assert models[0].id == "gpt-3.5-turbo"
    assert all(isinstance(m, ModelInfo) for m in models)


async def test_list_models_auth_error() -> None:
    factory = _make_client_factory(get_response={}, get_status=401)
    p = _provider(_client_factory=factory)
    with pytest.raises(ProviderAuthError):
        await p.list_models()


async def test_list_models_rate_limit() -> None:
    factory = _make_client_factory(get_response={}, get_status=429)
    p = _provider(_client_factory=factory)
    with pytest.raises(ProviderRateLimitError):
        await p.list_models()


async def test_list_models_connection_error() -> None:
    class _FailClient:
        async def get(self, *_: Any, **__: Any) -> None:
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> _FailClient:
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    p = _provider(_client_factory=_FailClient)
    with pytest.raises(ProviderUnavailableError):
        await p.list_models()


# ── chat streaming ────────────────────────────────────────────────────────────

async def test_chat_streams_tokens() -> None:
    sse = [
        _sse_line("Hello"),
        _sse_line(", "),
        _sse_line("world"),
        _sse_line("", finish="stop"),
        "data: [DONE]",
    ]
    factory = _make_client_factory(stream_lines=sse)
    p = _provider(_client_factory=factory)

    messages = [ChatMessage(role="user", content="Say hello")]
    chunks = []
    async for chunk in await p.chat(messages, model="gpt-4o", stream=True):
        chunks.append(chunk)

    text = "".join(c.delta for c in chunks)
    assert text == "Hello, world"
    assert chunks[-1].finish_reason == "stop"


async def test_chat_skips_blank_sse_lines() -> None:
    sse = [
        "",  # blank lines should be ignored
        ":",  # comment lines should be ignored
        _sse_line("Hi"),
        "data: [DONE]",
    ]
    factory = _make_client_factory(stream_lines=sse)
    p = _provider(_client_factory=factory)

    chunks = []
    async for chunk in await p.chat(
        [ChatMessage(role="user", content="hi")], model="gpt-4o"
    ):
        chunks.append(chunk)
    assert any(c.delta == "Hi" for c in chunks)


async def test_chat_stream_auth_error() -> None:
    factory = _make_client_factory(stream_lines=[], stream_status=401)
    p = _provider(_client_factory=factory)
    with pytest.raises(ProviderAuthError):
        async for _ in await p.chat(
            [ChatMessage(role="user", content="x")], model="gpt-4o"
        ):
            pass


# ── non-streaming chat ────────────────────────────────────────────────────────

async def test_chat_oneshot() -> None:
    post_resp = {
        "choices": [
            {"message": {"role": "assistant", "content": "42"}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6},
    }
    factory = _make_client_factory(post_response=post_resp)
    p = _provider(_client_factory=factory)

    chunks = []
    async for chunk in await p.chat(
        [ChatMessage(role="user", content="what is 6x7?")],
        model="gpt-4o",
        stream=False,
    ):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].delta == "42"
    assert chunks[0].usage is not None


# ── tool schema serialisation ─────────────────────────────────────────────────

async def test_chat_sends_tools_in_payload() -> None:
    sent_payload: list[dict[str, Any]] = []

    class _CapturingClient:
        def stream(self, method: str, url: str, json: Any = None, **_: Any) -> Any:
            sent_payload.append(json or {})
            return _FakeStreamResponse(["data: [DONE]"])

        async def __aenter__(self) -> _CapturingClient:
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    p = _provider(_client_factory=_CapturingClient)
    tool = ToolSchema(
        name="save_note",
        description="Save a note",
        parameters={"type": "object", "properties": {}},
    )
    async for _ in await p.chat(
        [ChatMessage(role="user", content="save this")],
        model="gpt-4o",
        tools=[tool],
    ):
        pass

    assert len(sent_payload) == 1
    tools_in_payload = sent_payload[0].get("tools", [])
    assert len(tools_in_payload) == 1
    assert tools_in_payload[0]["function"]["name"] == "save_note"


# ── validate_credentials ──────────────────────────────────────────────────────

async def test_validate_credentials_ok() -> None:
    factory = _make_client_factory(
        get_response=_make_models_response(["gpt-4o"])
    )
    p = _provider(_client_factory=factory)
    assert await p.validate_credentials() is True


async def test_validate_credentials_bad_key() -> None:
    factory = _make_client_factory(get_response={}, get_status=401)
    p = _provider(_client_factory=factory)
    assert await p.validate_credentials() is False


# ── registry ──────────────────────────────────────────────────────────────────

def test_registry_build_openai_compatible() -> None:
    p = build_provider(
        "OpenAICompatibleProvider",
        base_url="http://localhost:11434",
        name="ollama",
    )
    assert isinstance(p, OpenAICompatibleProvider)
    assert p.name == "ollama"


def test_registry_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown provider type"):
        build_provider("NonExistentProvider")


def test_registry_set_and_get_active() -> None:
    p = build_provider(
        "OpenAICompatibleProvider", base_url="http://localhost:1234", name="lmstudio"
    )
    set_active(p)
    assert get_active() is p
