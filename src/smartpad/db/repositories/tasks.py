"""Repository for Task entities with FTS5 search index maintenance."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Task


class TasksRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, task: Task) -> Task:
        task.updated_at = datetime.now(UTC)
        if task.sync_version is not None:
            task.sync_version += 1
        self._s.add(task)
        await self._s.flush()
        await self._upsert_fts(task)
        return task

    async def get(self, task_id: str) -> Task | None:
        result = await self._s.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: str | None = None,
        book_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Task]:
        q = select(Task)
        if not include_deleted:
            q = q.where(Task.deleted_at.is_(None))
        if status is not None:
            q = q.where(Task.status == status)
        if book_id is not None:
            q = q.where(Task.book_id == book_id)
        q = q.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 50) -> list[Task]:
        rows = await self._s.execute(
            text(
                "SELECT item_id FROM search_index"
                " WHERE item_type = 'task' AND search_index MATCH :q"
                " ORDER BY rank LIMIT :lim"
            ),
            {"q": query, "lim": limit},
        )
        ids = [r[0] for r in rows]
        if not ids:
            return []
        result = await self._s.execute(
            select(Task).where(Task.id.in_(ids), Task.deleted_at.is_(None))
        )
        by_id = {t.id: t for t in result.scalars().all()}
        return [by_id[i] for i in ids if i in by_id]

    async def mark_done(self, task_id: str) -> Task | None:
        task = await self.get(task_id)
        if task is None or task.deleted_at is not None:
            return None
        task.status = "done"
        task.completed_at = datetime.now(UTC)
        return await self.save(task)

    async def soft_delete(self, task_id: str) -> bool:
        task = await self.get(task_id)
        if task is None or task.deleted_at is not None:
            return False
        task.deleted_at = datetime.now(UTC)
        task.updated_at = datetime.now(UTC)
        self._s.add(task)
        await self._s.flush()
        await self._s.execute(
            text("DELETE FROM search_index WHERE item_id = :id AND item_type = 'task'"),
            {"id": task_id},
        )
        return True

    async def _upsert_fts(self, task: Task) -> None:
        await self._s.execute(
            text("DELETE FROM search_index WHERE item_id = :id AND item_type = 'task'"),
            {"id": task.id},
        )
        if task.deleted_at is None:
            await self._s.execute(
                text(
                    "INSERT INTO search_index(item_id, item_type, content, description)"
                    " VALUES (:id, 'task', :content, '')"
                ),
                {"id": task.id, "content": task.content},
            )
