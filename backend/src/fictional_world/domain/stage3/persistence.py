"""Stage 3 persistence records (memory / rules / world / quality)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class MemoryPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    memory_type: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=8_000)
    salience: Decimal
    confidence: Decimal
    emotional_weight: Decimal
    visibility: str = Field(min_length=1, max_length=50)
    occurred_phase_index: int = Field(ge=0)
    created_phase_index: int = Field(ge=0)
    last_recalled_phase_index: int | None = Field(default=None, ge=0)
    recall_count: int = Field(default=0, ge=0)
    decay_score: Decimal
    status: str = Field(default="active", min_length=1, max_length=50)
    content_hash: str = Field(min_length=1, max_length=128)
    summary_version: int = Field(default=1, ge=1)
    goal_relevance: Decimal = Decimal("0")
    emotional_resonance: Decimal = Decimal("0")
    unresolved_commitment: Decimal = Decimal("0")
    referenced_entity_ids: tuple[UUID, ...] = ()
    source_event_id: UUID | None = None
    created_at: datetime | None = None


class MemorySourcePersistenceRecord(StrictContract):
    id: UUID
    memory_id: UUID
    source_kind: str = Field(min_length=1, max_length=50)
    source_id: UUID
    source_role: str = Field(default="primary", min_length=1, max_length=50)
    weight: Decimal = Decimal("1")
    ordinal: int = Field(default=0, ge=0)


class EmbeddingModelVersionPersistenceRecord(StrictContract):
    id: UUID
    model_key: str = Field(min_length=1, max_length=100)
    provider: str = Field(min_length=1, max_length=100)
    model_slug: str = Field(min_length=1, max_length=200)
    dimension: int = Field(ge=1)
    query_prefix: str
    passage_prefix: str
    truncation_policy: str = "truncate_tail"
    embedding_version: int = Field(ge=1)
    is_active: bool = False
    capability_probe: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class MemoryEmbeddingPersistenceRecord(StrictContract):
    id: UUID
    memory_id: UUID
    world_id: UUID
    owner_character_id: UUID
    embedding_model_key: str
    embedding_version: int = Field(ge=1)
    dimension: int = Field(ge=1)
    prefix_type: str
    embedded_content_hash: str
    embedding: tuple[float, ...]
    is_active: bool = True
    created_at: datetime | None = None


class EmbeddingJobPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    memory_id: UUID
    embedding_model_key: str
    embedding_version: int = Field(ge=1)
    status: str = "pending"
    idempotency_key: str
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class RetrievalTracePersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    request_phase_index: int = Field(ge=0)
    query_text: str
    filters: dict[str, Any] = Field(default_factory=dict)
    candidate_memory_ids: tuple[UUID, ...] = ()
    selected_memory_ids: tuple[UUID, ...] = ()
    scores: dict[str, Any] = Field(default_factory=dict)
    embedding_model_key: str | None = None
    embedding_version: int | None = Field(default=None, ge=1)
    used_semantic: bool = False
    reranker_status: str = "skipped"
    model_call_id: UUID | None = None
    created_at: datetime | None = None


class MonthlyChapterPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    month_index: int = Field(ge=1)
    start_phase_index: int = Field(ge=0)
    end_phase_index: int = Field(ge=0)
    title: str
    content: str
    structured_extract: dict[str, Any] = Field(default_factory=dict)
    content_hash: str
    version_number: int = Field(default=1, ge=1)
    model_call_id: UUID | None = None
    created_at: datetime | None = None


class ReflectionRunPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    month_index: int = Field(ge=1)
    status: str = "pending"
    idempotency_key: str
    proposed_trait_changes: dict[str, Any] = Field(default_factory=dict)
    accepted_trait_changes: dict[str, Any] = Field(default_factory=dict)
    rejected_trait_changes: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: dict[str, Any] = Field(default_factory=dict)
    monthly_chapter_id: UUID | None = None
    model_call_id: UUID | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class StatStatePersistenceRecord(StrictContract):
    character_id: UUID
    world_id: UUID
    stat_code: str
    current_value: Decimal
    dynamic_potential_cap: Decimal
    growth_rate: Decimal
    adaptability: Decimal
    last_source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class SkillDefinitionPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    skill_code: str
    name: str
    category: str
    description: str = ""
    governing_stats: tuple[str, ...] = ()
    prerequisites: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    version: int = Field(default=0, ge=0)


class SkillStatePersistenceRecord(StrictContract):
    character_id: UUID
    skill_definition_id: UUID
    world_id: UUID
    proficiency: Decimal = Decimal("0")
    evidence_total: Decimal = Decimal("0")
    plateau_flag: bool = False
    teacher_character_id: UUID | None = None
    last_source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class SpellDefinitionPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    spell_code: str
    name: str
    school: str
    elements: tuple[str, ...] = ()
    prerequisites: dict[str, Any] = Field(default_factory=dict)
    mana_cost_min: Decimal
    mana_cost_max: Decimal
    cast_time_beats: int = Field(default=1, ge=0)
    range_desc: str = "touch"
    target_rules: dict[str, Any] = Field(default_factory=dict)
    possible_effects: dict[str, Any] = Field(default_factory=dict)
    failure_modes: dict[str, Any] = Field(default_factory=dict)
    counters: dict[str, Any] = Field(default_factory=dict)
    visibility: str = "public"
    status: str = "active"
    version: int = Field(default=0, ge=0)


class KnownSpellPersistenceRecord(StrictContract):
    character_id: UUID
    spell_definition_id: UUID
    world_id: UUID
    proficiency: Decimal = Decimal("0")
    discovery_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class InjuryPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    character_id: UUID
    body_region: str
    injury_type: str
    severity: Decimal
    bleeding: Decimal = Decimal("0")
    pain: Decimal = Decimal("0")
    mobility_penalty: Decimal = Decimal("0")
    consciousness_impact: Decimal = Decimal("0")
    infection_risk: Decimal = Decimal("0")
    healing_progress: Decimal = Decimal("0")
    treatment: dict[str, Any] = Field(default_factory=dict)
    permanent_consequence: bool = False
    status: str = "active"
    inflicted_event_id: UUID | None = None
    healed_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConditionPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    character_id: UUID
    condition_code: str
    severity: Decimal
    status: str = "active"
    started_phase_index: int = Field(ge=0)
    expected_end_phase_index: int | None = Field(default=None, ge=0)
    modifiers: dict[str, Any] = Field(default_factory=dict)
    source_event_id: UUID | None = None
    removed_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)


class ItemPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    item_code: str | None = None
    entity_id: UUID | None = None
    name: str
    item_kind: str
    stackable: bool = False
    properties: dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)


class InventoryEntryPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    item_id: UUID
    quantity: int = Field(default=1, ge=1)
    equipped_slot: str | None = None
    last_source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)


class FactionPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    faction_key: str
    name: str
    faction_type: str
    status: str = "active"
    leadership: dict[str, Any] = Field(default_factory=dict)
    territory_location_ids: tuple[UUID, ...] = ()
    goals: dict[str, Any] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    plans: dict[str, Any] = Field(default_factory=dict)
    plot_armour_bias: Decimal = Decimal("0")
    created_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None


class ArcPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    arc_key: str
    title: str
    arc_scope: str = "major"
    status: str = "dormant"
    premise: str
    objective: str
    milestones: dict[str, Any] = Field(default_factory=dict)
    prerequisites: dict[str, Any] = Field(default_factory=dict)
    closure_conditions: dict[str, Any] = Field(default_factory=dict)
    participant_entity_ids: tuple[UUID, ...] = ()
    dominant_genres: tuple[str, ...] = ()
    progress: Decimal = Decimal("0")
    deadline_phase_index: int | None = Field(default=None, ge=0)
    start_phase_index: int | None = Field(default=None, ge=0)
    end_phase_index: int | None = Field(default=None, ge=0)
    director_profile_key: str | None = None
    source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TropeUsagePersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    trope_tag: str
    phase_index: int = Field(ge=0)
    day_index: int = Field(ge=0)
    scene_id: UUID | None = None
    participant_ids: tuple[UUID, ...] = ()
    location_id: UUID | None = None
    cooldown_until_phase: int | None = Field(default=None, ge=0)
    content_hash: str | None = None
    created_at: datetime | None = None


class EvaluatorRunPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    scope: str
    target_ref: str | None = None
    status: str = "completed"
    idempotency_key: str
    findings_summary: dict[str, Any] = Field(default_factory=dict)
    requested_narration_regen: bool = False
    model_call_id: UUID | None = None
    created_at: datetime | None = None


class QualityFindingPersistenceRecord(StrictContract):
    id: UUID
    evaluator_run_id: UUID
    world_id: UUID
    finding_code: str
    severity: str = "info"
    message: str
    evidence_refs: dict[str, Any] = Field(default_factory=dict)
    can_mutate_canon: bool = False
    created_at: datetime | None = None


class ExportRunPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    export_kind: str
    status: str = "pending"
    idempotency_key: str
    artefact_uri: str | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)
    month_index: int | None = Field(default=None, ge=1)
    created_at: datetime | None = None
    completed_at: datetime | None = None


class MonthRunPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    month_index: int = Field(ge=1)
    status: str = "pending"
    start_day_index: int = Field(ge=0)
    end_day_index: int = Field(ge=0)
    idempotency_key: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None
