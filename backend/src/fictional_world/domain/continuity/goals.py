"""Pure goal lifecycle helpers (Stage 2; no personality mutation)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.config import GOAL_PRIORITY_MAX, GOAL_PRIORITY_MIN
from fictional_world.domain.continuity.persistence import GoalPersistenceRecord
from fictional_world.domain.continuity.statuses import GoalStatus

_GOAL_TRANSITIONS: dict[GoalStatus, frozenset[GoalStatus]] = {
    GoalStatus.PROPOSED: frozenset({GoalStatus.ACTIVE, GoalStatus.ABANDONED}),
    GoalStatus.ACTIVE: frozenset({GoalStatus.COMPLETED, GoalStatus.ABANDONED, GoalStatus.BLOCKED}),
    GoalStatus.BLOCKED: frozenset({GoalStatus.ACTIVE, GoalStatus.COMPLETED, GoalStatus.ABANDONED}),
    GoalStatus.COMPLETED: frozenset(),
    GoalStatus.ABANDONED: frozenset(),
}


def create_goal(
    *,
    world_id: UUID,
    owner_character_id: UUID,
    description: str,
    category: str,
    priority: Decimal = Decimal("0.5"),
    status: GoalStatus | str = GoalStatus.PROPOSED,
    horizon: str | None = None,
    success_conditions: dict[str, object] | None = None,
    failure_conditions: dict[str, object] | None = None,
    allows_alternative_plans: bool = False,
    source_event_id: UUID | None = None,
    goal_id: UUID | None = None,
) -> GoalPersistenceRecord:
    """Create a goal record. Does not mutate personality or values."""
    _validate_priority(priority)
    resolved = GoalStatus(status)
    return GoalPersistenceRecord(
        id=goal_id or uuid4(),
        world_id=world_id,
        owner_character_id=owner_character_id,
        description=description,
        category=category,
        priority=priority,
        status=resolved.value,
        horizon=horizon,
        success_conditions=dict(success_conditions or {}),
        failure_conditions=dict(failure_conditions or {}),
        allows_alternative_plans=allows_alternative_plans,
        source_event_id=source_event_id,
        version=0,
    )


def set_priority(goal: GoalPersistenceRecord, priority: Decimal) -> GoalPersistenceRecord:
    _validate_priority(priority)
    if _is_terminal(goal.status):
        raise InvalidAction(f"cannot set priority on terminal goal status {goal.status!r}")
    return goal.model_copy(update={"priority": priority, "version": goal.version + 1})


def activate(goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
    return _transition(goal, GoalStatus.ACTIVE)


def complete(goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
    return _transition(goal, GoalStatus.COMPLETED)


def abandon(goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
    return _transition(goal, GoalStatus.ABANDONED)


def block(goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
    return _transition(goal, GoalStatus.BLOCKED)


def _transition(goal: GoalPersistenceRecord, target: GoalStatus) -> GoalPersistenceRecord:
    current = GoalStatus(goal.status)
    allowed = _GOAL_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransition(entity="goal", from_state=current.value, to_state=target.value)
    return goal.model_copy(update={"status": target.value, "version": goal.version + 1})


def _validate_priority(priority: Decimal) -> None:
    if priority < GOAL_PRIORITY_MIN or priority > GOAL_PRIORITY_MAX:
        raise InvalidAction(
            f"goal priority must be in [{GOAL_PRIORITY_MIN}, {GOAL_PRIORITY_MAX}], got {priority}"
        )


def _is_terminal(status: str) -> bool:
    return GoalStatus(status) in {GoalStatus.COMPLETED, GoalStatus.ABANDONED}
