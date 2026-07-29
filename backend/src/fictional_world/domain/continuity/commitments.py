"""Pure commitment helpers (Stage 2)."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.persistence import CommitmentPersistenceRecord
from fictional_world.domain.continuity.statuses import CommitmentStatus

_COMMITMENT_TRANSITIONS: dict[CommitmentStatus, frozenset[CommitmentStatus]] = {
    CommitmentStatus.PROMISED: frozenset(
        {
            CommitmentStatus.ACTIVE,
            CommitmentStatus.FULFILLED,
            CommitmentStatus.BROKEN,
            CommitmentStatus.WAIVED,
        }
    ),
    CommitmentStatus.ACTIVE: frozenset(
        {
            CommitmentStatus.FULFILLED,
            CommitmentStatus.BROKEN,
            CommitmentStatus.WAIVED,
        }
    ),
    CommitmentStatus.FULFILLED: frozenset(),
    CommitmentStatus.BROKEN: frozenset(),
    CommitmentStatus.WAIVED: frozenset(),
}


def create_commitment(
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
    if debtor_character_id == beneficiary_character_id:
        raise InvalidAction("commitment debtor and beneficiary must differ")
    resolved = CommitmentStatus(status)
    condition = dict(due_condition or {})
    return CommitmentPersistenceRecord(
        id=commitment_id or uuid4(),
        world_id=world_id,
        debtor_character_id=debtor_character_id,
        beneficiary_character_id=beneficiary_character_id,
        description=description,
        due_condition=condition,
        status=resolved.value,
        created_event_id=created_event_id,
        fulfilled_event_id=None,
        version=0,
    )


def update_status(
    commitment: CommitmentPersistenceRecord,
    new_status: CommitmentStatus | str,
    *,
    fulfilled_event_id: UUID | None = None,
) -> CommitmentPersistenceRecord:
    """Transition commitment status while preserving reminder/due fields."""
    current = CommitmentStatus(commitment.status)
    target = CommitmentStatus(new_status)
    allowed = _COMMITMENT_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidStateTransition(
            entity="commitment", from_state=current.value, to_state=target.value
        )
    updates: dict[str, object] = {
        "status": target.value,
        "version": commitment.version + 1,
        # Explicitly keep reminder fields (due_condition, description) unchanged.
        "due_condition": dict(commitment.due_condition),
        "description": commitment.description,
        "debtor_character_id": commitment.debtor_character_id,
        "beneficiary_character_id": commitment.beneficiary_character_id,
    }
    if target is CommitmentStatus.FULFILLED:
        updates["fulfilled_event_id"] = fulfilled_event_id or commitment.fulfilled_event_id
    return commitment.model_copy(update=updates)
