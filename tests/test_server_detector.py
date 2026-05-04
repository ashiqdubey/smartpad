"""Tests for server_detector — SPEC.md section 10."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from smartpad.providers.server_detector import DetectedServer, detect_local_servers


# ── Mock helpers ──────────────────────────────────────────────────────────────


def _make_client_factory(responses: dict[str, int]) -> Any:
    """Build an injectable async client that returns given status codes per URL.

    Args:
        responses: Mapping of URL substring → status code to return.
    """

    class _Client:
        async def get(self, url: str, **_: Any) -> MagicMock:
            for key, status in responses.items():
                if key in url:
                    resp = MagicMock(spec=httpx.Response)
                    resp.status_code = status
                    return resp
            # Default: connection refused
            raise httpx.ConnectError(f"No mock for {url}")

        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    return _Client()


# ── detect_local_servers ──────────────────────────────────────────────────────


async def test_detect_all_servers_down_returns_empty() -> None:
    """When all probes fail, return an empty list."""
    import httpx

    original_client = httpx.AsyncClient

    class _FailClient:
        def __init__(self, **_: Any) -> None:
            pass

        async def get(self, url: str, **__: Any) -> None:
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_FailClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    # Patch httpx.AsyncClient used inside detect_local_servers
    import smartpad.providers.server_detector as detector_mod

    original = detector_mod.httpx.AsyncClient

    class _PatchedClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def get(self, url: str, **__: Any) -> None:
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_PatchedClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    detector_mod.httpx.AsyncClient = _PatchedClient  # type: ignore[misc]
    try:
        result = await detect_local_servers()
        assert result == []
    finally:
        detector_mod.httpx.AsyncClient = original  # type: ignore[misc]


async def test_detect_ollama_detected() -> None:
    """Ollama at port 11434 is detected when it responds."""
    import smartpad.providers.server_detector as detector_mod

    original = detector_mod.httpx.AsyncClient

    class _OllamaClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def get(self, url: str, **__: Any) -> MagicMock:
            if "11434" in url:
                resp = MagicMock(spec=httpx.Response)
                resp.status_code = 200
                return resp
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_OllamaClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    detector_mod.httpx.AsyncClient = _OllamaClient  # type: ignore[misc]
    try:
        result = await detect_local_servers()
        names = [s.name for s in result]
        assert "Ollama" in names
        assert any(s.server_type == "ollama" for s in result)
    finally:
        detector_mod.httpx.AsyncClient = original  # type: ignore[misc]


async def test_detect_lmstudio_detected() -> None:
    """LM Studio at port 1234 is detected."""
    import smartpad.providers.server_detector as detector_mod

    original = detector_mod.httpx.AsyncClient

    class _LMStudioClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def get(self, url: str, **__: Any) -> MagicMock:
            if "1234" in url:
                resp = MagicMock(spec=httpx.Response)
                resp.status_code = 200
                return resp
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_LMStudioClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    detector_mod.httpx.AsyncClient = _LMStudioClient  # type: ignore[misc]
    try:
        result = await detect_local_servers()
        assert any(s.server_type == "lmstudio" for s in result)
    finally:
        detector_mod.httpx.AsyncClient = original  # type: ignore[misc]


async def test_detect_llama_server_detected() -> None:
    """Raw llama-server at port 8080 is detected."""
    import smartpad.providers.server_detector as detector_mod

    original = detector_mod.httpx.AsyncClient

    class _LlamaClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def get(self, url: str, **__: Any) -> MagicMock:
            if "8080" in url:
                resp = MagicMock(spec=httpx.Response)
                resp.status_code = 200
                return resp
            raise httpx.ConnectError("refused")

        async def __aenter__(self) -> "_LlamaClient":
            return self

        async def __aexit__(self, *_: object) -> None:
            pass

    detector_mod.httpx.AsyncClient = _LlamaClient  # type: ignore[misc]
    try:
        result = await detect_local_servers()
        assert any(s.server_type == "llama_server" for s in result)
    finally:
        detector_mod.httpx.AsyncClient = original  # type: ignore[misc]


def test_detected_server_dataclass() -> None:
    s = DetectedServer(name="Ollama", base_url="http://localhost:11434", server_type="ollama")
    assert s.name == "Ollama"
    assert s.base_url == "http://localhost:11434"
    assert s.server_type == "ollama"
