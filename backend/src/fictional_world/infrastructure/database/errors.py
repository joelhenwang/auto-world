"""Persistence-layer exceptions normalized at repository boundaries."""

from __future__ import annotations

from fictional_world.domain.common.errors import ConcurrencyConflict, DomainError, UnknownTarget


class PersistenceError(DomainError):
    """Unexpected persistence failure."""


class NotFoundError(UnknownTarget):
    """Requested aggregate row was missing."""

    def __init__(self, *, entity: str, entity_id: str) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} not found: {entity_id}")


class OptimisticConcurrencyError(ConcurrencyConflict):
    """Optimistic version mismatch on update."""

    def __init__(self, *, entity: str, entity_id: str, expected_version: int) -> None:
        self.entity = entity
        self.entity_id = entity_id
        self.expected_version = expected_version
        super().__init__(
            f"concurrency conflict on {entity} {entity_id}: expected_version={expected_version}"
        )
