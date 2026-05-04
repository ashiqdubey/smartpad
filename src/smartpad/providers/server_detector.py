"""Local AI server auto-detection — SPEC.md section 10.

Probes well-known localhost ports to discover running AI servers.
Never raises — always returns a (possibly empty) list.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from loguru import logger

_PROBE_TIMEOUT = httpx.Timeout(connect=1.0, read=2.0, write=1.0, pool=1.0)

_PROBES: list[tuple[str, str, str]] = [
    # (name, base_url, server_type)
    ("Ollama", "http://localhost:11434", "ollama"),
    ("LM Studio", "http://localhost:1234", "lmstudio"),
    ("llama-server", "http://localhost:8080", "llama_server"),
]


@dataclass
class DetectedServer:
    """A discovered local AI server."""

    name: str
    base_url: str
    server_type: str  # ollama | lmstudio | llama_server


async def detect_local_servers() -> list[DetectedServer]:
    """Probe common localhost ports for running AI servers.

    Uses a 1-second connect timeout. Never raises — returns [] on failure.

    Returns:
        List of DetectedServer for each reachable server.
    """
    found: list[DetectedServer] = []

    async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT) as client:
        for name, base_url, server_type in _PROBES:
            try:
                # Ollama: GET /api/tags; LM Studio / llama-server: GET /v1/models
                probe_url = (
                    f"{base_url}/api/tags"
                    if server_type == "ollama"
                    else f"{base_url}/v1/models"
                )
                response = await client.get(probe_url)
                # Any response (even error) means the server is listening
                if response.status_code < 600:
                    logger.info("Detected local server '{}' at {}", name, base_url)
                    found.append(
                        DetectedServer(name=name, base_url=base_url, server_type=server_type)
                    )
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.RemoteProtocolError,
                OSError,
            ):
                logger.debug("No server found at {} ({})", base_url, name)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Probe error for {} ({}): {}", base_url, name, exc)

    return found
