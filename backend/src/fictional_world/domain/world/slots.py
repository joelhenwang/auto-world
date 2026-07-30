"""Active arc and secondary-hook slot rules (pure / deterministic)."""

from __future__ import annotations

from collections.abc import Sequence

from fictional_world.domain.continuity.persistence import HookPersistenceRecord
from fictional_world.domain.stage3.persistence import ArcPersistenceRecord
from fictional_world.domain.world.config import WorldSlotConfig
from fictional_world.domain.world.statuses import (
    ACTIVE_HOOK_STATUS,
    ArcScope,
    ArcStatus,
    HookStatus,
)


def count_active_major_arcs(arcs: Sequence[ArcPersistenceRecord]) -> int:
    """Count arcs occupying the active major-arc slot."""
    return sum(
        1
        for arc in arcs
        if arc.status == ArcStatus.ACTIVE.value and arc.arc_scope == ArcScope.MAJOR.value
    )


def count_active_secondary_hooks(hooks: Sequence[HookPersistenceRecord]) -> int:
    """Count hooks occupying secondary-hook slots (Stage 2 ``hook`` table)."""
    return sum(1 for hook in hooks if hook.status == ACTIVE_HOOK_STATUS.value)


def can_activate_major_arc(
    arcs: Sequence[ArcPersistenceRecord],
    *,
    candidate: ArcPersistenceRecord | None = None,
    config: WorldSlotConfig | None = None,
) -> bool:
    """Return True when a major arc may become active without exceeding the slot.

    If ``candidate`` is already the sole active major arc, returns True (idempotent).
    Secondary-scope arcs never consume the major slot.
    """
    cfg = config or WorldSlotConfig()
    if candidate is not None and candidate.arc_scope != ArcScope.MAJOR.value:
        return False
    active = [
        arc
        for arc in arcs
        if arc.status == ArcStatus.ACTIVE.value and arc.arc_scope == ArcScope.MAJOR.value
    ]
    if candidate is not None:
        # Candidate already active: always allowed (no double occupancy).
        if candidate.status == ArcStatus.ACTIVE.value:
            return (
                candidate.arc_scope == ArcScope.MAJOR.value
                and len(active) <= cfg.max_active_major_arcs
            )
        # Exclude candidate if present as non-active from occupancy check.
        active = [arc for arc in active if arc.id != candidate.id]
    return len(active) < cfg.max_active_major_arcs


def can_activate_secondary_hook(
    hooks: Sequence[HookPersistenceRecord],
    *,
    candidate: HookPersistenceRecord | None = None,
    config: WorldSlotConfig | None = None,
) -> bool:
    """Return True when a secondary hook may become active (max two by default)."""
    cfg = config or WorldSlotConfig()
    active = [hook for hook in hooks if hook.status == HookStatus.ACTIVE.value]
    if candidate is not None and candidate.status == HookStatus.ACTIVE.value:
        return len(active) <= cfg.max_active_secondary_hooks
    if candidate is not None:
        active = [hook for hook in active if hook.id != candidate.id]
    return len(active) < cfg.max_active_secondary_hooks
