"""Sync API routes — SPEC.md section 13.

Provides handshake, delta exchange, and status endpoints for
desktop-to-desktop WiFi sync.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class HandshakeRequest(BaseModel):
    device_id: str
    device_name: str
    pairing_code: str


class HandshakeResponse(BaseModel):
    accepted: bool
    server_device_id: str
    message: str


class DeltaRequest(BaseModel):
    device_id: str
    since_version: int
    changes: list[dict[str, Any]]


class DeltaResponse(BaseModel):
    changes: list[dict[str, Any]]
    current_version: int


class SyncStatus(BaseModel):
    last_sync_at: datetime | None
    pending_changes: int
    paired_devices: int


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/sync/handshake")
async def sync_handshake(
    body: HandshakeRequest,
    request: Request,
) -> HandshakeResponse:
    """Initiate pairing with a remote device.

    In v1 this is a stub — full pairing logic comes in v1.1.
    """
    # v1 stub: accept all handshakes (auth comes in v1.1)
    server_device_id = str(uuid.uuid4())
    return HandshakeResponse(
        accepted=True,
        server_device_id=server_device_id,
        message="Pairing accepted (v1 stub — no auth).",
    )


@router.post("/sync/delta")
async def sync_delta(
    body: DeltaRequest,
    request: Request,
) -> DeltaResponse:
    """Exchange deltas since last sync version.

    In v1 this is a stub — returns empty delta list.
    """
    return DeltaResponse(changes=[], current_version=0)


@router.get("/sync/status")
async def sync_status(request: Request) -> SyncStatus:
    """Return current sync status."""
    return SyncStatus(
        last_sync_at=None,
        pending_changes=0,
        paired_devices=0,
    )
