"""Unit tests for NPC registry and actor v1 (S2-WORLD-002)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.application.director.types import ProposedNpcStub
from fictional_world.application.knowledge.lookup import DEFAULT_DIRECTOR_ONLY
from fictional_world.application.npc import (
    BudgetSnapshot,
    NpcBudgetConfig,
    NpcProposalInput,
    NpcRegistryEntry,
    NpcTtlConfig,
    archive_npc,
    build_npc_knowledge_package,
    check_new_npc_budgets,
    compute_similarity_fingerprint,
    extend_ttl_on_meaningful_scene,
    may_receive_ordinary_actor_task,
    package_contains_forbidden_text,
    proposal_from_director_stub,
    propose_or_register_npc,
    recall_archived_npc,
)
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.knowledge.visibility import SecretAccessLevel

DIRECTOR_ONLY_FACT = next(iter(DEFAULT_DIRECTOR_ONLY))
OMNISCIENT_SECRET = "director omniscient: Mira's father true name is sealed"  # noqa: S105


@pytest.fixture
def world_id() -> UUID:
    return uuid4()


def _blacksmith_proposal(
    *,
    name: str = "Harn the Blacksmith",
    location_key: str = "embervale.forge",
    hook: str = "forge_repair_day2",
) -> NpcProposalInput:
    return NpcProposalInput(
        proposed_name=name,
        role_tags=("blacksmith", "craftsman"),
        traits=("sturdy", "practical", "quiet"),
        location_key=location_key,
        source_hook_key=hook,
        narrative_purpose="Repair tools and offer local forge gossip.",
        category="TEMPORARY_NAMED",
        appearance="Soot-stained apron, thick forearms",
        personality="Terse but fair",
    )


def _register_blacksmith(world_id: UUID, *, phase: int = 10) -> NpcRegistryEntry:
    result = propose_or_register_npc(
        _blacksmith_proposal(),
        world_id=world_id,
        current_phase_index=phase,
        existing=(),
        budgets=BudgetSnapshot(
            detailed_npcs_in_scene=0,
            active_detailed_in_region=0,
            new_named_today=0,
        ),
    )
    assert result.status == "registered"
    assert result.entry is not None
    return result.entry


def _belief(
    *,
    character_id: UUID,
    world_id: UUID,
    text: str,
    prop_key: str | None = None,
) -> BeliefPersistenceRecord:
    return BeliefPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        character_id=character_id,
        proposition_key=prop_key or f"belief.{uuid4().hex[:12]}",
        belief_text=text,
        confidence=Decimal("0.7"),
        status="active",
    )


def _secret(
    *,
    world_id: UUID,
    owner: UUID,
    holder: UUID,
    secret_key: str,
) -> SecretAccessPersistenceRecord:
    return SecretAccessPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        secret_key=secret_key,
        owner_character_id=owner,
        holder_character_id=holder,
        access_level=SecretAccessLevel.OWNER.value,
    )


@pytest.mark.unit
def test_duplicate_blacksmith_resolves_to_existing(world_id: UUID) -> None:
    existing = _register_blacksmith(world_id)
    assert existing.display_name == "Harn the Blacksmith"

    duplicate_stub = ProposedNpcStub(
        proposed_name="Harn the Blacksmith",
        role_tags=("blacksmith", "craftsman"),
        narrative_purpose="Repair tools and offer local forge gossip.",
        location_key="embervale.forge",
    )
    proposal = proposal_from_director_stub(
        duplicate_stub,
        traits=("sturdy", "practical", "quiet"),
        source_hook_key="forge_repair_day2",
    )
    # Fingerprint matches regardless of whitespace/case on role order.
    assert (
        compute_similarity_fingerprint(
            name=proposal.proposed_name,
            location_key=proposal.location_key,
            role_tags=proposal.role_tags,
            traits=proposal.traits,
            source_hook_key=proposal.source_hook_key,
        )
        == existing.similarity_fingerprint
    )

    result = propose_or_register_npc(
        proposal,
        world_id=world_id,
        current_phase_index=12,
        existing=(existing,),
        budgets=BudgetSnapshot(
            detailed_npcs_in_scene=1,
            active_detailed_in_region=1,
            new_named_today=1,
        ),
    )
    assert result.status == "reused"
    assert result.reused_existing is True
    assert result.created_new is False
    assert result.entry is not None
    assert result.entry.character_id == existing.character_id


@pytest.mark.unit
def test_npc_knowledge_package_excludes_director_and_omniscient(world_id: UUID) -> None:
    entry = _register_blacksmith(world_id)
    npc_id = entry.character_id
    other_id = uuid4()

    beliefs = [
        _belief(
            character_id=npc_id,
            world_id=world_id,
            text="The forge bellows need a new leather patch.",
        ),
        _belief(
            character_id=npc_id,
            world_id=world_id,
            text=DIRECTOR_ONLY_FACT,
        ),
        _belief(
            character_id=npc_id,
            world_id=world_id,
            text=OMNISCIENT_SECRET,
        ),
        _belief(
            character_id=other_id,
            world_id=world_id,
            text="Someone else's private plan to leave town.",
        ),
    ]
    # Omniscient director secret is NOT granted to the NPC.
    secrets = [
        _secret(
            world_id=world_id,
            owner=other_id,
            holder=other_id,
            secret_key="mira.father.true_name",  # noqa: S106 — fixture key, not a password
        ),
    ]

    package = build_npc_knowledge_package(
        entry,
        beliefs=beliefs,
        secret_access=secrets,
        director_only_texts=(DIRECTOR_ONLY_FACT,),
        omniscient_secret_texts=(OMNISCIENT_SECRET,),
    )

    assert package.character_id == npc_id
    assert package.may_receive_ordinary_actor_task is True
    assert any("bellows" in str(b.get("proposition", "")) for b in package.beliefs)
    assert not package_contains_forbidden_text(
        package,
        (DIRECTOR_ONLY_FACT, OMNISCIENT_SECRET, "mira.father.true_name"),
    )
    assert "mira.father.true_name" not in package.secret_keys
    assert all("Someone else's private plan" not in str(b) for b in package.beliefs)


@pytest.mark.unit
def test_ttl_extends_after_meaningful_scene(world_id: UUID) -> None:
    short_ttl = NpcTtlConfig(default_ttl_phases=5, meaningful_scene_extension_phases=10)
    result = propose_or_register_npc(
        _blacksmith_proposal(),
        world_id=world_id,
        current_phase_index=10,
        existing=(),
        budgets=BudgetSnapshot(
            detailed_npcs_in_scene=0,
            active_detailed_in_region=0,
            new_named_today=0,
        ),
        ttl_config=short_ttl,
    )
    entry = result.entry
    assert entry is not None
    assert entry.ttl_until_phase == 15
    assert entry.last_scene_phase_index is None

    extended = extend_ttl_on_meaningful_scene(
        entry,
        current_phase_index=18,
        ttl_config=short_ttl,
    )
    assert extended.last_scene_phase_index == 18
    assert extended.ttl_until_phase == 28
    assert extended.relevance_score > entry.relevance_score
    assert extended.version == entry.version + 1

    # Later smaller extension keeps the higher TTL.
    again = extend_ttl_on_meaningful_scene(
        extended,
        current_phase_index=20,
        ttl_config=NpcTtlConfig(meaningful_scene_extension_phases=5),
    )
    assert again.ttl_until_phase == 28
    assert again.last_scene_phase_index == 20


@pytest.mark.unit
def test_archive_blocks_ordinary_actor_tasks_but_allows_recall(world_id: UUID) -> None:
    entry = _register_blacksmith(world_id)
    assert may_receive_ordinary_actor_task(entry) is True

    archived = archive_npc(
        entry,
        archive_phase_index=40,
        archive_summary="Harn returned to quiet forge work; no longer on-screen.",
    )
    assert archived.lifecycle_status == "archived"
    assert archived.archive_phase_index == 40
    assert archived.archive_summary is not None
    assert "quiet forge" in archived.archive_summary
    assert archived.ttl_until_phase is None
    assert may_receive_ordinary_actor_task(archived) is False

    recalled = recall_archived_npc(archived)
    assert recalled.character_id == archived.character_id
    assert recalled.lifecycle_status == "archived"
    assert may_receive_ordinary_actor_task(recalled) is False

    with pytest.raises(InvalidAction):
        extend_ttl_on_meaningful_scene(archived, current_phase_index=41)


@pytest.mark.unit
def test_budget_rejection_scene_region_and_daily(world_id: UUID) -> None:
    proposal = _blacksmith_proposal(name="Other Smith", hook="other_hook")
    cfg = NpcBudgetConfig(
        max_detailed_per_scene=6,
        max_active_in_region=24,
        max_new_named_per_day=3,
    )

    scene_full = BudgetSnapshot(
        detailed_npcs_in_scene=6,
        active_detailed_in_region=1,
        new_named_today=0,
    )
    assert check_new_npc_budgets(scene_full, config=cfg) is not None
    scene_reject = propose_or_register_npc(
        proposal,
        world_id=world_id,
        current_phase_index=5,
        existing=(),
        budgets=scene_full,
        budget_config=cfg,
    )
    assert scene_reject.status == "rejected"
    assert scene_reject.violation is not None
    assert scene_reject.violation.code == "scene_detailed_npc_budget"

    region_full = BudgetSnapshot(
        detailed_npcs_in_scene=1,
        active_detailed_in_region=24,
        new_named_today=0,
    )
    region_reject = propose_or_register_npc(
        proposal,
        world_id=world_id,
        current_phase_index=5,
        existing=(),
        budgets=region_full,
        budget_config=cfg,
    )
    assert region_reject.status == "rejected"
    assert region_reject.violation is not None
    assert region_reject.violation.code == "region_active_npc_budget"

    day_full = BudgetSnapshot(
        detailed_npcs_in_scene=1,
        active_detailed_in_region=1,
        new_named_today=3,
    )
    day_reject = propose_or_register_npc(
        proposal,
        world_id=world_id,
        current_phase_index=5,
        existing=(),
        budgets=day_full,
        budget_config=cfg,
    )
    assert day_reject.status == "rejected"
    assert day_reject.violation is not None
    assert day_reject.violation.code == "daily_new_named_npc_budget"

    # Reuse bypasses budgets even when counters are saturated.
    existing = _register_blacksmith(world_id)
    reused = propose_or_register_npc(
        _blacksmith_proposal(),
        world_id=world_id,
        current_phase_index=6,
        existing=(existing,),
        budgets=day_full,
        budget_config=cfg,
    )
    assert reused.status == "reused"
    assert reused.entry is not None
    assert reused.entry.character_id == existing.character_id
