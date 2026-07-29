"""Thin application adapters over continuity domain transforms.

These adapters keep DB I/O at the repository boundary: load → pure transform →
return records for the caller/UoW to persist.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from fictional_world.domain.continuity import (
    CommitmentPersistenceRecord,
    GoalPersistenceRecord,
    PlanPersistenceRecord,
    PlanStepPersistenceRecord,
    RelationshipEdgePersistenceRecord,
    RelationshipEvidenceInput,
)
from fictional_world.domain.continuity import commitments as commitment_domain
from fictional_world.domain.continuity import goals as goal_domain
from fictional_world.domain.continuity import plans as plan_domain
from fictional_world.domain.continuity import relationships as relationship_domain
from fictional_world.domain.continuity.statuses import CommitmentStatus, GoalStatus, PlanStepStatus


class GoalService:
    """Pure goal transforms; persistence is the caller's responsibility."""

    def create(
        self,
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
        return goal_domain.create_goal(
            world_id=world_id,
            owner_character_id=owner_character_id,
            description=description,
            category=category,
            priority=priority,
            status=status,
            horizon=horizon,
            success_conditions=success_conditions,
            failure_conditions=failure_conditions,
            allows_alternative_plans=allows_alternative_plans,
            source_event_id=source_event_id,
            goal_id=goal_id,
        )

    def set_priority(self, goal: GoalPersistenceRecord, priority: Decimal) -> GoalPersistenceRecord:
        return goal_domain.set_priority(goal, priority)

    def activate(self, goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
        return goal_domain.activate(goal)

    def complete(self, goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
        return goal_domain.complete(goal)

    def abandon(self, goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
        return goal_domain.abandon(goal)


class PlanService:
    def create_primary(
        self,
        goal: GoalPersistenceRecord,
        *,
        title: str,
        existing_plans: Sequence[PlanPersistenceRecord] = (),
        steps: Sequence[dict[str, Any]] = (),
        expected_horizon: str | None = None,
        commitment_level: Decimal = Decimal("0.5"),
        source_event_id: UUID | None = None,
        plan_id: UUID | None = None,
    ) -> tuple[
        PlanPersistenceRecord,
        tuple[PlanStepPersistenceRecord, ...],
        tuple[PlanPersistenceRecord, ...],
    ]:
        plan, step_records = plan_domain.create_primary_plan(
            goal,
            title=title,
            existing_plans=existing_plans,
            steps=steps,
            expected_horizon=expected_horizon,
            commitment_level=commitment_level,
            source_event_id=source_event_id,
            plan_id=plan_id,
        )
        demoted = plan_domain.demote_conflicting_primary_plans(
            new_primary=plan,
            existing_plans=existing_plans,
            allows_alternative_plans=goal.allows_alternative_plans,
        )
        return plan, step_records, demoted

    def revise(
        self,
        plan: PlanPersistenceRecord,
        *,
        title: str | None = None,
        expected_horizon: str | None = None,
        commitment_level: Decimal | None = None,
        source_event_id: UUID | None = None,
    ) -> PlanPersistenceRecord:
        return plan_domain.revise_plan(
            plan,
            title=title,
            expected_horizon=expected_horizon,
            commitment_level=commitment_level,
            source_event_id=source_event_id,
        )

    def update_step_status(
        self, step: PlanStepPersistenceRecord, new_status: PlanStepStatus | str
    ) -> PlanStepPersistenceRecord:
        return plan_domain.update_plan_step_status(step, new_status)

    def invalidate_for_prerequisites(
        self,
        plan: PlanPersistenceRecord,
        steps: Sequence[PlanStepPersistenceRecord],
        *,
        current_location_id: UUID | None = None,
        available_resource_keys: frozenset[str] | set[str] | None = None,
    ) -> tuple[PlanPersistenceRecord, tuple[PlanStepPersistenceRecord, ...]]:
        return plan_domain.invalidate_plan_for_failed_prerequisites(
            plan,
            steps,
            current_location_id=current_location_id,
            available_resource_keys=available_resource_keys,
        )


class CommitmentService:
    def create(
        self,
        *,
        world_id: UUID,
        debtor_character_id: UUID,
        beneficiary_character_id: UUID,
        description: str,
        due_condition: dict[str, Any] | None = None,
        status: CommitmentStatus | str = CommitmentStatus.PROMISED,
        created_event_id: UUID | None = None,
        commitment_id: UUID | None = None,
    ) -> CommitmentPersistenceRecord:
        return commitment_domain.create_commitment(
            world_id=world_id,
            debtor_character_id=debtor_character_id,
            beneficiary_character_id=beneficiary_character_id,
            description=description,
            due_condition=due_condition,
            status=status,
            created_event_id=created_event_id,
            commitment_id=commitment_id,
        )

    def update_status(
        self,
        commitment: CommitmentPersistenceRecord,
        new_status: CommitmentStatus | str,
        *,
        fulfilled_event_id: UUID | None = None,
    ) -> CommitmentPersistenceRecord:
        return commitment_domain.update_status(
            commitment, new_status, fulfilled_event_id=fulfilled_event_id
        )


class RelationshipService:
    def apply_evidence(
        self,
        edge: RelationshipEdgePersistenceRecord,
        evidence: RelationshipEvidenceInput,
        *,
        prior_same_sign_count: int = 0,
        max_abs_delta: Decimal | None = None,
    ) -> tuple[RelationshipEdgePersistenceRecord, Decimal]:
        return relationship_domain.apply_relationship_evidence(
            edge,
            evidence,
            prior_same_sign_count=prior_same_sign_count,
            max_abs_delta=max_abs_delta,
        )
