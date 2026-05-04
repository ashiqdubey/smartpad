"""Repository for Snippet entities with FTS5 search index maintenance."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Snippet


class SnippetsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, snippet: Snippet) -> Snippet:
        snippet.updated_at = datetime.now(UTC)
        if snippet.sync_version is not None:
            snippet.sync_version += 1
        self._s.add(snippet)
        await self._s.flush()
        await self._upsert_fts(snippet)
        return snippet

    async def get(self, snippet_id: str) -> Snippet | None:
        result = await self._s.execute(
            select(Snippet).where(Snippet.id == snippet_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        language: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Snippet]:
        q = select(Snippet)
        if not include_deleted:
            q = q.where(Snippet.deleted_at.is_(None))
        if language is not None:
            q = q.where(Snippet.language == language)
        q = q.order_by(Snippet.use_count.desc(), Snippet.created_at.desc())
        q = q.limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 50) -> list[Snippet]:
        rows = await self._s.execute(
            text(
                "SELECT item_id FROM search_index"
                " WHERE item_type = 'snippet' AND search_index MATCH :q"
                " ORDER BY rank LIMIT :lim"
            ),
            {"q": query, "lim": limit},
        )
        ids = [r[0] for r in rows]
        if not ids:
            return []
        result = await self._s.execute(
            select(Snippet).where(Snippet.id.in_(ids), Snippet.deleted_at.is_(None))
        )
        by_id = {s.id: s for s in result.scalars().all()}
        return [by_id[i] for i in ids if i in by_id]

    async def increment_use_count(self, snippet_id: str) -> Snippet | None:
        snippet = await self.get(snippet_id)
        if snippet is None or snippet.deleted_at is not None:
            return None
        snippet.use_count = (snippet.use_count or 0) + 1
        snippet.last_used_at = datetime.now(UTC)
        return await self.save(snippet)

    async def soft_delete(self, snippet_id: str) -> bool:
        snippet = await self.get(snippet_id)
        if snippet is None or snippet.deleted_at is not None:
            return False
        snippet.deleted_at = datetime.now(UTC)
        snippet.updated_at = datetime.now(UTC)
        self._s.add(snippet)
        await self._s.flush()
        await self._s.execute(
            text(
                "DELETE FROM search_index WHERE item_id = :id AND item_type = 'snippet'"
            ),
            {"id": snippet_id},
        )
        return True

    async def _upsert_fts(self, snippet: Snippet) -> None:
        await self._s.execute(
            text(
                "DELETE FROM search_index WHERE item_id = :id AND item_type = 'snippet'"
            ),
            {"id": snippet.id},
        )
        if snippet.deleted_at is None:
            await self._s.execute(
                text(
                    "INSERT INTO search_index(item_id, item_type, content, description)"
                    " VALUES (:id, 'snippet', :content, :desc)"
                ),
                {
                    "id": snippet.id,
                    "content": snippet.content,
                    "desc": snippet.description or "",
                },
            )
