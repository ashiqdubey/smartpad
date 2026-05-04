"""Repository for Reminder entities with FTS5 search index maintenance."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Reminder


class RemindersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, reminder: Reminder) -> Reminder:
        reminder.updated_at = datetime.now(UTC)
        if reminder.sync_version is not None:
            reminder.sync_version += 1
        self._s.add(reminder)
        await self._s.flush()
        await self._upsert_fts(reminder)
        return reminder

    async def get(self, reminder_id: str) -> Reminder | None:
        result = await self._s.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        notified: bool | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Reminder]:
        q = select(Reminder)
        if not include_deleted:
            q = q.where(Reminder.deleted_at.is_(None))
        if notified is not None:
            q = q.where(Reminder.notified == notified)
        q = q.order_by(Reminder.trigger_at.asc()).limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def get_due(self, as_of: datetime | None = None) -> list[Reminder]:
        """Return pending (un-notified, non-deleted) reminders due by as_of."""
        cutoff = as_of or datetime.now(UTC)
        result = await self._s.execute(
            select(Reminder).where(
                Reminder.deleted_at.is_(None),
                Reminder.notified == False,  # noqa: E712
                Reminder.trigger_at <= cutoff,
            )
        )
        return list(result.scalars().all())

    async def mark_notified(self, reminder_id: str) -> Reminder | None:
        reminder = await self.get(reminder_id)
        if reminder is None or reminder.deleted_at is not None:
            return None
        reminder.notified = True
        reminder.notified_at = datetime.now(UTC)
        return await self.save(reminder)

    async def soft_delete(self, reminder_id: str) -> bool:
        reminder = await self.get(reminder_id)
        if reminder is None or reminder.deleted_at is not None:
            return False
        reminder.deleted_at = datetime.now(UTC)
        reminder.updated_at = datetime.now(UTC)
        self._s.add(reminder)
        await self._s.flush()
        await self._s.execute(
            text(
                "DELETE FROM search_index WHERE item_id = :id AND item_type = 'reminder'"
            ),
            {"id": reminder_id},
        )
        return True

    async def _upsert_fts(self, reminder: Reminder) -> None:
        await self._s.execute(
            text(
                "DELETE FROM search_index WHERE item_id = :id AND item_type = 'reminder'"
            ),
            {"id": reminder.id},
        )
        if reminder.deleted_at is None:
            await self._s.execute(
                text(
                    "INSERT INTO search_index(item_id, item_type, content, description)"
                    " VALUES (:id, 'reminder', :content, '')"
                ),
                {"id": reminder.id, "content": reminder.content},
            )
