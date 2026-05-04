"""OpenAI-compatible provider adapter — covers OpenAI, OpenRouter, Groq,
Ollama, LM Studio, llama-server, and any custom OpenAI-compat endpoint.
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

_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


class OpenAICompatibleProvider(Provider):
    """Adapter for any OpenAI-compatible REST API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        name: str = "openai",
        *,
        _client_factory: Any = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.name = name
        self._client_factory = _client_factory  # injected in tests

    # ── internal helpers ──────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _make_client(self) -> httpx.AsyncClient:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.AsyncClient(headers=self._headers(), timeout=_TIMEOUT)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code == 401:
            raise ProviderAuthError("Invalid API key or unauthorized.")
        if response.status_code == 429:
            raise ProviderRateLimitError("Rate limit exceeded. Retry later.")
        if response.status_code >= 500:
            raise ProviderUnavailableError(
                f"Provider server error: {response.status_code}"
            )
        response.raise_for_status()

    # ── Provider interface ────────────────────────────────────────────────────

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with self._make_client() as client:
                response = await client.get(f"{self.base_url}/v1/models")
                self._raise_for_status(response)
                data = response.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc

        models = []
        for item in data.get("data", []):
            models.append(
                ModelInfo(
                    id=item["id"],
                    name=item.get("name") or item["id"],
                    context_length=item.get("context_length"),
                )
            )
        return sorted(models, key=lambda m: m.id)

    async def chat(  # type: ignore[override]  # returns AsyncIterator via yield
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [m.to_api_dict() for m in messages],
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = [t.to_api_dict() for t in tools]

        if stream:
            return self._stream_chat(payload)
        return self._oneshot_chat(payload)

    async def _stream_chat(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[ChatChunk]:
        try:
            async with self._make_client() as client, client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            ) as response:
                self._raise_for_status(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        logger.warning("Unparseable SSE chunk: {}", data)
                        continue
                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    yield ChatChunk(
                        delta=delta.get("content") or "",
                        finish_reason=choice.get("finish_reason"),
                        tool_calls=delta.get("tool_calls"),
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc

    async def _oneshot_chat(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[ChatChunk]:
        try:
            async with self._make_client() as client:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                )
                self._raise_for_status(response)
                data = response.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc

        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
        usage = data.get("usage")
        yield ChatChunk(
            delta=content,
            finish_reason=choice.get("finish_reason"),
            usage=usage,
        )

    async def validate_credentials(self) -> bool:
        try:
            await self.list_models()
            return True
        except ProviderAuthError:
            return False
        except ProviderError:
            return False
