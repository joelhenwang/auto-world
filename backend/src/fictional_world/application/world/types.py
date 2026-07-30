"""Pacing / novelty contracts for Stage 3 anti-repetition scoring."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.stage3.persistence import (
    NoveltySignaturePersistenceRecord,
    TropeUsagePersistenceRecord,
)


class PacingMetricsSnapshot(StrictContract):
    """Rolling repetition / balance metrics used by novelty scoring."""

    location_repetition_ratio: float = Field(ge=0, le=1)
    participant_combo_ratio: float = Field(ge=0, le=1)
    action_family_ratio: float = Field(ge=0, le=1)
    quiet_share: float = Field(ge=0, le=1)
    dramatic_share: float = Field(ge=0, le=1)
    quiet_dramatic_balance: float = Field(
        ge=0,
        le=1,
        description="1.0 = balanced; lower = skewed toward quiet or dramatic",
    )
    tropes_in_cooldown: tuple[str, ...] = ()
    matching_signature_hashes: tuple[str, ...] = ()


class NoveltyScoreBreakdown(StrictContract):
    base_score: float = Field(ge=0, le=1)
    trope_penalty: float = Field(ge=0, le=1)
    location_penalty: float = Field(ge=0, le=1)
    participant_penalty: float = Field(ge=0, le=1)
    action_family_penalty: float = Field(ge=0, le=1)
    balance_penalty: float = Field(ge=0, le=1)
    signature_penalty: float = Field(ge=0, le=1)
    disruptive_penalty: float = Field(ge=0, le=1)
    causality_boost_applied: bool = False
    final_score: float = Field(ge=0, le=1)


class NoveltyScoreResult(StrictContract):
    """Soft score for Director proposal selection — not a hard validation ban."""

    score: float = Field(ge=0, le=1)
    metrics: PacingMetricsSnapshot
    breakdown: NoveltyScoreBreakdown
    allowed_despite_cooldown: bool = False
    reasons: tuple[str, ...] = ()


class NoveltyHistory(StrictContract):
    """In-memory rolling history for pure scoring (repos optional later)."""

    world_id: UUID
    current_phase_index: int = Field(ge=0)
    trope_usages: tuple[TropeUsagePersistenceRecord, ...] = ()
    signatures: tuple[NoveltySignaturePersistenceRecord, ...] = ()
    recent_location_ids: tuple[UUID | None, ...] = ()
    recent_participant_combos: tuple[str, ...] = ()
    recent_action_families: tuple[str, ...] = ()
    recent_proposal_kinds: tuple[str, ...] = ()
