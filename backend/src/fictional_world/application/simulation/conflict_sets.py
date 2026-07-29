"""Read and potential-write sets for action proposals and assembled scenes."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
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


def scene_mutable_write_set(proposals: Sequence[ActionProposal]) -> frozenset[UUID]:
    """Union of mutable write sets across simultaneous proposals in one scene."""

    aggregates: set[UUID] = set()
    for proposal in proposals:
        aggregates.update(mutable_write_set(proposal))
    return frozenset(aggregates)


def scene_read_set(proposals: Sequence[ActionProposal]) -> frozenset[UUID]:
    """Union of read sets across simultaneous proposals in one scene."""

    aggregates: set[UUID] = set()
    for proposal in proposals:
        aggregates.update(read_set(proposal))
    return frozenset(aggregates)


def write_sets_intersect(left: Iterable[UUID], right: Iterable[UUID]) -> bool:
    """True when two mutable write sets share at least one aggregate."""

    return not frozenset(left).isdisjoint(frozenset(right))


def may_resolve_concurrently(
    left_writes: Iterable[UUID],
    right_writes: Iterable[UUID],
) -> bool:
    """Independent scenes may run concurrently when write sets do not intersect.

    Read-only overlap does not block parallel resolution (handbook ``07`` §10.3).
    """

    return not write_sets_intersect(left_writes, right_writes)


def partition_concurrent_batches(
    scene_write_sets: Sequence[frozenset[UUID]],
) -> tuple[tuple[int, ...], ...]:
    """Partition scene indices into concurrent-safe batches (greedy by index order).

    Scenes in the same batch have pairwise non-intersecting write sets and may
    resolve in parallel. Conflicting scenes are serialized across successive batches.
    """

    batches: list[list[int]] = []
    batch_writes: list[set[UUID]] = []
    for index, writes in enumerate(scene_write_sets):
        placed = False
        for batch_index, occupied in enumerate(batch_writes):
            if occupied.isdisjoint(writes):
                batches[batch_index].append(index)
                occupied.update(writes)
                placed = True
                break
        if not placed:
            batches.append([index])
            batch_writes.append(set(writes))
    return tuple(tuple(batch) for batch in batches)


__all__ = [
    "may_resolve_concurrently",
    "mutable_write_set",
    "partition_concurrent_batches",
    "read_set",
    "scene_mutable_write_set",
    "scene_read_set",
    "write_sets_intersect",
]
