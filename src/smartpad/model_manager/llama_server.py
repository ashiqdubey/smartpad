"""llama-server subprocess lifecycle manager — SPEC.MD section 16.

Downloads the correct llama-server binary for the current OS/arch,
starts it as a child process, monitors it, and shuts it down on request.
Also implements idle-unload: after 30 minutes without chat activity the
server is stopped; it restarts on the next chat request.
"""

from __future__ import annotations

import asyncio
import platform
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import httpx
from loguru import logger

# ── Binary download URLs (from llama.cpp GitHub releases) ────────────────────

_LLAMA_VERSION = "b5610"  # pin a known-good release

_BINARY_URLS: dict[str, str] = {
    "windows-x86_64": (
        f"https://github.com/ggerganov/llama.cpp/releases/download/{_LLAMA_VERSION}"
        f"/llama-{_LLAMA_VERSION}-bin-win-avx2-x64.zip"
    ),
    "darwin-arm64": (
        f"https://github.com/ggerganov/llama.cpp/releases/download/{_LLAMA_VERSION}"
        f"/llama-{_LLAMA_VERSION}-bin-macos-arm64.zip"
    ),
    "darwin-x86_64": (
        f"https://github.com/ggerganov/llama.cpp/releases/download/{_LLAMA_VERSION}"
        f"/llama-{_LLAMA_VERSION}-bin-macos-x64.zip"
    ),
    "linux-x86_64": (
        f"https://github.com/ggerganov/llama.cpp/releases/download/{_LLAMA_VERSION}"
        f"/llama-{_LLAMA_VERSION}-bin-ubuntu-x64.zip"
    ),
}


def _binary_name() -> str:
    return "llama-server.exe" if sys.platform == "win32" else "llama-server"


def _platform_key() -> str:
    system = sys.platform
    machine = platform.machine().lower()
    if system == "win32":
        return "windows-x86_64"
    if system == "darwin":
        return "darwin-arm64" if "arm" in machine or "aarch" in machine else "darwin-x86_64"
    return "linux-x86_64"


def get_binary_url() -> str:
    return _BINARY_URLS.get(_platform_key(), _BINARY_URLS["linux-x86_64"])


def binary_path(models_dir: Path) -> Path:
    return models_dir / _binary_name()


# ── LlamaServer ───────────────────────────────────────────────────────────────

class LlamaServer:
    """Manages a llama-server child process.

    Lifecycle:
        server = LlamaServer(models_dir, model_path, port=8080)
        await server.start()    # launches process, waits for /health
        await server.stop()     # terminates process
        server.touch_activity() # reset idle timer
    """

    def __init__(
        self,
        models_dir: Path,
        model_path: Path,
        port: int = 8080,
        idle_timeout_minutes: int = 30,
        on_idle_unload: Callable[[], None] | None = None,
    ) -> None:
        self._models_dir = models_dir
        self._model_path = model_path
        self._port = port
        self._idle_timeout = idle_timeout_minutes * 60
        self._on_idle_unload = on_idle_unload
        self._process: subprocess.Popen[bytes] | None = None
        self._last_activity = time.monotonic()
        self._idle_task: asyncio.Task[None] | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def touch_activity(self) -> None:
        self._last_activity = time.monotonic()

    async def start(self, timeout: float = 30.0) -> bool:
        """Start llama-server and wait until /health returns 200."""
        binary = binary_path(self._models_dir)
        if not binary.exists():
            logger.error("llama-server binary not found at {}", binary)
            return False

        cmd = [
            str(binary),
            "--model", str(self._model_path),
            "--port", str(self._port),
            "--host", "127.0.0.1",
            "--ctx-size", "4096",
        ]
        logger.info("Starting llama-server: {}", " ".join(cmd))

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            logger.error("llama-server binary not executable at {}", binary)
            return False

        if not await self._wait_healthy(timeout):
            logger.error("llama-server failed to start within {}s", timeout)
            await self.stop()
            return False

        logger.success("llama-server started on port {}", self._port)
        self._start_idle_monitor()
        return True

    async def stop(self) -> None:
        if self._idle_task:
            self._idle_task.cancel()
            self._idle_task = None
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
            logger.info("llama-server stopped")

    async def _wait_healthy(self, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        async with httpx.AsyncClient(timeout=2.0) as client:
            while time.monotonic() < deadline:
                try:
                    r = await client.get(f"{self.base_url}/health")
                    if r.status_code == 200:
                        return True
                except Exception:
                    pass
                await asyncio.sleep(0.5)
        return False

    def _start_idle_monitor(self) -> None:
        async def _monitor() -> None:
            while self.is_running:
                await asyncio.sleep(60)
                idle = time.monotonic() - self._last_activity
                if idle >= self._idle_timeout:
                    logger.info("llama-server idle for {:.0f}s — unloading", idle)
                    await self.stop()
                    if self._on_idle_unload:
                        self._on_idle_unload()
                    return

        loop = asyncio.get_event_loop()
        if loop.is_running():
            self._idle_task = loop.create_task(_monitor())
