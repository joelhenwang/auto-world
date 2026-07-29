"""Read and potential-write sets for Stage 1 action proposals."""

from __future__ import annotations

from uuid import UUID

from fictional_world.domain.scenes.proposals import ActionProposal


def mutable_write_set(proposal: ActionProposal) -> frozenset[UUID]:
    """Return aggregates the proposal could mutate if accepted and resolved."""

    aggregate_ids = {proposal.actor_id, *proposal.target_entity_ids}
    if proposal.target_location_id is not None:
        aggregate_ids.add(proposal.target_location_id)
    if proposal.continuation_activity_id is not None:
        aggregate_ids.add(proposal.continuation_activity_id)
    return frozenset(aggregate_ids)


def read_set(proposal: ActionProposal) -> frozenset[UUID]:
    """Return aggregates whose state or identity informs proposal resolution."""

    aggregate_ids = set(mutable_write_set(proposal))
    aggregate_ids.update(proposal.relevant_goal_ids)
    return frozenset(aggregate_ids)


__all__ = ["mutable_write_set", "read_set"]
