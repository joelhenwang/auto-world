"""Deterministic assembly of simultaneous action proposals into scenes.

Stage 1 ``assemble_scenes`` remains the frozen grouping entry point.
Stage 2 ``assemble_multiparty_scenes`` adds focus/NPC bounds, write-set
concurrency metadata, per-participant knowledge isolation hashes, initiative
order, and beat-budget continuation decisions (handbook ``27`` S2-SIM-002).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid5

from fictional_world.application.simulation.beat_budget import SceneType, beat_budget_for
from fictional_world.application.simulation.conflict_sets import (
    may_resolve_concurrently,
    mutable_write_set,
    partition_concurrent_batches,
    scene_mutable_write_set,
    scene_read_set,
    write_sets_intersect,
)
from fictional_world.application.simulation.priority import score_initiative, score_priority
from fictional_world.domain.common.enums import ActionFamily
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    PriorityBreakdown,
    SceneDraft,
)

SCENE_ID_NAMESPACE = UUID("dbf26eb0-83d4-5d87-844c-23c47c83d64a")
MAX_FOCUS_CHARACTERS = 4
MAX_DETAILED_NPCS_PER_SCENE = 6

_SOCIAL_FAMILIES = frozenset(
    {
        ActionFamily.COMMUNICATE,
        ActionFamily.SOCIALIZE,
        ActionFamily.PERSUADE,
        ActionFamily.DECEIVE,
        ActionFamily.PERFORM,
    }
)
_NEGOTIATION_FAMILIES = frozenset({ActionFamily.PERSUADE, ActionFamily.DECEIVE})
_DANGER_FAMILIES = frozenset({ActionFamily.ATTACK, ActionFamily.DEFEND})
_NONLETHAL_FAMILIES = frozenset(
    {
        ActionFamily.ATTACK,
        ActionFamily.DEFEND,
        ActionFamily.INTERACT_ENVIRONMENT,
    }
)


class ParticipantKind(StrEnum):
    """Assembly-time participant classification (not a frozen domain enum)."""

    FOCUS = "focus"
    NPC = "npc"


@dataclass(frozen=True, slots=True)
class ParticipantAssemblyMeta:
    """Per-participant assembly metadata with knowledge-isolation scope."""

    entity_id: UUID
    kind: ParticipantKind
    knowledge_scope_hash: str | None
    reaction_eligible: bool = True


@dataclass(frozen=True, slots=True)
class BeatContinuationDecision:
    """Outcome of beat-budget expiry — never recursively loops in-phase."""

    continue_next_phase: bool
    scene_concluded: bool
    recursive_loop_allowed: Literal[False] = False


@dataclass(frozen=True, slots=True)
class AssembledScene:
    """Stage 2 scene assembly result wrapping a Stage 1 ``SceneDraft``."""

    draft: SceneDraft
    scene_type: SceneType
    focus_participant_ids: tuple[UUID, ...]
    npc_participant_ids: tuple[UUID, ...]
    participants: tuple[ParticipantAssemblyMeta, ...]
    mutable_write_set: frozenset[UUID]
    read_set: frozenset[UUID]
    initiative_order: tuple[UUID, ...]
    allows_hidden_reaction: Literal[False] = False
    continue_next_phase: bool = False


def assemble_scenes(
    phase_id: UUID,
    snapshot_id: UUID,
    proposals: Sequence[ActionProposal],
    actor_locations: Mapping[UUID, UUID | None],
) -> tuple[SceneDraft, ...]:
    """Group proposals and return stable priority-ordered scene drafts."""

    ordered = _ordered_proposals(proposals)
    _validate_unique_proposals(ordered)
    components = _proposal_components(ordered, actor_locations)
    scenes = tuple(
        _build_scene(
            phase_id=phase_id,
            snapshot_id=snapshot_id,
            proposals=component,
            actor_locations=actor_locations,
        )
        for component in components
    )
    return tuple(
        sorted(
            scenes,
            key=lambda scene: (-scene.priority.final_score, scene.participant_ids[0].int),
        )
    )


def assemble_multiparty_scenes(
    phase_id: UUID,
    snapshot_id: UUID,
    proposals: Sequence[ActionProposal],
    actor_locations: Mapping[UUID, UUID | None],
    *,
    focus_character_ids: Sequence[UUID],
    npc_character_ids: Sequence[UUID] = (),
    knowledge_scope_hashes: Mapping[UUID, str | None] | None = None,
    npc_knowledge_scope_hashes: Mapping[UUID, str | None] | None = None,
    initiative_factors: Mapping[UUID, Mapping[str, float]] | None = None,
    max_focus: int = MAX_FOCUS_CHARACTERS,
    max_detailed_npcs: int = MAX_DETAILED_NPCS_PER_SCENE,
) -> tuple[AssembledScene, ...]:
    """Assemble up to four focus characters plus bounded detailed NPCs.

    Compatible intents merge; intersecting mutable write sets force merge /
    serialization into one scene. Independent write sets remain separate scenes
    eligible for concurrent resolution. Actor-authored hidden reactions are never
    permitted (``allows_hidden_reaction`` is always ``False``).
    """

    if max_focus < 1 or max_focus > MAX_FOCUS_CHARACTERS:
        raise ValueError(f"max_focus must be between 1 and {MAX_FOCUS_CHARACTERS}")
    if max_detailed_npcs < 0 or max_detailed_npcs > MAX_DETAILED_NPCS_PER_SCENE:
        raise ValueError(f"max_detailed_npcs must be between 0 and {MAX_DETAILED_NPCS_PER_SCENE}")

    focus_ids = tuple(dict.fromkeys(focus_character_ids))
    npc_ids = tuple(dict.fromkeys(npc_character_ids))
    if len(focus_ids) > max_focus:
        raise ValueError(
            f"at most {max_focus} focus characters may participate in assembly "
            f"(got {len(focus_ids)})"
        )
    focus_set = frozenset(focus_ids)
    npc_set = frozenset(npc_ids)
    if focus_set.intersection(npc_set):
        raise ValueError("focus and NPC character id sets must be disjoint")

    ordered = _ordered_proposals(proposals)
    _validate_unique_proposals(ordered)
    for proposal in ordered:
        if proposal.actor_id not in focus_set and proposal.actor_id not in npc_set:
            raise ValueError(
                f"proposal actor {proposal.actor_id} is neither focus nor registered NPC"
            )

    hashes = dict(knowledge_scope_hashes or {})
    npc_hashes = dict(npc_knowledge_scope_hashes or {})
    # NPC hashes never fall back to a shared/omniscient package — only per-NPC maps.
    for npc_id, scope in npc_hashes.items():
        hashes[npc_id] = scope

    components = _proposal_components(ordered, actor_locations)
    assembled: list[AssembledScene] = []
    for component in components:
        scene_npc_candidates = _npc_ids_for_component(component, npc_set, actor_locations)
        if len(scene_npc_candidates) > max_detailed_npcs:
            raise ValueError(
                f"scene exceeds detailed NPC budget "
                f"({len(scene_npc_candidates)} > {max_detailed_npcs})"
            )
        draft = _build_scene(
            phase_id=phase_id,
            snapshot_id=snapshot_id,
            proposals=component,
            actor_locations=actor_locations,
            extra_participant_ids=scene_npc_candidates,
        )
        scene_type = _scene_type(
            component,
            draft.shared_entity_ids,
            npc_count=len(scene_npc_candidates),
        )
        # Recompute beat budget with Stage 2 type (NPC batch / negotiation / nonlethal).
        participant_count = len(draft.participant_ids)
        budget = beat_budget_for(scene_type, participant_count)
        if budget != draft.beat_budget:
            draft = draft.model_copy(update={"beat_budget": budget})

        focus_in_scene = tuple(pid for pid in draft.participant_ids if pid in focus_set)
        npcs_in_scene = tuple(pid for pid in draft.participant_ids if pid in npc_set)
        participants = tuple(
            ParticipantAssemblyMeta(
                entity_id=pid,
                kind=ParticipantKind.FOCUS if pid in focus_set else ParticipantKind.NPC,
                knowledge_scope_hash=_isolated_scope_hash(
                    pid,
                    kind=ParticipantKind.FOCUS if pid in focus_set else ParticipantKind.NPC,
                    hashes=hashes,
                    npc_hashes=npc_hashes,
                ),
                reaction_eligible=True,
            )
            for pid in draft.participant_ids
        )
        _assert_npc_knowledge_isolation(participants)

        initiative_order = _initiative_order(
            component,
            participant_ids=draft.participant_ids,
            factors=initiative_factors or {},
        )
        assembled.append(
            AssembledScene(
                draft=draft,
                scene_type=scene_type,
                focus_participant_ids=focus_in_scene,
                npc_participant_ids=npcs_in_scene,
                participants=participants,
                mutable_write_set=scene_mutable_write_set(component).union(npcs_in_scene),
                read_set=scene_read_set(component).union(draft.participant_ids),
                initiative_order=initiative_order,
                allows_hidden_reaction=False,
                continue_next_phase=False,
            )
        )

    ordered_scenes = tuple(
        sorted(
            assembled,
            key=lambda scene: (
                -scene.draft.priority.final_score,
                scene.draft.participant_ids[0].int,
            ),
        )
    )
    return ordered_scenes


def evaluate_beat_continuation(
    *,
    beats_used: int,
    beat_budget: int,
    unresolved: bool,
) -> BeatContinuationDecision:
    """Decide continuation when the beat budget is exhausted.

    Expired budgets never recurse within the phase; unresolved scenes continue
    next phase instead of looping (handbook ``07`` §12.3 / ``27`` S2-SIM-002).
    """

    if beats_used < 0:
        raise ValueError("beats_used cannot be negative")
    if not 1 <= beat_budget <= 12:
        raise ValueError("beat_budget must be between 1 and 12")
    if beats_used < beat_budget:
        return BeatContinuationDecision(
            continue_next_phase=False,
            scene_concluded=False,
            recursive_loop_allowed=False,
        )
    if unresolved:
        return BeatContinuationDecision(
            continue_next_phase=True,
            scene_concluded=False,
            recursive_loop_allowed=False,
        )
    return BeatContinuationDecision(
        continue_next_phase=False,
        scene_concluded=True,
        recursive_loop_allowed=False,
    )


def mark_continuation(scene: AssembledScene, *, unresolved: bool) -> AssembledScene:
    """Return a copy with ``continue_next_phase`` set from budget expiry rules."""

    decision = evaluate_beat_continuation(
        beats_used=scene.draft.beat_budget,
        beat_budget=scene.draft.beat_budget,
        unresolved=unresolved,
    )
    return AssembledScene(
        draft=scene.draft,
        scene_type=scene.scene_type,
        focus_participant_ids=scene.focus_participant_ids,
        npc_participant_ids=scene.npc_participant_ids,
        participants=scene.participants,
        mutable_write_set=scene.mutable_write_set,
        read_set=scene.read_set,
        initiative_order=scene.initiative_order,
        allows_hidden_reaction=False,
        continue_next_phase=decision.continue_next_phase,
    )


def concurrent_scene_batches(
    scenes: Sequence[AssembledScene],
) -> tuple[tuple[AssembledScene, ...], ...]:
    """Group assembled scenes into write-set-safe concurrent batches."""

    write_sets = tuple(scene.mutable_write_set for scene in scenes)
    batches = partition_concurrent_batches(write_sets)
    return tuple(tuple(scenes[index] for index in batch) for batch in batches)


def scenes_are_independent(left: AssembledScene, right: AssembledScene) -> bool:
    """True when two assembled scenes may resolve concurrently."""

    return may_resolve_concurrently(left.mutable_write_set, right.mutable_write_set)


def _ordered_proposals(proposals: Sequence[ActionProposal]) -> tuple[ActionProposal, ...]:
    return tuple(
        sorted(
            proposals,
            key=lambda proposal: (proposal.actor_id.int, proposal.decision_request_id.int),
        )
    )


def _validate_unique_proposals(proposals: tuple[ActionProposal, ...]) -> None:
    actor_ids = [proposal.actor_id for proposal in proposals]
    if len(actor_ids) != len(set(actor_ids)):
        raise ValueError("each actor must have exactly one primary proposal")
    request_ids = [proposal.decision_request_id for proposal in proposals]
    if len(request_ids) != len(set(request_ids)):
        raise ValueError("decision_request_id values must be unique")


def _proposal_components(
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
) -> tuple[tuple[ActionProposal, ...], ...]:
    parents = list(range(len(proposals)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for left_index, left in enumerate(proposals):
        for right_index in range(left_index + 1, len(proposals)):
            right = proposals[right_index]
            if _should_group(left, right, actor_locations):
                union(left_index, right_index)

    grouped: dict[int, list[ActionProposal]] = {}
    for index, proposal in enumerate(proposals):
        grouped.setdefault(root(index), []).append(proposal)
    return tuple(
        tuple(component)
        for component in sorted(
            grouped.values(),
            key=lambda component: component[0].actor_id.int,
        )
    )


def _should_group(
    left: ActionProposal,
    right: ActionProposal,
    actor_locations: Mapping[UUID, UUID | None],
) -> bool:
    shared_targets = set(left.target_entity_ids).intersection(right.target_entity_ids)
    targets_other_actor = (
        right.actor_id in left.target_entity_ids or left.actor_id in right.target_entity_ids
    )
    if shared_targets or targets_other_actor:
        return True

    if left.target_location_id is not None and left.target_location_id == right.target_location_id:
        return True

    # Same-resource / activity conflicts: intersecting mutable write sets merge.
    if write_sets_intersect(mutable_write_set(left), mutable_write_set(right)):
        # Actor self-ids always differ; only merge when a *shared* aggregate exists
        # beyond the two distinct actors themselves.
        shared_writes = mutable_write_set(left).intersection(mutable_write_set(right))
        non_actor_shared = shared_writes - {left.actor_id, right.actor_id}
        if non_actor_shared:
            return True

    left_location = actor_locations.get(left.actor_id)
    right_location = actor_locations.get(right.actor_id)
    return (
        left_location is not None
        and left_location == right_location
        and (left.action_family in _SOCIAL_FAMILIES or right.action_family in _SOCIAL_FAMILIES)
    )


def _build_scene(
    *,
    phase_id: UUID,
    snapshot_id: UUID,
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
    extra_participant_ids: Sequence[UUID] = (),
) -> SceneDraft:
    participant_ids = tuple(
        sorted(
            {proposal.actor_id for proposal in proposals}.union(extra_participant_ids),
            key=lambda x: x.int,
        )
    )
    proposal_ids = tuple(
        sorted((proposal.decision_request_id for proposal in proposals), key=lambda x: x.int)
    )
    shared_entity_ids = _shared_entity_ids(proposals)
    scene_type = _scene_type(proposals, shared_entity_ids)
    priority = _scene_priority(proposals)
    scene_id = uuid5(
        SCENE_ID_NAMESPACE,
        f"{phase_id}:{snapshot_id}:{','.join(str(proposal_id) for proposal_id in proposal_ids)}",
    )
    return SceneDraft(
        scene_id=scene_id,
        phase_id=phase_id,
        snapshot_id=snapshot_id,
        location_id=_scene_location(proposals, actor_locations),
        participant_ids=participant_ids,
        action_proposal_ids=proposal_ids,
        shared_entity_ids=shared_entity_ids,
        priority=priority,
        beat_budget=beat_budget_for(scene_type, len(participant_ids)),
        high_impact=any(proposal.action_family in _DANGER_FAMILIES for proposal in proposals),
    )


def _shared_entity_ids(proposals: tuple[ActionProposal, ...]) -> tuple[UUID, ...]:
    references: Counter[UUID] = Counter()
    for proposal in proposals:
        references.update({proposal.actor_id, *proposal.target_entity_ids})
    return tuple(
        sorted(
            (entity_id for entity_id, count in references.items() if count > 1),
            key=lambda entity_id: entity_id.int,
        )
    )


def _scene_location(
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
) -> UUID | None:
    target_locations = {
        proposal.target_location_id
        for proposal in proposals
        if proposal.target_location_id is not None
    }
    if len(target_locations) == 1:
        return next(iter(target_locations))
    if target_locations:
        return None

    current_locations = {
        location
        for proposal in proposals
        if (location := actor_locations.get(proposal.actor_id)) is not None
    }
    return next(iter(current_locations)) if len(current_locations) == 1 else None


def _scene_type(
    proposals: tuple[ActionProposal, ...],
    shared_entity_ids: tuple[UUID, ...],
    *,
    npc_count: int = 0,
) -> SceneType:
    if not proposals and npc_count > 0:
        return SceneType.NPC_BATCH
    if len(proposals) == 1 and npc_count == 0:
        return SceneType.SOLO_ACTION
    if any(proposal.action_family in _NEGOTIATION_FAMILIES for proposal in proposals):
        return SceneType.NEGOTIATION
    if any(proposal.action_family in _DANGER_FAMILIES for proposal in proposals):
        # Lethal combat is out of Stage 2 SIM-002 scope; treat as nonlethal.
        return SceneType.NONLETHAL_CONFLICT
    if any(proposal.action_family in _SOCIAL_FAMILIES for proposal in proposals):
        if len(proposals) + npc_count == 2:
            return SceneType.DIALOGUE
        return SceneType.SOCIAL_INTERACTION
    if shared_entity_ids:
        return SceneType.RESOURCE_CONFLICT
    if all(proposal.action_family is ActionFamily.MOVE for proposal in proposals):
        return SceneType.TRAVEL
    if npc_count > 0 and all(
        proposal.action_family
        in {ActionFamily.WAIT, ActionFamily.OBSERVE, ActionFamily.CONTINUE_ACTIVITY}
        for proposal in proposals
    ):
        return SceneType.NPC_BATCH
    return SceneType.WORLD_EVENT_RESPONSE


def _scene_priority(proposals: tuple[ActionProposal, ...]) -> PriorityBreakdown:
    return score_priority(
        causal_urgency=float(any(not proposal.interruptible for proposal in proposals)),
        immediate_danger=float(
            any(proposal.action_family in _DANGER_FAMILIES for proposal in proposals)
        ),
        scheduled_commitment=float(
            any(proposal.continuation_activity_id is not None for proposal in proposals)
        ),
        unresolved_dependency=float(
            any(
                proposal.target_entity_ids or proposal.target_location_id is not None
                for proposal in proposals
            )
        ),
        goal_relevance=float(any(proposal.relevant_goal_ids for proposal in proposals)),
        starvation_fairness=0.0,
    )


def _npc_ids_for_component(
    proposals: tuple[ActionProposal, ...],
    npc_set: frozenset[UUID],
    actor_locations: Mapping[UUID, UUID | None],
) -> tuple[UUID, ...]:
    """NPCs that belong in this component: proposers or co-located / targeted."""

    in_scene: set[UUID] = {p.actor_id for p in proposals if p.actor_id in npc_set}
    for proposal in proposals:
        for target in proposal.target_entity_ids:
            if target in npc_set:
                in_scene.add(target)

    scene_location = _scene_location(proposals, actor_locations)
    interactive = any(
        p.action_family in _SOCIAL_FAMILIES.union(_NONLETHAL_FAMILIES) or p.target_entity_ids
        for p in proposals
    )
    if scene_location is not None and interactive:
        for npc_id in npc_set:
            if actor_locations.get(npc_id) == scene_location:
                in_scene.add(npc_id)
    return tuple(sorted(in_scene, key=lambda x: x.int))


def _isolated_scope_hash(
    entity_id: UUID,
    *,
    kind: ParticipantKind,
    hashes: Mapping[UUID, str | None],
    npc_hashes: Mapping[UUID, str | None],
) -> str | None:
    if kind is ParticipantKind.NPC:
        # Prefer the dedicated NPC map so a shared focus hash cannot leak in.
        if entity_id in npc_hashes:
            return npc_hashes[entity_id]
        return hashes.get(entity_id)
    return hashes.get(entity_id)


def _assert_npc_knowledge_isolation(
    participants: Sequence[ParticipantAssemblyMeta],
) -> None:
    """NPC knowledge scopes must be per-NPC; no shared omniscient package hash."""

    npc_hashes = [
        meta.knowledge_scope_hash
        for meta in participants
        if meta.kind is ParticipantKind.NPC and meta.knowledge_scope_hash is not None
    ]
    if len(npc_hashes) != len(set(npc_hashes)):
        raise ValueError(
            "NPC participants must not share a knowledge_scope_hash "
            "(per-NPC knowledge isolation required)"
        )


def _initiative_order(
    proposals: tuple[ActionProposal, ...],
    *,
    participant_ids: Sequence[UUID],
    factors: Mapping[UUID, Mapping[str, float]],
) -> tuple[UUID, ...]:
    """Deterministic initiative: social initiator first, then scored order."""

    initiator: UUID | None = None
    if any(p.action_family in _SOCIAL_FAMILIES for p in proposals):
        social = [p for p in proposals if p.action_family in _SOCIAL_FAMILIES]
        initiator = min(social, key=lambda p: p.actor_id.int).actor_id

    def sort_key(entity_id: UUID) -> tuple[int, float, int]:
        raw = factors.get(entity_id, {})
        score = score_initiative(
            preparation=float(raw.get("preparation", 0.0)),
            surprise=float(raw.get("surprise", 0.0)),
            dexterity=float(raw.get("dexterity", 0.0)),
            perception=float(raw.get("perception", 0.0)),
            relevant_skill=float(raw.get("relevant_skill", 0.0)),
            current_stamina=float(raw.get("current_stamina", 0.0)),
            terrain_advantage=float(raw.get("terrain_advantage", 0.0)),
            seeded_randomness=float(raw.get("seeded_randomness", 0.0)),
            injury_penalty=float(raw.get("injury_penalty", 0.0)),
        )
        opener = 0 if initiator is not None and entity_id == initiator else 1
        return (opener, -score, entity_id.int)

    return tuple(sorted(participant_ids, key=sort_key))


__all__ = [
    "MAX_DETAILED_NPCS_PER_SCENE",
    "MAX_FOCUS_CHARACTERS",
    "SCENE_ID_NAMESPACE",
    "AssembledScene",
    "BeatContinuationDecision",
    "ParticipantAssemblyMeta",
    "ParticipantKind",
    "assemble_multiparty_scenes",
    "assemble_scenes",
    "concurrent_scene_batches",
    "evaluate_beat_continuation",
    "mark_continuation",
    "scenes_are_independent",
]
