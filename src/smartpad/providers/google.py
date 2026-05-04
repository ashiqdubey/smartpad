"""Google Gemini provider adapter — SPEC.MD section 10.

Adapts Google's generative language API to the Provider interface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

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

_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)


class GoogleProvider(Provider):
    """Adapter for the Google Gemini API."""

    name: str = "google"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        *,
        _client_factory: Any = None,
    ) -> None:
        self.api_key = api_key
        self.default_model = model
        self._client_factory = _client_factory

    def _make_client(self) -> httpx.AsyncClient:
        if self._client_factory is not None:
            return self._client_factory()
        return httpx.AsyncClient(timeout=_TIMEOUT)

    @staticmethod
    def _check_status(response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise ProviderAuthError("Invalid Google API key.")
        if response.status_code == 429:
            raise ProviderRateLimitError("Google rate limit hit.")
        if response.status_code >= 500:
            raise ProviderUnavailableError(f"Google server error: {response.status_code}")
        response.raise_for_status()

    @staticmethod
    def _to_google_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
        result = []
        for m in messages:
            if m.role == "system":
                continue
            role = "model" if m.role == "assistant" else "user"
            result.append({"role": role, "parts": [{"text": m.content}]})
        return result

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with self._make_client() as client:
                r = await client.get(f"{_API_BASE}/models?key={self.api_key}")
                self._check_status(r)
                data = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc
        return [
            ModelInfo(
                id=m["name"].split("/")[-1],
                name=m.get("displayName", m["name"]),
                context_length=m.get("inputTokenLimit"),
            )
            for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]

    async def chat(  # type: ignore[override]
        self,
        messages: list[ChatMessage],
        model: str = "",
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]:
        actual_model = model or self.default_model
        system_parts = [m.content for m in messages if m.role == "system"]
        payload: dict[str, Any] = {
            "contents": self._to_google_messages(messages),
            "generationConfig": {"temperature": temperature},
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        return self._oneshot_chat(payload, actual_model)

    async def _oneshot_chat(
        self, payload: dict[str, Any], model: str
    ) -> AsyncIterator[ChatChunk]:
        url = f"{_API_BASE}/models/{model}:generateContent?key={self.api_key}"
        try:
            async with self._make_client() as client:
                r = await client.post(url, json=payload)
                self._check_status(r)
                data = r.json()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise ProviderUnavailableError(str(exc)) from exc
        candidates = data.get("candidates", [])
        if not candidates:
            yield ChatChunk(delta="", finish_reason="stop")
            return
        content = "".join(
            part.get("text", "")
            for candidate in candidates
            for part in candidate.get("content", {}).get("parts", [])
        )
        yield ChatChunk(delta=content, finish_reason="stop")

    async def validate_credentials(self) -> bool:
        try:
            await self.list_models()
            return True
        except ProviderError:
            return False
