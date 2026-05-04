"""Tests for the local API server — SPEC.md section 13."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from smartpad.api.server import create_app
from smartpad.db.engine import get_async_session, init_async_engine
from smartpad.db.migrations import run_migrations
from smartpad.db.models import Note
from smartpad.db.repositories.notes import NotesRepo


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Create a TestClient backed by a fresh in-memory DB."""
    db_path = tmp_path / "test.db"
    run_migrations(db_path)
    init_async_engine(db_path)

    @asynccontextmanager
    async def session_factory():
        async with get_async_session() as session:
            yield session

    app = create_app(session_factory=session_factory)
    return TestClient(app, raise_server_exceptions=True)


# ── /api/health ───────────────────────────────────────────────────────────────


def test_health_returns_200(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "device_id" in body


# ── /api/notes CRUD ───────────────────────────────────────────────────────────


def test_create_note(client: TestClient) -> None:
    resp = client.post("/api/notes", json={"content": "Test note content"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["content"] == "Test note content"
    assert "id" in body


def test_list_notes_empty(client: TestClient) -> None:
    resp = client.get("/api/notes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_notes_after_create(client: TestClient) -> None:
    client.post("/api/notes", json={"content": "Note A"})
    client.post("/api/notes", json={"content": "Note B"})
    resp = client.get("/api/notes")
    assert resp.status_code == 200
    notes = resp.json()
    assert len(notes) == 2
    contents = {n["content"] for n in notes}
    assert "Note A" in contents
    assert "Note B" in contents


def test_get_note_by_id(client: TestClient) -> None:
    create_resp = client.post("/api/notes", json={"content": "Specific note"})
    note_id = create_resp.json()["id"]

    resp = client.get(f"/api/notes/{note_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == note_id
    assert resp.json()["content"] == "Specific note"


def test_get_note_not_found(client: TestClient) -> None:
    resp = client.get(f"/api/notes/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_soft_delete_note(client: TestClient) -> None:
    create_resp = client.post("/api/notes", json={"content": "Delete me"})
    note_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/notes/{note_id}")
    assert del_resp.status_code == 204

    # Should no longer appear in list
    list_resp = client.get("/api/notes")
    ids = [n["id"] for n in list_resp.json()]
    assert note_id not in ids


def test_delete_nonexistent_note_404(client: TestClient) -> None:
    resp = client.delete(f"/api/notes/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_update_note(client: TestClient) -> None:
    create_resp = client.post("/api/notes", json={"content": "Original"})
    note_id = create_resp.json()["id"]

    update_resp = client.put(f"/api/notes/{note_id}", json={"content": "Updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["content"] == "Updated"


# ── /api/search ───────────────────────────────────────────────────────────────


def test_search_empty_query_returns_empty(client: TestClient) -> None:
    resp = client.get("/api/search?q=")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_with_data(client: TestClient) -> None:
    client.post("/api/notes", json={"content": "searchterm unique content here"})
    resp = client.get("/api/search?q=searchterm")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert any("searchterm" in r["snippet"] for r in results)


# ── /api/sync ─────────────────────────────────────────────────────────────────


def test_sync_status(client: TestClient) -> None:
    resp = client.get("/api/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "pending_changes" in body
    assert "paired_devices" in body


def test_sync_handshake(client: TestClient) -> None:
    resp = client.post(
        "/api/sync/handshake",
        json={"device_id": str(uuid.uuid4()), "device_name": "Test Device", "pairing_code": "1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] is True


def test_sync_delta(client: TestClient) -> None:
    resp = client.post(
        "/api/sync/delta",
        json={"device_id": str(uuid.uuid4()), "since_version": 0, "changes": []},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "changes" in body
