"""Provider registry — maps provider type strings to concrete classes.

To add a new provider: subclass Provider, then add to REGISTRY.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from smartpad.providers.anthropic import AnthropicProvider
from smartpad.providers.google import GoogleProvider
from smartpad.providers.openai_compatible import OpenAICompatibleProvider

if TYPE_CHECKING:
    from smartpad.providers.base import Provider

REGISTRY: dict[str, type] = {
    "OpenAICompatibleProvider": OpenAICompatibleProvider,
    "AnthropicProvider": AnthropicProvider,
    "GoogleProvider": GoogleProvider,
    # Phase 16: "ManagedLocalProvider": ManagedLocalProvider,
}

_active_provider: Provider | None = None


def get_active() -> Provider | None:
    return _active_provider


def set_active(provider: Provider) -> None:
    global _active_provider
    logger.info("Active provider set to '{}'", provider.name)
    _active_provider = provider


def build_provider(type_name: str, **kwargs: object) -> Provider:
    """Instantiate a provider from its type name and kwargs."""
    cls = REGISTRY.get(type_name)
    if cls is None:
        raise ValueError(f"Unknown provider type: {type_name!r}")
    return cls(**kwargs)  # type: ignore[return-value]
