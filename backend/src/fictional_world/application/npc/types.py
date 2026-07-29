"""NPC registry contracts (propose / reuse / archive / knowledge package)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]

NpcLifecycleStatusName = Literal["proposed", "active", "archived", "retained"]
ProposeOutcomeStatus = Literal["reused", "registered", "rejected"]


class NpcProposalInput(StrictContract):
    """Director-originated NPC blueprint for registry validation/dedup."""

    proposed_name: str = Field(min_length=1, max_length=200)
    role_tags: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    location_key: str | None = Field(default=None, max_length=200)
    source_hook_key: str | None = Field(default=None, max_length=200)
    source_hook_id: UUID | None = None
    narrative_purpose: str = Field(min_length=1, max_length=1_000)
    category: str = Field(default="TEMPORARY_NAMED", min_length=1, max_length=50)
    appearance: str | None = Field(default=None, max_length=1_000)
    personality: str | None = Field(default=None, max_length=1_000)


class NpcCompactCard(StrictContract):
    """Public-facing compact identity card — never carries director secrets."""

    display_name: str = Field(min_length=1, max_length=200)
    role_tags: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    location_key: str | None = None
    narrative_purpose: str = Field(min_length=1, max_length=1_000)
    category: str = Field(min_length=1, max_length=50)
    appearance: str | None = None
    personality: str | None = None
    source_hook_key: str | None = None


class NpcRegistryEntry(StrictContract):
    """In-memory registry row combining profile + lifecycle for pure checks."""

    character_id: UUID
    world_id: UUID
    display_name: str = Field(min_length=1, max_length=200)
    role_tags: tuple[str, ...] = ()
    traits: tuple[str, ...] = ()
    location_key: str | None = None
    source_hook_key: str | None = None
    source_hook_id: UUID | None = None
    similarity_fingerprint: str = Field(min_length=1, max_length=256)
    compact_card: NpcCompactCard
    lifecycle_status: NpcLifecycleStatusName
    activated_phase_index: int | None = None
    archive_phase_index: int | None = None
    ttl_until_phase: int | None = None
    relevance_score: Decimal = Field(default=Decimal("0.5"))
    archive_summary: str | None = Field(default=None, max_length=4_000)
    last_scene_phase_index: int | None = None
    version: int = Field(default=0, ge=0)


class BudgetSnapshot(StrictContract):
    """Current usage counters for pure budget enforcement."""

    detailed_npcs_in_scene: int = Field(ge=0)
    active_detailed_in_region: int = Field(ge=0)
    new_named_today: int = Field(ge=0)


class BudgetViolation(StrictContract):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)


class ProposeNpcResult(StrictContract):
    status: ProposeOutcomeStatus
    entry: NpcRegistryEntry | None = None
    created_new: bool = False
    violation: BudgetViolation | None = None
    reused_existing: bool = False


class NpcKnowledgePackage(StrictContract):
    """Perspective package for an NPC actor — never omniscient Director data."""

    character_id: UUID
    compact_card: NpcCompactCard
    beliefs: tuple[dict[str, Any], ...] = ()
    secret_keys: tuple[str, ...] = ()
    secret_summaries: tuple[dict[str, Any], ...] = ()
    may_receive_ordinary_actor_task: bool
