"""Relevance helpers for goal/commitment context assembly (Stage 2)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from fictional_world.domain.continuity.config import MAX_ACTIVE_GOALS_IN_CONTEXT
from fictional_world.domain.continuity.persistence import (
    CommitmentPersistenceRecord,
    GoalPersistenceRecord,
)
from fictional_world.domain.continuity.statuses import CommitmentStatus, GoalStatus


def rank_goals_for_context(
    goals: Sequence[GoalPersistenceRecord],
    *,
    limit: int = MAX_ACTIVE_GOALS_IN_CONTEXT,
) -> tuple[GoalPersistenceRecord, ...]:
    """Return up to ``limit`` highest-priority active goals."""
    active = [g for g in goals if GoalStatus(g.status) == GoalStatus.ACTIVE]
    ordered = sorted(active, key=lambda g: Decimal(g.priority), reverse=True)
    return tuple(ordered[: max(0, limit)])


def commitments_for_reminder(
    commitments: Sequence[CommitmentPersistenceRecord],
    *,
    debtor_character_id: UUID | None = None,
    counterpart_ids: frozenset[UUID] | set[UUID] | None = None,
    include_statuses: frozenset[str] | set[str] | None = None,
) -> tuple[CommitmentPersistenceRecord, ...]:
    """Select open commitments preserving due_condition reminder payloads."""
    open_statuses = include_statuses or {
        CommitmentStatus.PROMISED.value,
        CommitmentStatus.ACTIVE.value,
    }
    counterparts = frozenset(counterpart_ids or ())
    selected: list[CommitmentPersistenceRecord] = []
    for commitment in commitments:
        if commitment.status not in open_statuses:
            continue
        if (
            debtor_character_id is not None
            and commitment.debtor_character_id != debtor_character_id
        ):
            continue
        if counterparts and (
            commitment.beneficiary_character_id not in counterparts
            and commitment.debtor_character_id not in counterparts
        ):
            continue
        selected.append(commitment)
    return tuple(selected)


def goal_relevance_score(
    goal: GoalPersistenceRecord,
    *,
    related_entity_ids: frozenset[UUID] | set[UUID] | None = None,
) -> Decimal:
    """Heuristic relevance in [0, 1] for priority scoring / context trim."""
    if GoalStatus(goal.status) != GoalStatus.ACTIVE:
        return Decimal("0")
    base = Decimal(goal.priority)
    related = frozenset(related_entity_ids or ())
    if not related:
        return min(Decimal("1"), max(Decimal("0"), base))
    bump = Decimal("0")
    for value in goal.success_conditions.values():
        if str(value) in {str(entity_id) for entity_id in related}:
            bump = Decimal("0.1")
            break
    return min(Decimal("1"), max(Decimal("0"), base + bump))
