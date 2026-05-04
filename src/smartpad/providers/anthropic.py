"""Anthropic provider adapter — SPEC.md section 10.

Adapts Anthropic's native SSE API to the Provider interface.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx
from loguru import logger

from smartpad.providers.base import (
    ChatChunk,
    ChatMessage,
    ModelInfo,
    Provider,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ToolSchema,
)

_API_BASE = "https://api.anthropic.com"
_ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


class AnthropicProvider(Provider):
    """Adapter for the Anthropic API (Claude models)."""

    name: str = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-latest",
        *,
        _client_factory: Any = None,
    ) -> None:
        self.api_key = api_key
        self.default_model = model
        self._client_factory = _client_factory

    def _make_client(self) -> httpx.AsyncClient:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            timeout=_TIMEOUT,
        )

    @staticmethod
    def _check_status(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise ProviderAuthError("Invalid Anthropic API key.")
        if response.status_code == 429:
            raise ProviderRateLimitError("Anthropic rate limit hit.")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"Anthropic server error: {response.status_code}")
        response.raise_for_status()

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with self._make_client() as client:
                r = await client.get(f"{_API_BASE}/v1/models")
                self._check_status(r)
                data = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc
        return sorted(
            [
                ModelInfo(id=m["id"], name=m.get("display_name", m["id"]))
                for m in data.get("data", [])
            ],
            key=lambda m: m.id,
        )

    async def chat(  # type: ignore[override]
        self,
        messages: list[ChatMessage],
        model: str = "",
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]:
        system_parts = [m.content for m in messages if m.role == "system"]
        conv = [m.to_api_dict() for m in messages if m.role != "system"]
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": conv,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": stream,
        }
        if system_parts:
            payload["system"] = "\n".join(system_parts)
        if tools:
            payload["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.parameters}
                for t in tools
            ]
        if stream:
            return self._stream_chat(payload)
        return self._oneshot_chat(payload)

    async def _stream_chat(self, payload: dict[str, Any]) -> AsyncIterator[ChatChunk]:
        try:
            async with self._make_client() as client, client.stream(
                "POST", f"{_API_BASE}/v1/messages", json=payload
            ) as response:
                self._check_status(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        logger.warning("Unparseable Anthropic SSE: {}", data)
                        continue
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield ChatChunk(delta=delta.get("text", ""))
                    elif event.get("type") == "message_stop":
                        yield ChatChunk(finish_reason="stop")
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc

    async def _oneshot_chat(self, payload: dict[str, Any]) -> AsyncIterator[ChatChunk]:
        payload["stream"] = False
        try:
            async with self._make_client() as client:
                r = await client.post(f"{_API_BASE}/v1/messages", json=payload)
                self._check_status(r)
                data = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc
        content = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        yield ChatChunk(delta=content, finish_reason=data.get("stop_reason"))

    async def validate_credentials(self) -> bool:
        try:
            await self.list_models()
            return True
        except ProviderError:
            return False
