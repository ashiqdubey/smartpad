"""Repository for Provider configuration entities."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smartpad.db.models import Provider


class ProvidersRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, provider: Provider) -> Provider:
        provider.updated_at = datetime.now(UTC)
        self._s.add(provider)
        await self._s.flush()
        return provider

    async def get(self, provider_id: str) -> Provider | None:
        result = await self._s.execute(
            select(Provider).where(Provider.id == provider_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Provider | None:
        result = await self._s.execute(
            select(Provider).where(Provider.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> Provider | None:
        """Return the single active provider (is_active=True), or None."""
        result = await self._s.execute(
            select(Provider).where(Provider.is_active == True, Provider.enabled == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        enabled_only: bool = False,
    ) -> list[Provider]:
        q = select(Provider)
        if enabled_only:
            q = q.where(Provider.enabled == True)  # noqa: E712
        q = q.order_by(Provider.name.asc())
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def set_active(self, provider_id: str) -> Provider | None:
        """Deactivate all providers, then set the given one as active."""
        all_providers = await self.list()
        for p in all_providers:
            if p.is_active:
                p.is_active = False
                self._s.add(p)

        target = await self.get(provider_id)
        if target is None:
            return None
        target.is_active = True
        target.enabled = True
        return await self.save(target)

    async def delete(self, provider_id: str) -> bool:
        """Hard-delete a provider (providers have no soft-delete per spec)."""
        provider = await self.get(provider_id)
        if provider is None:
            return False
        await self._s.delete(provider)
        await self._s.flush()
        return True
