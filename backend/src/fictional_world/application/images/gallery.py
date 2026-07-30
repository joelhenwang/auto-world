"""Gallery listing service (S4-IMG-003).

Handbook: 16 §13.4.  Gallery items are illustrative; they never mutate canon.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.images.persistence import GalleryItemRecord


class GalleryService:
    """Read-only gallery queries."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        display_status: str | None = None,
        source_event_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[GalleryItemRecord]:
        """Return gallery items for a world, newest first."""
        async with self._uow as uow:
            return await uow.gallery_items.list_for_world(
                world_id,
                display_status=display_status,
                source_event_id=source_event_id,
                limit=limit,
                offset=offset,
            )

    async def list_approved(
        self,
        world_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[GalleryItemRecord]:
        """Return items with display_status in (auto_selected, user_selected)."""
        async with self._uow as uow:
            auto = await uow.gallery_items.list_for_world(
                world_id,
                display_status="auto_selected",
                limit=limit,
                offset=offset,
            )
            user = await uow.gallery_items.list_for_world(
                world_id,
                display_status="user_selected",
                limit=limit,
                offset=offset,
            )
        combined = list(auto) + list(user)
        combined.sort(key=lambda i: i.created_at or "", reverse=True)
        return combined[:limit]
