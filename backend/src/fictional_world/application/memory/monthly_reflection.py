"""Monthly chapter, reflection, and forgetting (S3-MEM-003)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.domain.stage3.persistence import (
    MemoryPersistenceRecord,
    MonthlyChapterPersistenceRecord,
    ReflectionRunPersistenceRecord,
)

MAX_TRAIT_DELTA = Decimal("0.10")
MIN_EVIDENCE_SOURCES = 2
IDENTITY_MEMORY_TYPES = frozenset({"identity", "commitment", "promise", "secret"})


@dataclass(frozen=True, slots=True)
class TraitChangeProposal:
    trait_key: str
    value_before: Decimal
    value_after: Decimal
    evidence_memory_ids: tuple[UUID, ...]
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class TraitValidationResult:
    accepted: tuple[TraitChangeProposal, ...]
    rejected: tuple[TraitChangeProposal, ...]
    rejection_reasons: Mapping[str, str]


def reflection_idempotency_key(world_id: UUID, owner_character_id: UUID, month_index: int) -> str:
    return f"month-reflection:{world_id}:{owner_character_id}:{month_index}"


def _hash_content(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def filter_owner_memories_for_month(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    world_id: UUID,
    owner_character_id: UUID,
    start_phase_index: int,
    end_phase_index: int,
) -> tuple[MemoryPersistenceRecord, ...]:
    out: list[MemoryPersistenceRecord] = []
    for memory in memories:
        if memory.world_id != world_id:
            continue
        if memory.owner_character_id != owner_character_id:
            continue
        if memory.created_phase_index < start_phase_index:
            continue
        if memory.created_phase_index > end_phase_index:
            continue
        out.append(memory)
    return tuple(out)


def build_monthly_chapter(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    world_id: UUID,
    owner_character_id: UUID,
    month_index: int,
    start_phase_index: int,
    end_phase_index: int,
    chapter_id: UUID | None = None,
) -> MonthlyChapterPersistenceRecord:
    """Extractive monthly chapter from owner-scoped memories only."""

    owned = filter_owner_memories_for_month(
        memories,
        world_id=world_id,
        owner_character_id=owner_character_id,
        start_phase_index=start_phase_index,
        end_phase_index=end_phase_index,
    )
    lines = [
        m.content for m in sorted(owned, key=lambda m: (-float(m.salience), m.created_phase_index))
    ]
    body = "\n".join(lines[:40]) if lines else "A quiet month with little to record."
    title = f"Month {month_index} chapter"
    structured = {
        "memory_ids": [str(m.id) for m in owned],
        "memory_count": len(owned),
        "top_salience": [float(m.salience) for m in owned[:5]],
    }
    return MonthlyChapterPersistenceRecord(
        id=chapter_id or uuid4(),
        world_id=world_id,
        owner_character_id=owner_character_id,
        month_index=month_index,
        start_phase_index=start_phase_index,
        end_phase_index=end_phase_index,
        title=title,
        content=body,
        structured_extract=structured,
        content_hash=_hash_content({"title": title, "content": body, "structured": structured}),
        version_number=1,
    )


def validate_trait_changes(
    proposals: Sequence[TraitChangeProposal],
    *,
    available_memory_ids: set[UUID],
    max_abs_delta: Decimal = MAX_TRAIT_DELTA,
    min_evidence: int = MIN_EVIDENCE_SOURCES,
) -> TraitValidationResult:
    accepted: list[TraitChangeProposal] = []
    rejected: list[TraitChangeProposal] = []
    reasons: dict[str, str] = {}
    for proposal in proposals:
        delta = abs(proposal.value_after - proposal.value_before)
        if delta > max_abs_delta:
            rejected.append(proposal)
            reasons[proposal.trait_key] = "delta_exceeds_maximum"
            continue
        if len(proposal.evidence_memory_ids) < min_evidence:
            rejected.append(proposal)
            reasons[proposal.trait_key] = "insufficient_evidence"
            continue
        if any(mid not in available_memory_ids for mid in proposal.evidence_memory_ids):
            rejected.append(proposal)
            reasons[proposal.trait_key] = "unknown_or_foreign_evidence"
            continue
        accepted.append(proposal)
    return TraitValidationResult(
        accepted=tuple(accepted),
        rejected=tuple(rejected),
        rejection_reasons=reasons,
    )


def apply_forgetting_weights(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    decay_factor: Decimal = Decimal("0.85"),
) -> tuple[MemoryPersistenceRecord, ...]:
    """Decay ordinary retrieval weights without deleting raw memory."""

    out: list[MemoryPersistenceRecord] = []
    for memory in memories:
        if memory.memory_type in IDENTITY_MEMORY_TYPES:
            out.append(memory)
            continue
        new_decay = max(Decimal("0"), min(Decimal("1"), memory.decay_score * decay_factor))
        out.append(memory.model_copy(update={"decay_score": new_decay}))
    return tuple(out)


def build_reflection_run(
    *,
    world_id: UUID,
    owner_character_id: UUID,
    month_index: int,
    chapter: MonthlyChapterPersistenceRecord,
    proposals: Sequence[TraitChangeProposal],
    available_memory_ids: set[UUID],
    run_id: UUID | None = None,
) -> ReflectionRunPersistenceRecord:
    validated = validate_trait_changes(proposals, available_memory_ids=available_memory_ids)
    return ReflectionRunPersistenceRecord(
        id=run_id or uuid4(),
        world_id=world_id,
        owner_character_id=owner_character_id,
        month_index=month_index,
        status="completed",
        idempotency_key=reflection_idempotency_key(world_id, owner_character_id, month_index),
        proposed_trait_changes={
            p.trait_key: {
                "before": float(p.value_before),
                "after": float(p.value_after),
                "evidence": [str(x) for x in p.evidence_memory_ids],
            }
            for p in proposals
        },
        accepted_trait_changes={
            p.trait_key: {
                "before": float(p.value_before),
                "after": float(p.value_after),
                "evidence": [str(x) for x in p.evidence_memory_ids],
            }
            for p in validated.accepted
        },
        rejected_trait_changes={
            p.trait_key: {
                "reason": validated.rejection_reasons.get(p.trait_key, "rejected"),
                "before": float(p.value_before),
                "after": float(p.value_after),
            }
            for p in validated.rejected
        },
        evidence_refs={"memory_ids": [str(x) for x in available_memory_ids]},
        monthly_chapter_id=chapter.id,
    )
