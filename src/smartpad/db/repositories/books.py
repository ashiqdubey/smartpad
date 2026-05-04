"""Repository for Book entities."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Book


class BooksRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, book: Book) -> Book:
        book.updated_at = datetime.now(UTC)
        if book.sync_version is not None:
            book.sync_version += 1
        self._s.add(book)
        await self._s.flush()
        return book

    async def get(self, book_id: str) -> Book | None:
        result = await self._s.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Book | None:
        result = await self._s.execute(
            select(Book).where(Book.name == name, Book.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        include_deleted: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Book]:
        q = select(Book)
        if not include_deleted:
            q = q.where(Book.deleted_at.is_(None))
        q = q.order_by(Book.name.asc()).limit(limit).offset(offset)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def get_or_create(self, name: str, *, ai_generated: bool = True) -> Book:
        """Return existing book by name, or create it."""
        existing = await self.get_by_name(name)
        if existing is not None:
            return existing
        book = Book(
            name=name,
            ai_generated=ai_generated,
            created_at=datetime.now(UTC),
        )
        return await self.save(book)

    async def soft_delete(self, book_id: str) -> bool:
        book = await self.get(book_id)
        if book is None or book.deleted_at is not None:
            return False
        book.deleted_at = datetime.now(UTC)
        book.updated_at = datetime.now(UTC)
        self._s.add(book)
        await self._s.flush()
        return True
