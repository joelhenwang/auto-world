"""Pure hook close / expire helpers (Stage 2 ``hook`` table; Stage 3 slots)."""

from __future__ import annotations

from collections.abc import Sequence

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.persistence import HookPersistenceRecord
from fictional_world.domain.world.config import WorldSlotConfig
from fictional_world.domain.world.slots import can_activate_secondary_hook
from fictional_world.domain.world.statuses import HookStatus

_HOOK_TRANSITIONS: dict[HookStatus, frozenset[HookStatus]] = {
    HookStatus.DORMANT: frozenset({HookStatus.ACTIVE, HookStatus.RESOLVED, HookStatus.ABANDONED}),
    HookStatus.ACTIVE: frozenset({HookStatus.DORMANT, HookStatus.RESOLVED, HookStatus.ABANDONED}),
    HookStatus.RESOLVED: frozenset(),
    HookStatus.ABANDONED: frozenset(),
}


def activate_hook(
    hook: HookPersistenceRecord,
    hooks: Sequence[HookPersistenceRecord],
    *,
    config: WorldSlotConfig | None = None,
) -> HookPersistenceRecord:
    """Activate a hook if the secondary-hook slot budget allows (default max 2)."""
    current = HookStatus(hook.status)
    target = HookStatus.ACTIVE
    _assert_transition(current, target)
    if not can_activate_secondary_hook(hooks, candidate=hook, config=config):
        raise InvalidAction("cannot activate hook: active secondary hook slots already full")
    return hook.model_copy(update={"status": target.value, "version": hook.version + 1})


def close_hook(hook: HookPersistenceRecord) -> HookPersistenceRecord:
    """Close a hook as resolved (causal closure)."""
    current = HookStatus(hook.status)
    target = HookStatus.RESOLVED
    _assert_transition(current, target)
    return hook.model_copy(update={"status": target.value, "version": hook.version + 1})


def expire_hook(
    hook: HookPersistenceRecord,
    *,
    cooldown_until_phase: int | None = None,
) -> HookPersistenceRecord:
    """Expire a hook without resolution (maps to ``abandoned`` under Stage 2 constraint).

    DB vocabulary has no ``expired`` status; abandonment records expiry.
    Optional cooldown prevents lazy reactivation during the same window.
    """
    current = HookStatus(hook.status)
    target = HookStatus.ABANDONED
    _assert_transition(current, target)
    updates: dict[str, object] = {
        "status": target.value,
        "version": hook.version + 1,
    }
    if cooldown_until_phase is not None:
        if cooldown_until_phase < 0:
            raise InvalidAction("cooldown_until_phase must be >= 0")
        updates["cooldown_until_phase"] = cooldown_until_phase
    return hook.model_copy(update=updates)


def _assert_transition(current: HookStatus, target: HookStatus) -> None:
    if current == target:
        return
    allowed = _HOOK_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransition(entity="hook", from_state=current.value, to_state=target.value)
