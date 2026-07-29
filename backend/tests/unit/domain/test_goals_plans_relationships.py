"""Unit tests for Stage 2 goals, plans, commitments, and relationships."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.domain.common.enums import RelationshipDimension
from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.commitments import create_commitment, update_status
from fictional_world.domain.continuity.config import NORMAL_SCENE_MAX_ABS_DELTA
from fictional_world.domain.continuity.evidence import RelationshipEvidenceInput
from fictional_world.domain.continuity.goals import (
    abandon,
    activate,
    complete,
    create_goal,
    set_priority,
)
from fictional_world.domain.continuity.plans import (
    create_primary_plan,
    demote_conflicting_primary_plans,
    invalidate_plan_for_failed_prerequisites,
    revise_plan,
    update_plan_step_status,
)
from fictional_world.domain.continuity.relationships import (
    apply_relationship_evidence,
    empty_relationship_edge,
)
from fictional_world.domain.continuity.relevance import commitments_for_reminder
from fictional_world.domain.continuity.statuses import (
    CommitmentStatus,
    GoalStatus,
    PlanStatus,
    PlanStepStatus,
)


@pytest.fixture
def world_id() -> UUID:
    return uuid4()


@pytest.fixture
def char_a() -> UUID:
    return uuid4()


@pytest.fixture
def char_b() -> UUID:
    return uuid4()


def test_goal_lifecycle_and_priority(world_id: UUID, char_a: UUID) -> None:
    goal = create_goal(
        world_id=world_id,
        owner_character_id=char_a,
        description="Secure the lantern ward storefront",
        category="livelihood",
        priority=Decimal("0.72"),
    )
    assert goal.status == GoalStatus.PROPOSED.value
    goal = activate(goal)
    assert goal.status == GoalStatus.ACTIVE.value
    goal = set_priority(goal, Decimal("0.9"))
    assert goal.priority == Decimal("0.9")
    done = complete(goal)
    assert done.status == GoalStatus.COMPLETED.value
    with pytest.raises(InvalidStateTransition):
        abandon(done)


def test_goal_rejects_out_of_range_priority(world_id: UUID, char_a: UUID) -> None:
    with pytest.raises(InvalidAction, match="priority"):
        create_goal(
            world_id=world_id,
            owner_character_id=char_a,
            description="x",
            category="y",
            priority=Decimal("1.5"),
        )


def test_one_active_primary_plan_unless_alternatives_allowed(world_id: UUID, char_a: UUID) -> None:
    goal = create_goal(
        world_id=world_id,
        owner_character_id=char_a,
        description="Find Mira",
        category="social",
        status=GoalStatus.ACTIVE,
    )
    plan1, steps1 = create_primary_plan(
        goal,
        title="Ask at the inn",
        steps=[{"description": "Walk to inn"}],
    )
    assert plan1.is_primary
    assert plan1.status == PlanStatus.ACTIVE.value
    assert len(steps1) == 1

    with pytest.raises(InvalidAction, match="active primary"):
        create_primary_plan(goal, title="Other route", existing_plans=(plan1,))

    alt_goal = goal.model_copy(update={"allows_alternative_plans": True})
    plan2, _steps = create_primary_plan(alt_goal, title="Check market", existing_plans=(plan1,))
    demoted = demote_conflicting_primary_plans(
        new_primary=plan2,
        existing_plans=(plan1,),
        allows_alternative_plans=True,
    )
    assert len(demoted) == 1
    assert demoted[0].is_primary is False
    assert demoted[0].status == PlanStatus.SUPERSEDED.value


def test_revise_plan_and_step_status(world_id: UUID, char_a: UUID) -> None:
    goal = create_goal(
        world_id=world_id,
        owner_character_id=char_a,
        description="Restock",
        category="work",
        status=GoalStatus.ACTIVE,
    )
    plan, steps = create_primary_plan(
        goal, title="Buy supplies", steps=[{"description": "Visit stall"}]
    )
    revised = revise_plan(plan, title="Buy supplies at dawn")
    assert revised.revision_number == 2
    assert revised.title == "Buy supplies at dawn"
    step = update_plan_step_status(steps[0], PlanStepStatus.ACTIVE)
    step = update_plan_step_status(step, PlanStepStatus.COMPLETED)
    assert step.status == PlanStepStatus.COMPLETED.value
    with pytest.raises(InvalidStateTransition):
        update_plan_step_status(step, PlanStepStatus.PENDING)


def test_plan_invalidation_when_location_or_resource_prerequisite_fails(
    world_id: UUID, char_a: UUID
) -> None:
    goal = create_goal(
        world_id=world_id,
        owner_character_id=char_a,
        description="Deliver crate",
        category="work",
        status=GoalStatus.ACTIVE,
    )
    required_location = uuid4()
    elsewhere = uuid4()
    plan, steps = create_primary_plan(
        goal,
        title="Deliver",
        steps=[
            {
                "description": "Hand off crate",
                "prerequisites": {
                    "location_id": str(required_location),
                    "resource": "crate_key",
                },
            }
        ],
    )
    new_plan, new_steps = invalidate_plan_for_failed_prerequisites(
        plan,
        steps,
        current_location_id=elsewhere,
        available_resource_keys=frozenset({"crate_key"}),
    )
    assert new_steps[0].status == PlanStepStatus.INVALIDATED.value
    assert new_plan.status == PlanStatus.INVALIDATED.value

    ok_plan, ok_steps = invalidate_plan_for_failed_prerequisites(
        plan,
        steps,
        current_location_id=required_location,
        available_resource_keys=frozenset({"crate_key"}),
    )
    assert ok_plan.status == PlanStatus.ACTIVE.value
    assert ok_steps[0].status == PlanStepStatus.PENDING.value

    _, missing_resource_steps = invalidate_plan_for_failed_prerequisites(
        plan,
        steps,
        current_location_id=required_location,
        available_resource_keys=frozenset(),
    )
    assert missing_resource_steps[0].status == PlanStepStatus.INVALIDATED.value


def test_commitment_status_preserves_reminder_fields(
    world_id: UUID, char_a: UUID, char_b: UUID
) -> None:
    due = {
        "due_phase_index": 42,
        "reminder_text": "Meet Torren before dusk",
        "reminder_salience": 0.8,
    }
    commitment = create_commitment(
        world_id=world_id,
        debtor_character_id=char_a,
        beneficiary_character_id=char_b,
        description="Return the borrowed ledger",
        due_condition=due,
    )
    assert commitment.status == CommitmentStatus.PROMISED.value
    active = update_status(commitment, CommitmentStatus.ACTIVE)
    assert active.due_condition == due
    assert active.description == "Return the borrowed ledger"
    fulfilled = update_status(active, CommitmentStatus.FULFILLED, fulfilled_event_id=uuid4())
    assert fulfilled.due_condition["reminder_text"] == "Meet Torren before dusk"
    assert fulfilled.status == CommitmentStatus.FULFILLED.value
    with pytest.raises(InvalidStateTransition):
        update_status(fulfilled, CommitmentStatus.ACTIVE)

    reminders = commitments_for_reminder((commitment, active), debtor_character_id=char_a)
    assert len(reminders) == 2
    assert reminders[0].due_condition["reminder_text"] == "Meet Torren before dusk"


def test_asymmetric_relationships(world_id: UUID, char_a: UUID, char_b: UUID) -> None:
    a_to_b = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    b_to_a = empty_relationship_edge(
        world_id=world_id, source_character_id=char_b, target_character_id=char_a
    )
    evidence = RelationshipEvidenceInput(
        dimension=RelationshipDimension.TRUST.value,
        signed_strength=Decimal("0.5"),
    )
    a_to_b, delta_ab = apply_relationship_evidence(a_to_b, evidence)
    assert delta_ab == NORMAL_SCENE_MAX_ABS_DELTA
    assert a_to_b.trust == NORMAL_SCENE_MAX_ABS_DELTA
    assert b_to_a.trust == Decimal("0")
    assert a_to_b.trust != b_to_a.trust


def test_repeated_positive_evidence_diminishes(world_id: UUID, char_a: UUID, char_b: UUID) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    evidence = RelationshipEvidenceInput(
        dimension=RelationshipDimension.AFFECTION.value,
        signed_strength=Decimal("0.08"),
    )
    edge, delta0 = apply_relationship_evidence(edge, evidence, prior_same_sign_count=0)
    edge, delta1 = apply_relationship_evidence(edge, evidence, prior_same_sign_count=1)
    _edge, delta2 = apply_relationship_evidence(edge, evidence, prior_same_sign_count=3)
    assert delta0 == Decimal("0.08")
    assert abs(delta1) < abs(delta0)
    assert abs(delta2) < abs(delta1)


def test_betrayal_reduces_trust_within_bounds(world_id: UUID, char_a: UUID, char_b: UUID) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    edge = edge.model_copy(update={"trust": Decimal("0.4")})
    evidence = RelationshipEvidenceInput(
        dimension=RelationshipDimension.TRUST.value,
        signed_strength=Decimal("-1.0"),
        evidence_tags=("betrayal",),
    )
    new_edge, delta = apply_relationship_evidence(edge, evidence)
    assert delta == -NORMAL_SCENE_MAX_ABS_DELTA
    assert new_edge.trust == Decimal("0.4") - NORMAL_SCENE_MAX_ABS_DELTA
    assert Decimal("-1") <= new_edge.trust <= Decimal("1")


def test_trust_cannot_jump_beyond_configured_delta(
    world_id: UUID, char_a: UUID, char_b: UUID
) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    evidence = RelationshipEvidenceInput(
        dimension=RelationshipDimension.TRUST.value,
        signed_strength=Decimal("1.0"),
    )
    new_edge, delta = apply_relationship_evidence(edge, evidence)
    assert abs(delta) <= NORMAL_SCENE_MAX_ABS_DELTA
    assert new_edge.trust == NORMAL_SCENE_MAX_ABS_DELTA


def test_kindness_does_not_increase_attraction(world_id: UUID, char_a: UUID, char_b: UUID) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    kindness = RelationshipEvidenceInput(
        dimension=RelationshipDimension.ATTRACTION.value,
        signed_strength=Decimal("0.5"),
        evidence_tags=("kindness",),
    )
    new_edge, delta = apply_relationship_evidence(edge, kindness)
    assert delta == Decimal("0")
    assert new_edge.attraction == Decimal("0")

    affection_evidence = RelationshipEvidenceInput(
        dimension=RelationshipDimension.AFFECTION.value,
        signed_strength=Decimal("0.5"),
        evidence_tags=("kindness",),
    )
    new_edge, affection_delta = apply_relationship_evidence(edge, affection_evidence)
    assert affection_delta > 0
    assert new_edge.attraction == Decimal("0")

    explicit = RelationshipEvidenceInput(
        dimension=RelationshipDimension.ATTRACTION.value,
        signed_strength=Decimal("0.5"),
        evidence_tags=("kindness", "attraction"),
    )
    _new_edge, attraction_delta = apply_relationship_evidence(edge, explicit)
    assert attraction_delta > 0


def test_unsupported_relationship_dimension_rejected(
    world_id: UUID, char_a: UUID, char_b: UUID
) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    with pytest.raises(InvalidAction, match="unsupported relationship dimension"):
        apply_relationship_evidence(
            edge,
            RelationshipEvidenceInput(
                dimension="friendship_score",
                signed_strength=Decimal("0.2"),
            ),
        )


def test_seed_edge_may_exist_without_evidence(world_id: UUID, char_a: UUID, char_b: UUID) -> None:
    edge = empty_relationship_edge(
        world_id=world_id, source_character_id=char_a, target_character_id=char_b
    )
    assert edge.trust == Decimal("0")
    assert edge.familiarity == Decimal("0")
    assert edge.version == 0
