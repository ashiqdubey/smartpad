"""ManagedLocalProvider — owns the llama-server child process.

Wraps OpenAICompatibleProvider pointed at localhost:8080 (llama-server's
default OpenAI-compatible endpoint), plus lifecycle management: download
model, start server, monitor health, idle-unload.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from loguru import logger

from smartpad.model_manager.catalog import CatalogModel, get_by_id
from smartpad.model_manager.downloader import download_model, is_downloaded
from smartpad.model_manager.llama_server import LlamaServer, binary_path
from smartpad.providers.base import (
    ChatChunk,
    ChatMessage,
    ModelInfo,
    Provider,
    ProviderUnavailableError,
    ToolSchema,
)
from smartpad.providers.openai_compatible import OpenAICompatibleProvider


class ManagedLocalProvider(Provider):
    """Provider that manages a local llama-server process.

    Usage:
        provider = ManagedLocalProvider(models_dir, catalog_model_id)
        await provider.ensure_ready()   # download model + start server
        async for chunk in await provider.chat(...):
            ...
        await provider.shutdown()
    """

    name: str = "local"

    def __init__(
        self,
        models_dir: Path,
        model_id: str = "qwen3-1.7b-q4",
        port: int = 8080,
        idle_timeout_minutes: int = 30,
    ) -> None:
        self._models_dir = models_dir
        self._model_id = model_id
        self._port = port
        self._idle_timeout = idle_timeout_minutes
        self._catalog_model: CatalogModel | None = get_by_id(model_id)
        self._server: LlamaServer | None = None
        self._openai: OpenAICompatibleProvider | None = None
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready and self._server is not None and self._server.is_running

    async def ensure_ready(
        self,
        on_download_progress: Any = None,
    ) -> bool:
        """Download model if needed, then start llama-server."""
        if self.is_ready:
            return True

        if self._catalog_model is None:
            logger.error("Unknown catalog model ID: {}", self._model_id)
            return False

        model_path = self._models_dir / self._catalog_model.filename

        # Download if needed
        if not is_downloaded(self._catalog_model, self._models_dir):
            logger.info("Downloading model {}", self._catalog_model.filename)
            try:
                await download_model(
                    self._catalog_model,
                    self._models_dir,
                    on_progress=on_download_progress,
                )
            except Exception as exc:
                logger.error("Model download failed: {}", exc)
                return False

        # Check binary
        if not binary_path(self._models_dir).exists():
            logger.error(
                "llama-server binary not found. Download it to {}",
                binary_path(self._models_dir),
            )
            return False

        # Start server
        self._server = LlamaServer(
            models_dir=self._models_dir,
            model_path=model_path,
            port=self._port,
            idle_timeout_minutes=self._idle_timeout,
            on_idle_unload=self._on_server_idle,
        )
        if not await self._server.start():
            return False

        self._openai = OpenAICompatibleProvider(
            base_url=f"http://127.0.0.1:{self._port}",
            api_key=None,
            name="local",
        )
        self._ready = True
        return True

    async def shutdown(self) -> None:
        if self._server:
            await self._server.stop()
        self._ready = False

    def _on_server_idle(self) -> None:
        self._ready = False
        logger.info("ManagedLocalProvider: server unloaded due to idle")

    # ── Provider interface ────────────────────────────────────────────────────

    async def list_models(self) -> list[ModelInfo]:
        if not self.is_ready or self._openai is None:
            if self._catalog_model:
                return [ModelInfo(
                    id=self._catalog_model.filename,
                    name=self._catalog_model.display_name,
                    context_length=self._catalog_model.context_length,
                )]
            return []
        return await self._openai.list_models()

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str = "",
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]:
        if not self.is_ready or self._openai is None:
            raise ProviderUnavailableError(
                "Local model not loaded. Call ensure_ready() first."
            )
        if self._server:
            self._server.touch_activity()

        actual_model = model or (
            self._catalog_model.filename if self._catalog_model else "local"
        )
        return await self._openai.chat(
            messages=messages,
            model=actual_model,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

    async def validate_credentials(self) -> bool:
        return self.is_ready
