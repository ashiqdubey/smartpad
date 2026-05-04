"""Notes CRUD API routes — SPEC.md section 13."""
# ruff: noqa: B008  -- Depends() in route signature is FastAPI's standard pattern

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from smartpad.db.models import Note
from smartpad.db.repositories.notes import NotesRepo

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class NoteIn(BaseModel):
    content: str
    book_id: str | None = None
    tags: str | None = None
    pinned: bool = False
    ai_level: int | None = None


class NoteOut(BaseModel):
    id: str
    content: str
    original_content: str
    book_id: str | None
    tags: str | None
    pinned: bool
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_orm(cls, n: Note) -> NoteOut:
        return cls(
            id=n.id,
            content=n.content,
            original_content=n.original_content,
            book_id=n.book_id,
            tags=n.tags,
            pinned=n.pinned,
            created_at=n.created_at,
            updated_at=n.updated_at,
        )


# ── Dependency ────────────────────────────────────────────────────────────────


async def _get_session(request: Request) -> Any:
    """Yield an async session from the app-level session factory."""
    factory = request.app.state.session_factory
    if factory is None:
        raise HTTPException(status_code=503, detail="Database not initialised.")
    async with factory() as session:
        yield session


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/notes")
async def list_notes(
    book_id: str | None = None,
    pinned: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    session: Any = Depends(_get_session),
) -> list[NoteOut]:
    repo = NotesRepo(session)
    notes = await repo.list(book_id=book_id, pinned=pinned, limit=limit, offset=offset)
    return [NoteOut.from_orm(n) for n in notes]


@router.get("/notes/{note_id}")
async def get_note(note_id: str, session: Any = Depends(_get_session)) -> NoteOut:
    repo = NotesRepo(session)
    note = await repo.get(note_id)
    if note is None or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found.")
    return NoteOut.from_orm(note)


@router.post("/notes", status_code=201)
async def create_note(body: NoteIn, session: Any = Depends(_get_session)) -> NoteOut:
    now = datetime.now(UTC)
    note = Note(
        id=str(uuid.uuid4()),
        content=body.content,
        original_content=body.content,
        book_id=body.book_id,
        tags=body.tags,
        pinned=body.pinned,
        ai_level_applied=body.ai_level,
        created_at=now,
        sync_version=0,
    )
    repo = NotesRepo(session)
    saved = await repo.save(note)
    await session.commit()
    return NoteOut.from_orm(saved)


@router.put("/notes/{note_id}")
async def update_note(
    note_id: str, body: NoteIn, session: Any = Depends(_get_session)
) -> NoteOut:
    repo = NotesRepo(session)
    note = await repo.get(note_id)
    if note is None or note.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Note not found.")
    note.content = body.content
    note.book_id = body.book_id
    note.tags = body.tags
    note.pinned = body.pinned
    saved = await repo.save(note)
    await session.commit()
    return NoteOut.from_orm(saved)


@router.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: str, session: Any = Depends(_get_session)) -> None:
    repo = NotesRepo(session)
    deleted = await repo.soft_delete(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found.")
    await session.commit()
