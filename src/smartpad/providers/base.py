"""Provider abstraction layer — SPEC.md section 10.

All AI backends (cloud, local, custom) implement this interface.
The rest of the app talks exclusively to these abstractions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelInfo:
    id: str
    name: str
    context_length: int | None = None


@dataclass
class ChatMessage:
    role: str  # user | assistant | system | tool
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None  # when role == "tool"

    def to_api_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ChatChunk:
    delta: str = ""
    finish_reason: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: dict[str, int] | None = None


class ProviderError(Exception):
    """Base class for provider errors surfaced to the UI as error bubbles."""


class ProviderAuthError(ProviderError):
    """Invalid or missing API credentials."""


class ProviderRateLimitError(ProviderError):
    """Rate limit hit — caller should back off and retry."""


class ProviderUnavailableError(ProviderError):
    """Provider endpoint unreachable or returned a server error."""


class Provider(ABC):
    """Abstract base for all AI provider adapters."""

    name: str

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return available models for this provider."""

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]:
        """Stream chat completions as ChatChunk objects."""

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Return True if the provider can be reached with current credentials."""
