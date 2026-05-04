"""Repository for Message (chat history) entities."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Message


class ChatRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, message: Message) -> Message:
        message.updated_at = datetime.now(UTC)
        if message.sync_version is not None:
            message.sync_version += 1
        self._s.add(message)
        await self._s.flush()
        return message

    async def get(self, message_id: str) -> Message | None:
        result = await self._s.execute(
            select(Message).where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        kind: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        q = select(Message)
        if not include_deleted:
            q = q.where(Message.deleted_at.is_(None))
        if kind is not None:
            q = q.where(Message.kind == kind)
        q = q.order_by(Message.created_at.desc()).limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def get_conversation(self, limit: int = 50) -> list[Message]:
        """Return most-recent chat messages in chronological order (oldest first)."""
        result = await self._s.execute(
            select(Message)
            .where(
                Message.deleted_at.is_(None),
                Message.kind.in_(["chat", "tool_result", "error"]),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def soft_delete(self, message_id: str) -> bool:
        message = await self.get(message_id)
        if message is None or message.deleted_at is not None:
            return False
        message.deleted_at = datetime.now(UTC)
        message.updated_at = datetime.now(UTC)
        self._s.add(message)
        await self._s.flush()
        return True
