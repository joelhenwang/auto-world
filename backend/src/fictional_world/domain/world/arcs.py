"""Pure arc lifecycle helpers (Director proposes; services validate/apply)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.stage3.persistence import ArcPersistenceRecord
from fictional_world.domain.world.config import WorldSlotConfig
from fictional_world.domain.world.slots import can_activate_major_arc
from fictional_world.domain.world.statuses import (
    ARC_TERMINAL_STATUSES,
    ArcScope,
    ArcStatus,
)

_ARC_TRANSITIONS: dict[ArcStatus, frozenset[ArcStatus]] = {
    ArcStatus.DORMANT: frozenset(
        {ArcStatus.ACTIVE, ArcStatus.ABANDONED, ArcStatus.FAILED, ArcStatus.RESOLVED}
    ),
    ArcStatus.ACTIVE: frozenset(
        {
            ArcStatus.DORMANT,
            ArcStatus.RESOLVED,
            ArcStatus.FAILED,
            ArcStatus.ABANDONED,
        }
    ),
    ArcStatus.RESOLVED: frozenset(),
    ArcStatus.FAILED: frozenset(),
    ArcStatus.ABANDONED: frozenset(),
}


def activate_arc(
    arc: ArcPersistenceRecord,
    arcs: Sequence[ArcPersistenceRecord],
    *,
    start_phase_index: int,
    config: WorldSlotConfig | None = None,
) -> ArcPersistenceRecord:
    """Activate an arc if slot rules and transitions allow.

    Major arcs require an empty major slot (handbook one-active-major rule).
    Secondary arcs do not consume the major slot.
    """
    if start_phase_index < 0:
        raise InvalidAction("start_phase_index must be >= 0")
    current = ArcStatus(arc.status)
    target = ArcStatus.ACTIVE
    _assert_transition(current, target)
    if arc.arc_scope == ArcScope.MAJOR.value and not can_activate_major_arc(
        arcs, candidate=arc, config=config
    ):
        raise InvalidAction("cannot activate major arc: active major arc slot already occupied")
    return arc.model_copy(
        update={
            "status": target.value,
            "start_phase_index": start_phase_index
            if arc.start_phase_index is None
            else arc.start_phase_index,
            "version": arc.version + 1,
        }
    )


def advance_arc_progress(
    arc: ArcPersistenceRecord,
    *,
    delta: Decimal,
    phase_index: int | None = None,
) -> ArcPersistenceRecord:
    """Advance arc progress within [0, 1]. Only active arcs may progress."""
    if ArcStatus(arc.status) != ArcStatus.ACTIVE:
        raise InvalidAction(f"cannot advance progress on arc status {arc.status!r}")
    if delta < 0:
        raise InvalidAction("arc progress delta must be non-negative")
    new_progress = min(Decimal("1"), max(Decimal("0"), arc.progress + delta))
    updates: dict[str, object] = {
        "progress": new_progress,
        "version": arc.version + 1,
    }
    if phase_index is not None:
        if phase_index < 0:
            raise InvalidAction("phase_index must be >= 0")
        # Preserve deadline semantics; callers pass phase for audit only via milestones.
        milestones = dict(arc.milestones)
        milestones["last_progress_phase_index"] = phase_index
        updates["milestones"] = milestones
    return arc.model_copy(update=updates)


def close_arc(
    arc: ArcPersistenceRecord,
    *,
    outcome: ArcStatus | str = ArcStatus.RESOLVED,
    end_phase_index: int,
) -> ArcPersistenceRecord:
    """Close an arc to a terminal status (resolved / failed / abandoned)."""
    if end_phase_index < 0:
        raise InvalidAction("end_phase_index must be >= 0")
    target = ArcStatus(outcome)
    if target not in ARC_TERMINAL_STATUSES:
        raise InvalidAction(f"close_arc outcome must be terminal; got {target.value!r}")
    current = ArcStatus(arc.status)
    _assert_transition(current, target)
    return arc.model_copy(
        update={
            "status": target.value,
            "end_phase_index": end_phase_index,
            "version": arc.version + 1,
        }
    )


def _assert_transition(current: ArcStatus, target: ArcStatus) -> None:
    if current == target:
        return
    allowed = _ARC_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransition(entity="arc", from_state=current.value, to_state=target.value)
