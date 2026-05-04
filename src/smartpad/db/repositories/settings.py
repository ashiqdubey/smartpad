"""Repository for key-value Setting store."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Setting


class SettingsRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, key: str) -> object | None:
        """Return the stored value for key, or None if not set."""
        result = await self._s.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        return row.value if row is not None else None

    async def set(self, key: str, value: object) -> None:
        """Upsert a key-value pair."""
        result = await self._s.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            row = Setting(key=key, value=value)
        else:
            row.value = value
        self._s.add(row)
        await self._s.flush()

    async def delete(self, key: str) -> bool:
        result = await self._s.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            return False
        await self._s.delete(row)
        await self._s.flush()
        return True

    async def get_all(self) -> dict[str, object]:
        result = await self._s.execute(select(Setting))
        return {row.key: row.value for row in result.scalars().all()}
