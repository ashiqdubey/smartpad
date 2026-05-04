"""Repository for Note entities with FTS5 search index maintenance."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Note


class NotesRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, note: Note) -> Note:
        """Insert or update a Note and keep the FTS5 index in sync."""
        note.updated_at = datetime.now(UTC)
        if note.sync_version is not None:
            note.sync_version += 1
        self._s.add(note)
        await self._s.flush()
        await self._upsert_fts(note)
        return note

    async def get(self, note_id: str) -> Note | None:
        result = await self._s.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        book_id: str | None = None,
        pinned: bool | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Note]:
        q = select(Note)
        if not include_deleted:
            q = q.where(Note.deleted_at.is_(None))
        if book_id is not None:
            q = q.where(Note.book_id == book_id)
        if pinned is not None:
            q = q.where(Note.pinned == pinned)
        q = q.order_by(Note.created_at.desc()).limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 50) -> list[Note]:
        """FTS5 full-text search across notes content."""
        rows = await self._s.execute(
            text(
                "SELECT item_id FROM search_index"
                " WHERE item_type = 'note' AND search_index MATCH :q"
                " ORDER BY rank LIMIT :lim"
            ),
            {"q": query, "lim": limit},
        )
        ids = [r[0] for r in rows]
        if not ids:
            return []
        result = await self._s.execute(
            select(Note).where(Note.id.in_(ids), Note.deleted_at.is_(None))
        )
        by_id = {n.id: n for n in result.scalars().all()}
        return [by_id[i] for i in ids if i in by_id]

    async def soft_delete(self, note_id: str) -> bool:
        """Mark a note deleted and remove from search index."""
        note = await self.get(note_id)
        if note is None or note.deleted_at is not None:
            return False
        note.deleted_at = datetime.now(UTC)
        note.updated_at = datetime.now(UTC)
        self._s.add(note)
        await self._s.flush()
        await self._s.execute(
            text("DELETE FROM search_index WHERE item_id = :id AND item_type = 'note'"),
            {"id": note_id},
        )
        return True

    async def _upsert_fts(self, note: Note) -> None:
        await self._s.execute(
            text(
                "DELETE FROM search_index WHERE item_id = :id AND item_type = 'note'"
            ),
            {"id": note.id},
        )
        if note.deleted_at is None:
            await self._s.execute(
                text(
                    "INSERT INTO search_index(item_id, item_type, content, description)"
                    " VALUES (:id, 'note', :content, '')"
                ),
                {"id": note.id, "content": note.content},
            )
