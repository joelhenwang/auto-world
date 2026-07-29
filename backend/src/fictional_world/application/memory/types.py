"""Contracts for daily consolidation / diary pipeline (S2-MEM-001)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.continuity.persistence import (
    DailyAuditPersistenceRecord,
    DayRunPersistenceRecord,
    DiaryEntryPersistenceRecord,
    SummaryPersistenceRecord,
    SummarySourcePersistenceRecord,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord

JsonObject = dict[str, Any]


class ConsolidationProposal(StrictContract):
    """Model (or fake) consolidator output. Source IDs must ⊆ allowed set."""

    summary_content: str = Field(min_length=1, max_length=50_000)
    diary_content: str = Field(min_length=1, max_length=50_000)
    cited_source_ids: tuple[UUID, ...] = ()
    structured_extract: JsonObject = Field(default_factory=dict)


class CharacterConsolidationInput(StrictContract):
    """Perspective-filtered inputs handed to an optional consolidator."""

    world_id: UUID
    day_index: int = Field(ge=0)
    owner_character_id: UUID
    observations: tuple[ObservationPersistenceRecord, ...] = ()
    allowed_source_ids: tuple[UUID, ...] = ()
    held_secret_keys: tuple[str, ...] = ()


class CharacterDayConsolidation(StrictContract):
    """One character's daily summary + diary + provenance for a day."""

    owner_character_id: UUID
    summary: SummaryPersistenceRecord
    sources: tuple[SummarySourcePersistenceRecord, ...]
    diary: DiaryEntryPersistenceRecord
    used_model: bool = False
    fell_back_to_extractive: bool = False


class DailyConsolidationResult(StrictContract):
    """Full day consolidation output (idempotent under day_run key)."""

    world_id: UUID
    day_index: int = Field(ge=0)
    day_run: DayRunPersistenceRecord
    daily_audit: DailyAuditPersistenceRecord
    characters: tuple[CharacterDayConsolidation, ...]
    compacted_memories: tuple[RecentMemoryRecord, ...] = ()
    reused_prior: bool = False


ConsolidatorCallable = Callable[[CharacterConsolidationInput], ConsolidationProposal]


__all__ = [
    "CharacterConsolidationInput",
    "CharacterDayConsolidation",
    "ConsolidationProposal",
    "ConsolidatorCallable",
    "DailyConsolidationResult",
]
