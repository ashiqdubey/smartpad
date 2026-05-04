"""Local FastAPI server — SPEC.md section 13.

Exposes REST endpoints for notes, tasks, reminders, snippets, search, chat,
and sync. Runs on 127.0.0.1:7823 alongside the desktop app.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from loguru import logger

from smartpad.api.routes import chat, notes, sync

_VERSION = "0.0.1"


def create_app(session_factory: Any | None = None) -> FastAPI:
    """Build and return the FastAPI application.

    Args:
        session_factory: Async context-manager factory that yields an AsyncSession.
            Stored in ``app.state.session_factory`` for route access.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("SmartPad API server starting up.")
        yield
        logger.info("SmartPad API server shutting down.")

    app = FastAPI(
        title="SmartPad Local API",
        version=_VERSION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
    )

    # Store the session factory so routes can access it
    app.state.session_factory = session_factory

    # Include route modules
    app.include_router(notes.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(sync.router, prefix="/api")

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        """Health check endpoint."""
        import uuid

        device_id = str(uuid.uuid4())  # Per-process ID; real app persists this
        return {"status": "ok", "version": _VERSION, "device_id": device_id}

    @app.get("/api/search")
    async def search(q: str = "", limit: int = 50, request: Any = None) -> list[dict[str, Any]]:
        """FTS5 search across all entity types."""

        factory = app.state.session_factory
        if factory is None or not q:
            return []
        from smartpad.core.search_service import search as fts_search

        async with factory() as session:
            results = await fts_search(q, session, limit=limit)
        return [
            {"item_id": r.item_id, "item_type": r.item_type, "snippet": r.snippet}
            for r in results
        ]

    return app


async def start_api_server(
    host: str,
    port: int,
    session_factory: Any,
) -> None:
    """Start the uvicorn server (blocks until shutdown).

    Args:
        host: Bind host (e.g. ``"127.0.0.1"``).
        port: Bind port (e.g. ``7823``).
        session_factory: Async session factory passed to the app.
    """
    app = create_app(session_factory)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.info("Starting SmartPad API on {}:{}", host, port)
    await server.serve()
