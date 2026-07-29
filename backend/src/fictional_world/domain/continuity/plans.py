"""Pure plan and plan-step helpers (Stage 2)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.persistence import (
    GoalPersistenceRecord,
    PlanPersistenceRecord,
    PlanStepPersistenceRecord,
)
from fictional_world.domain.continuity.statuses import (
    GoalStatus,
    PlanStatus,
    PlanStepStatus,
)

_PLAN_STEP_TRANSITIONS: dict[PlanStepStatus, frozenset[PlanStepStatus]] = {
    PlanStepStatus.PENDING: frozenset(
        {
            PlanStepStatus.ACTIVE,
            PlanStepStatus.COMPLETED,
            PlanStepStatus.BLOCKED,
            PlanStepStatus.FAILED,
            PlanStepStatus.SKIPPED,
            PlanStepStatus.INVALIDATED,
        }
    ),
    PlanStepStatus.ACTIVE: frozenset(
        {
            PlanStepStatus.COMPLETED,
            PlanStepStatus.BLOCKED,
            PlanStepStatus.FAILED,
            PlanStepStatus.SKIPPED,
            PlanStepStatus.INVALIDATED,
        }
    ),
    PlanStepStatus.BLOCKED: frozenset(
        {
            PlanStepStatus.PENDING,
            PlanStepStatus.ACTIVE,
            PlanStepStatus.FAILED,
            PlanStepStatus.SKIPPED,
            PlanStepStatus.INVALIDATED,
        }
    ),
    PlanStepStatus.COMPLETED: frozenset(),
    PlanStepStatus.FAILED: frozenset({PlanStepStatus.PENDING, PlanStepStatus.INVALIDATED}),
    PlanStepStatus.SKIPPED: frozenset(),
    PlanStepStatus.INVALIDATED: frozenset(),
}


def create_primary_plan(
    goal: GoalPersistenceRecord,
    *,
    title: str,
    existing_plans: Sequence[PlanPersistenceRecord] = (),
    steps: Sequence[dict[str, Any]] = (),
    expected_horizon: str | None = None,
    commitment_level: Decimal = Decimal("0.5"),
    source_event_id: UUID | None = None,
    plan_id: UUID | None = None,
) -> tuple[PlanPersistenceRecord, tuple[PlanStepPersistenceRecord, ...]]:
    """Create an active primary plan for a goal.

    Enforces at most one active primary plan unless ``allows_alternative_plans``.
    When alternatives are allowed, callers must also persist demotions from
    ``demote_conflicting_primary_plans``.
    """
    if GoalStatus(goal.status) not in {GoalStatus.ACTIVE, GoalStatus.PROPOSED, GoalStatus.BLOCKED}:
        raise InvalidAction(f"cannot create plan for goal in status {goal.status!r}")

    active_primaries = [
        p for p in existing_plans if p.is_primary and PlanStatus(p.status) == PlanStatus.ACTIVE
    ]
    if active_primaries and not goal.allows_alternative_plans:
        raise InvalidAction(
            "goal already has an active primary plan; set allows_alternative_plans to add another"
        )

    resolved_id = plan_id or uuid4()
    plan = PlanPersistenceRecord(
        id=resolved_id,
        goal_id=goal.id,
        world_id=goal.world_id,
        owner_character_id=goal.owner_character_id,
        title=title,
        status=PlanStatus.ACTIVE.value,
        is_primary=True,
        expected_horizon=expected_horizon,
        commitment_level=commitment_level,
        revision_number=1,
        source_event_id=source_event_id,
        version=0,
    )
    step_records = tuple(
        _step_from_spec(plan_id=resolved_id, index=index, spec=spec)
        for index, spec in enumerate(steps)
    )
    return plan, step_records


def demote_conflicting_primary_plans(
    *,
    new_primary: PlanPersistenceRecord,
    existing_plans: Sequence[PlanPersistenceRecord],
    allows_alternative_plans: bool,
) -> tuple[PlanPersistenceRecord, ...]:
    """Return updated copies of plans that must yield primary status."""
    if not allows_alternative_plans:
        return ()
    demoted: list[PlanPersistenceRecord] = []
    for plan in existing_plans:
        if plan.id == new_primary.id:
            continue
        if plan.is_primary and PlanStatus(plan.status) == PlanStatus.ACTIVE:
            demoted.append(
                plan.model_copy(
                    update={
                        "is_primary": False,
                        "status": PlanStatus.SUPERSEDED.value,
                        "version": plan.version + 1,
                    }
                )
            )
    return tuple(demoted)


def revise_plan(
    plan: PlanPersistenceRecord,
    *,
    title: str | None = None,
    expected_horizon: str | None = None,
    commitment_level: Decimal | None = None,
    source_event_id: UUID | None = None,
) -> PlanPersistenceRecord:
    """Bump revision after a relevant event; keeps plan active when revising."""
    if PlanStatus(plan.status) in {
        PlanStatus.COMPLETED,
        PlanStatus.ABANDONED,
        PlanStatus.INVALIDATED,
    }:
        raise InvalidAction(f"cannot revise plan in status {plan.status!r}")
    updates: dict[str, object] = {
        "revision_number": plan.revision_number + 1,
        "version": plan.version + 1,
        "status": PlanStatus.ACTIVE.value,
    }
    if title is not None:
        updates["title"] = title
    if expected_horizon is not None:
        updates["expected_horizon"] = expected_horizon
    if commitment_level is not None:
        updates["commitment_level"] = commitment_level
    if source_event_id is not None:
        updates["source_event_id"] = source_event_id
    return plan.model_copy(update=updates)


def update_plan_step_status(
    step: PlanStepPersistenceRecord,
    new_status: PlanStepStatus | str,
) -> PlanStepPersistenceRecord:
    current = PlanStepStatus(step.status)
    target = PlanStepStatus(new_status)
    allowed = _PLAN_STEP_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransition(
            entity="plan_step", from_state=current.value, to_state=target.value
        )
    return step.model_copy(update={"status": target.value, "version": step.version + 1})


def invalidate_plan_for_failed_prerequisites(
    plan: PlanPersistenceRecord,
    steps: Sequence[PlanStepPersistenceRecord],
    *,
    current_location_id: UUID | None = None,
    available_resource_keys: frozenset[str] | set[str] | None = None,
) -> tuple[PlanPersistenceRecord, tuple[PlanStepPersistenceRecord, ...]]:
    """Invalidate active/pending steps whose location/resource prerequisites fail."""
    resources = frozenset(available_resource_keys or ())
    updated_steps: list[PlanStepPersistenceRecord] = []
    any_invalidated = False
    for step in steps:
        status = PlanStepStatus(step.status)
        if status in {
            PlanStepStatus.COMPLETED,
            PlanStepStatus.SKIPPED,
            PlanStepStatus.INVALIDATED,
        }:
            updated_steps.append(step)
            continue
        if _prerequisites_failed(
            step.prerequisites,
            current_location_id=current_location_id,
            available_resource_keys=resources,
        ):
            updated_steps.append(
                step.model_copy(
                    update={
                        "status": PlanStepStatus.INVALIDATED.value,
                        "version": step.version + 1,
                    }
                )
            )
            any_invalidated = True
        else:
            updated_steps.append(step)

    if not any_invalidated:
        return plan, tuple(updated_steps)

    new_plan = plan
    if PlanStatus(plan.status) == PlanStatus.ACTIVE:
        new_plan = plan.model_copy(
            update={"status": PlanStatus.INVALIDATED.value, "version": plan.version + 1}
        )
    return new_plan, tuple(updated_steps)


def _prerequisites_failed(
    prerequisites: dict[str, Any],
    *,
    current_location_id: UUID | None,
    available_resource_keys: frozenset[str],
) -> bool:
    if not prerequisites:
        return False

    required_location = prerequisites.get("location_id") or prerequisites.get(
        "required_location_id"
    )
    if required_location is not None:
        required_uuid = (
            required_location
            if isinstance(required_location, UUID)
            else UUID(str(required_location))
        )
        if current_location_id is None or current_location_id != required_uuid:
            return True

    required_resources = prerequisites.get("resources") or prerequisites.get("required_resources")
    if required_resources is not None:
        needed = {str(item) for item in required_resources}
        if not needed.issubset(available_resource_keys):
            return True

    resource_key = prerequisites.get("resource") or prerequisites.get("required_resource")
    return bool(resource_key is not None and str(resource_key) not in available_resource_keys)


def _step_from_spec(
    *, plan_id: UUID, index: int, spec: dict[str, Any]
) -> PlanStepPersistenceRecord:
    description = str(spec.get("description", "")).strip()
    if not description:
        raise InvalidAction("plan step description is required")
    raw_id = spec.get("id")
    step_id: UUID = raw_id if isinstance(raw_id, UUID) else uuid4()
    return PlanStepPersistenceRecord(
        id=step_id,
        plan_id=plan_id,
        step_index=int(spec.get("step_index", index)),
        description=description,
        status=str(spec.get("status", PlanStepStatus.PENDING.value)),
        target_entity_id=spec.get("target_entity_id"),
        target_location_id=spec.get("target_location_id"),
        activity_id=spec.get("activity_id"),
        prerequisites=dict(spec.get("prerequisites") or {}),
        expected_duration_phases=spec.get("expected_duration_phases"),
        version=0,
    )
