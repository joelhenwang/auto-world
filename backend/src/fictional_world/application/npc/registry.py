"""NPC registry: propose→dedup→register, TTL, archive, actor scheduling gates."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.application.director.types import ProposedNpcStub
from fictional_world.application.npc.budgets import check_new_npc_budgets
from fictional_world.application.npc.cards import build_compact_card, compact_card_as_json
from fictional_world.application.npc.config import NpcBudgetConfig, NpcTtlConfig
from fictional_world.application.npc.fingerprint import compute_similarity_fingerprint
from fictional_world.application.npc.types import (
    BudgetSnapshot,
    NpcProposalInput,
    NpcRegistryEntry,
    ProposeNpcResult,
)
from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.persistence import (
    NpcLifecyclePersistenceRecord,
    NpcProfilePersistenceRecord,
)

_ACTIVE_STATUSES: frozenset[str] = frozenset({"proposed", "active"})
_ORDINARY_ACTOR_STATUSES: frozenset[str] = frozenset({"active"})
_ARCHIVABLE_FROM: frozenset[str] = frozenset({"proposed", "active", "retained"})


def proposal_from_director_stub(
    stub: ProposedNpcStub,
    *,
    traits: Sequence[str] = (),
    source_hook_key: str | None = None,
    source_hook_id: UUID | None = None,
    category: str = "TEMPORARY_NAMED",
) -> NpcProposalInput:
    """Map a Director ``ProposedNpcStub`` into a registry proposal input."""

    return NpcProposalInput(
        proposed_name=stub.proposed_name,
        role_tags=tuple(stub.role_tags),
        traits=tuple(traits),
        location_key=stub.location_key,
        source_hook_key=source_hook_key,
        source_hook_id=source_hook_id,
        narrative_purpose=stub.narrative_purpose,
        category=category,
    )


def find_duplicate(
    proposal: NpcProposalInput,
    existing: Sequence[NpcRegistryEntry],
) -> NpcRegistryEntry | None:
    """Return the first existing NPC matching the proposal fingerprint."""

    fingerprint = compute_similarity_fingerprint(
        name=proposal.proposed_name,
        location_key=proposal.location_key,
        role_tags=proposal.role_tags,
        traits=proposal.traits,
        source_hook_key=proposal.source_hook_key,
    )
    for entry in existing:
        if entry.similarity_fingerprint == fingerprint:
            return entry
    return None


def propose_or_register_npc(
    proposal: NpcProposalInput,
    *,
    world_id: UUID,
    current_phase_index: int,
    existing: Sequence[NpcRegistryEntry],
    budgets: BudgetSnapshot,
    character_id: UUID | None = None,
    budget_config: NpcBudgetConfig | None = None,
    ttl_config: NpcTtlConfig | None = None,
    counts_toward_scene: bool = True,
) -> ProposeNpcResult:
    """Director proposal path: dedup by fingerprint, else budget-check and register.

    Does **not** promote NPCs into focus slots. Persistence is the caller's job.
    """

    if current_phase_index < 0:
        raise InvalidAction("current_phase_index must be >= 0")

    duplicate = find_duplicate(proposal, existing)
    if duplicate is not None:
        return ProposeNpcResult(
            status="reused",
            entry=duplicate,
            created_new=False,
            reused_existing=True,
        )

    violation = check_new_npc_budgets(
        budgets,
        config=budget_config,
        counts_toward_scene=counts_toward_scene,
    )
    if violation is not None:
        return ProposeNpcResult(
            status="rejected",
            entry=None,
            created_new=False,
            violation=violation,
        )

    ttl_cfg = ttl_config or NpcTtlConfig()
    card = build_compact_card(proposal)
    fingerprint = compute_similarity_fingerprint(
        name=proposal.proposed_name,
        location_key=proposal.location_key,
        role_tags=proposal.role_tags,
        traits=proposal.traits,
        source_hook_key=proposal.source_hook_key,
    )
    entry = NpcRegistryEntry(
        character_id=character_id or uuid4(),
        world_id=world_id,
        display_name=proposal.proposed_name,
        role_tags=tuple(proposal.role_tags),
        traits=tuple(proposal.traits),
        location_key=proposal.location_key,
        source_hook_key=proposal.source_hook_key,
        source_hook_id=proposal.source_hook_id,
        similarity_fingerprint=fingerprint,
        compact_card=card,
        lifecycle_status="active",
        activated_phase_index=current_phase_index,
        archive_phase_index=None,
        ttl_until_phase=current_phase_index + ttl_cfg.default_ttl_phases,
        relevance_score=Decimal("0.5"),
        archive_summary=None,
        last_scene_phase_index=None,
        version=0,
    )
    return ProposeNpcResult(
        status="registered",
        entry=entry,
        created_new=True,
        reused_existing=False,
    )


def extend_ttl_on_meaningful_scene(
    entry: NpcRegistryEntry,
    *,
    current_phase_index: int,
    ttl_config: NpcTtlConfig | None = None,
    relevance_bump: Decimal = Decimal("0.1"),
) -> NpcRegistryEntry:
    """Extend TTL and mark last scene after a meaningful on-screen appearance."""

    if entry.lifecycle_status not in _ACTIVE_STATUSES:
        raise InvalidAction(f"cannot extend TTL for NPC in status {entry.lifecycle_status!r}")
    if current_phase_index < 0:
        raise InvalidAction("current_phase_index must be >= 0")

    ttl_cfg = ttl_config or NpcTtlConfig()
    extended = current_phase_index + ttl_cfg.meaningful_scene_extension_phases
    current_ttl = entry.ttl_until_phase if entry.ttl_until_phase is not None else 0
    new_ttl = max(current_ttl, extended)
    new_relevance = min(Decimal("1.0"), entry.relevance_score + relevance_bump)
    return entry.model_copy(
        update={
            "ttl_until_phase": new_ttl,
            "last_scene_phase_index": current_phase_index,
            "relevance_score": new_relevance,
            "version": entry.version + 1,
        }
    )


def archive_npc(
    entry: NpcRegistryEntry,
    *,
    archive_phase_index: int,
    archive_summary: str,
) -> NpcRegistryEntry:
    """Archive an NPC with a compact legacy summary; stops ordinary actor scheduling."""

    if entry.lifecycle_status not in _ARCHIVABLE_FROM:
        raise InvalidStateTransition(
            entity="npc_lifecycle",
            from_state=entry.lifecycle_status,
            to_state="archived",
        )
    if archive_phase_index < 0:
        raise InvalidAction("archive_phase_index must be >= 0")
    summary = archive_summary.strip()
    if not summary:
        raise InvalidAction("archive_summary must be non-empty")

    return entry.model_copy(
        update={
            "lifecycle_status": "archived",
            "archive_phase_index": archive_phase_index,
            "archive_summary": summary[:4_000],
            "ttl_until_phase": None,
            "relevance_score": Decimal("0.0"),
            "version": entry.version + 1,
        }
    )


def may_receive_ordinary_actor_task(entry: NpcRegistryEntry) -> bool:
    """Archived/retained/proposed NPCs are not scheduled for ordinary actor tasks."""

    return entry.lifecycle_status in _ORDINARY_ACTOR_STATUSES


def recall_archived_npc(entry: NpcRegistryEntry) -> NpcRegistryEntry:
    """Return the archived entry for continuity lookup without enabling actor tasks.

    Identity and ``archive_summary`` remain available; status is unchanged.
    """

    if entry.lifecycle_status != "archived":
        raise InvalidAction(
            f"recall_archived_npc requires archived status, got {entry.lifecycle_status!r}"
        )
    return entry


def to_profile_record(entry: NpcRegistryEntry) -> NpcProfilePersistenceRecord:
    """Map registry entry → ``npc_profile`` persistence record."""

    return NpcProfilePersistenceRecord(
        character_id=entry.character_id,
        world_id=entry.world_id,
        display_name=entry.display_name,
        role_tags=entry.role_tags,
        compact_card=compact_card_as_json(entry.compact_card),
        source_hook_id=entry.source_hook_id,
        similarity_fingerprint=entry.similarity_fingerprint,
        version=entry.version,
    )


def to_lifecycle_record(entry: NpcRegistryEntry) -> NpcLifecyclePersistenceRecord:
    """Map registry entry → ``npc_lifecycle`` persistence record."""

    return NpcLifecyclePersistenceRecord(
        character_id=entry.character_id,
        world_id=entry.world_id,
        lifecycle_status=entry.lifecycle_status,
        activated_phase_index=entry.activated_phase_index,
        archive_phase_index=entry.archive_phase_index,
        ttl_until_phase=entry.ttl_until_phase,
        relevance_score=entry.relevance_score,
        archive_summary=entry.archive_summary,
        last_scene_phase_index=entry.last_scene_phase_index,
        version=entry.version,
    )


__all__ = [
    "archive_npc",
    "extend_ttl_on_meaningful_scene",
    "find_duplicate",
    "may_receive_ordinary_actor_task",
    "proposal_from_director_stub",
    "propose_or_register_npc",
    "recall_archived_npc",
    "to_lifecycle_record",
    "to_profile_record",
]
