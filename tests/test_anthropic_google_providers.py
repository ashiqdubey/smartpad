"""Tests for AnthropicProvider and GoogleProvider — SPEC.md section 10."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from smartpad.providers.anthropic import AnthropicProvider
from smartpad.providers.base import (
    ChatChunk,
    ChatMessage,
    ModelInfo,
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from smartpad.providers.google import GoogleProvider


# ── Mock helpers ──────────────────────────────────────────────────────────────


def _mock_response(status: int, body: dict[str, Any]) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.json.return_value = body
    return resp


class _FakeStreamResponse:
    """Simulate httpx streaming for Anthropic SSE."""

    def __init__(self, lines: list[str], status: int = 200) -> None:
        self.status_code = status
        self._lines = lines

    def raise_for_status(self) -> None:
        if self.status_code == 401:
            raise httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock(status_code=401))

    async def aiter_lines(self) -> AsyncIterator[str]:
        for line in self._lines:
            yield line

    async def __aenter__(self) -> "_FakeStreamResponse":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass


def _make_anthropic_client(
    *,
    get_response: dict[str, Any] | None = None,
    get_status: int = 200,
    post_response: dict[str, Any] | None = None,
    stream_lines: list[str] | None = None,
    stream_status: int = 200,
) -> Any:
    class _Client:
        async def get(self, url: str, **_: Any) -> MagicMock:
            return _mock_response(get_status, get_response or {})

        async def post(self, url: str, **_: Any) -> MagicMock:
            r = _mock_response(200, post_response or {})
            if get_status == 401:
                r.status_code = 401
            return r

        def stream(self, *_: Any, **__: Any) -> _FakeStreamResponse:
            return _FakeStreamResponse(stream_lines or [], status=stream_status)

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    return _Client


def _make_google_client(
    *,
    get_response: dict[str, Any] | None = None,
    get_status: int = 200,
    post_response: dict[str, Any] | None = None,
    post_status: int = 200,
) -> Any:
    class _Client:
        async def get(self, url: str, **_: Any) -> MagicMock:
            return _mock_response(get_status, get_response or {})

        async def post(self, url: str, **_: Any) -> MagicMock:
            return _mock_response(post_status, post_response or {})

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    return _Client


# ══════════════════════════════════════════════════════════════════════════════
# AnthropicProvider tests
# ══════════════════════════════════════════════════════════════════════════════


async def test_anthropic_list_models_success() -> None:
    factory = _make_anthropic_client(
        get_response={
            "data": [
                {"id": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
                {"id": "claude-3-haiku-20240307", "display_name": "Claude 3 Haiku"},
            ]
        }
    )
    p = AnthropicProvider(api_key="sk-test", _client_factory=factory)
    models = await p.list_models()
    assert len(models) == 2
    assert all(isinstance(m, ModelInfo) for m in models)
    assert models[0].id == "claude-3-haiku-20240307"  # sorted


async def test_anthropic_list_models_auth_error() -> None:
    class _AuthFail:
        async def get(self, *_: Any, **__: Any) -> MagicMock:
            return _mock_response(401, {})

        async def __aenter__(self) -> "_AuthFail":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    p = AnthropicProvider(api_key="bad-key", _client_factory=_AuthFail)
    with pytest.raises(ProviderAuthError):
        await p.list_models()


async def test_anthropic_list_models_connection_error() -> None:
    class _Fail:
        async def get(self, *_: Any, **__: Any) -> None:
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_Fail":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    p = AnthropicProvider(api_key="sk-x", _client_factory=_Fail)
    with pytest.raises(ProviderUnavailableError):
        await p.list_models()


def _anthropic_sse_line(text: str, event_type: str = "content_block_delta") -> str:
    if event_type == "content_block_delta":
        payload = {
            "type": "content_block_delta",
            "delta": {"type": "text_delta", "text": text},
        }
    elif event_type == "message_stop":
        payload = {"type": "message_stop"}
    else:
        payload = {"type": event_type}
    return f"data: {json.dumps(payload)}"


async def test_anthropic_chat_streaming() -> None:
    sse = [
        _anthropic_sse_line("Hello"),
        _anthropic_sse_line(", world"),
        _anthropic_sse_line("", event_type="message_stop"),
    ]
    factory = _make_anthropic_client(stream_lines=sse)
    p = AnthropicProvider(api_key="sk-test", _client_factory=factory)

    msgs = [ChatMessage(role="user", content="Say hello")]
    chunks = []
    async for chunk in await p.chat(msgs, model="claude-3-haiku", stream=True):
        chunks.append(chunk)

    text = "".join(c.delta for c in chunks if c.delta)
    assert text == "Hello, world"


async def test_anthropic_chat_oneshot() -> None:
    body = {
        "content": [{"type": "text", "text": "42"}],
        "stop_reason": "end_turn",
    }
    factory = _make_anthropic_client(post_response=body)
    p = AnthropicProvider(api_key="sk-test", _client_factory=factory)

    msgs = [ChatMessage(role="user", content="What is 6*7?")]
    chunks = []
    async for chunk in await p.chat(msgs, model="claude-3-haiku", stream=False):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].delta == "42"
    assert chunks[0].finish_reason == "end_turn"


async def test_anthropic_validate_credentials_ok() -> None:
    factory = _make_anthropic_client(get_response={"data": [{"id": "m1", "display_name": "M1"}]})
    p = AnthropicProvider(api_key="sk-ok", _client_factory=factory)
    assert await p.validate_credentials() is True


async def test_anthropic_validate_credentials_fail() -> None:
    factory = _make_anthropic_client(get_status=401)
    p = AnthropicProvider(api_key="bad", _client_factory=factory)
    assert await p.validate_credentials() is False


# ══════════════════════════════════════════════════════════════════════════════
# GoogleProvider tests
# ══════════════════════════════════════════════════════════════════════════════


async def test_google_list_models_success() -> None:
    factory = _make_google_client(
        get_response={
            "models": [
                {
                    "name": "models/gemini-2.0-flash",
                    "displayName": "Gemini 2.0 Flash",
                    "inputTokenLimit": 1000000,
                    "supportedGenerationMethods": ["generateContent"],
                },
                {
                    "name": "models/gemini-1.5-pro",
                    "displayName": "Gemini 1.5 Pro",
                    "inputTokenLimit": 2000000,
                    "supportedGenerationMethods": ["generateContent"],
                },
            ]
        }
    )
    p = GoogleProvider(api_key="gkey-test", _client_factory=factory)
    models = await p.list_models()
    assert len(models) == 2
    assert all(isinstance(m, ModelInfo) for m in models)


async def test_google_list_models_auth_error() -> None:
    factory = _make_google_client(get_status=403)
    p = GoogleProvider(api_key="bad", _client_factory=factory)
    with pytest.raises(ProviderAuthError):
        await p.list_models()


async def test_google_list_models_connection_error() -> None:
    class _Fail:
        async def get(self, *_: Any, **__: Any) -> None:
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_Fail":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    p = GoogleProvider(api_key="k", _client_factory=_Fail)
    with pytest.raises(ProviderUnavailableError):
        await p.list_models()


async def test_google_chat_returns_text() -> None:
    body = {
        "candidates": [
            {
                "content": {"parts": [{"text": "The answer is 42."}], "role": "model"},
                "finishReason": "STOP",
            }
        ]
    }
    factory = _make_google_client(post_response=body)
    p = GoogleProvider(api_key="gkey", _client_factory=factory)

    msgs = [ChatMessage(role="user", content="What is 6*7?")]
    chunks = []
    async for chunk in await p.chat(msgs, model="gemini-2.0-flash", stream=False):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert "42" in chunks[0].delta


async def test_google_chat_empty_candidates() -> None:
    body: dict[str, Any] = {"candidates": []}
    factory = _make_google_client(post_response=body)
    p = GoogleProvider(api_key="gkey", _client_factory=factory)

    msgs = [ChatMessage(role="user", content="hi")]
    chunks = []
    async for chunk in await p.chat(msgs, model="gemini-2.0-flash", stream=False):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].delta == ""
    assert chunks[0].finish_reason == "stop"


async def test_google_validate_credentials_ok() -> None:
    factory = _make_google_client(
        get_response={
            "models": [
                {
                    "name": "models/gemini-2.0-flash",
                    "displayName": "Gemini 2.0 Flash",
                    "supportedGenerationMethods": ["generateContent"],
                }
            ]
        }
    )
    p = GoogleProvider(api_key="good-key", _client_factory=factory)
    assert await p.validate_credentials() is True


async def test_google_validate_credentials_fail() -> None:
    factory = _make_google_client(get_status=401)
    p = GoogleProvider(api_key="bad", _client_factory=factory)
    assert await p.validate_credentials() is False


# ── Registry integration ──────────────────────────────────────────────────────


def test_registry_includes_anthropic_and_google() -> None:
    from smartpad.providers.registry import REGISTRY

    assert "AnthropicProvider" in REGISTRY
    assert "GoogleProvider" in REGISTRY


def test_registry_build_anthropic() -> None:
    from smartpad.providers.registry import build_provider

    p = build_provider("AnthropicProvider", api_key="sk-x")
    assert isinstance(p, AnthropicProvider)


def test_registry_build_google() -> None:
    from smartpad.providers.registry import build_provider

    p = build_provider("GoogleProvider", api_key="gk-x")
    assert isinstance(p, GoogleProvider)
