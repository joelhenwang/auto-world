"""Stage 3 long-term memory retrieval with mandatory owner filters (S3-MEM-002)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fictional_world.application.memory.embedding_pipeline import cosine_similarity
from fictional_world.domain.stage3.persistence import (
    MemoryEmbeddingPersistenceRecord,
    MemoryPersistenceRecord,
    RetrievalTracePersistenceRecord,
)

# Handbook 28 default composite weights
W_SEMANTIC = Decimal("0.35")
W_SALIENCE = Decimal("0.20")
W_GOAL = Decimal("0.15")
W_RECENCY = Decimal("0.10")
W_ENTITY = Decimal("0.10")
W_EMOTION = Decimal("0.05")
W_COMMITMENT = Decimal("0.05")

DEFAULT_TOKEN_BUDGET = 3500
DEFAULT_SELECT_COUNT = 10
CHARS_PER_TOKEN_EST = 4


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    world_id: UUID
    owner_character_id: UUID
    query_text: str
    request_phase_index: int
    query_embedding: tuple[float, ...] | None = None
    visibility_allowlist: tuple[str, ...] = ("private", "shared", "public")
    status: str = "active"
    max_results: int = DEFAULT_SELECT_COUNT
    token_budget: int = DEFAULT_TOKEN_BUDGET
    referenced_entity_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ScoredMemory:
    memory: MemoryPersistenceRecord
    score: Decimal
    components: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    selected: tuple[ScoredMemory, ...]
    candidates: tuple[ScoredMemory, ...]
    trace: RetrievalTracePersistenceRecord
    used_semantic: bool


def filter_memories_for_owner(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    world_id: UUID,
    owner_character_id: UUID,
    visibility_allowlist: Sequence[str] = ("private", "shared", "public"),
    status: str = "active",
    as_of_phase_index: int | None = None,
) -> tuple[MemoryPersistenceRecord, ...]:
    """Mandatory access predicates — apply in query layer, never in prompts."""

    allowed = set(visibility_allowlist)
    out: list[MemoryPersistenceRecord] = []
    for memory in memories:
        if memory.world_id != world_id:
            continue
        if memory.owner_character_id != owner_character_id:
            continue
        if memory.status != status:
            continue
        if memory.visibility not in allowed:
            continue
        if as_of_phase_index is not None and memory.created_phase_index > as_of_phase_index:
            continue
        out.append(memory)
    return tuple(out)


def _recency_score(memory: MemoryPersistenceRecord, *, request_phase: int) -> float:
    age = max(0, request_phase - memory.created_phase_index)
    return 1.0 / (1.0 + age / 50.0)


def _entity_overlap(memory: MemoryPersistenceRecord, referenced: Sequence[UUID]) -> float:
    if not referenced or not memory.referenced_entity_ids:
        return 0.0
    left = set(memory.referenced_entity_ids)
    right = set(referenced)
    return len(left & right) / max(1, len(right))


def score_memory(
    memory: MemoryPersistenceRecord,
    *,
    request: RetrievalRequest,
    semantic: float | None,
) -> ScoredMemory:
    sem = semantic if semantic is not None else 0.0
    components = {
        "semantic_similarity": sem,
        "salience": float(memory.salience),
        "goal_relevance": float(memory.goal_relevance),
        "recency": _recency_score(memory, request_phase=request.request_phase_index),
        "entity_overlap": _entity_overlap(memory, request.referenced_entity_ids),
        "emotional_resonance": float(memory.emotional_resonance),
        "unresolved_commitment": float(memory.unresolved_commitment),
    }
    total = (
        W_SEMANTIC * Decimal(str(components["semantic_similarity"]))
        + W_SALIENCE * Decimal(str(components["salience"]))
        + W_GOAL * Decimal(str(components["goal_relevance"]))
        + W_RECENCY * Decimal(str(components["recency"]))
        + W_ENTITY * Decimal(str(components["entity_overlap"]))
        + W_EMOTION * Decimal(str(components["emotional_resonance"]))
        + W_COMMITMENT * Decimal(str(components["unresolved_commitment"]))
    )
    return ScoredMemory(memory=memory, score=total, components=components)


def diversify_by_content_hash(
    scored: Sequence[ScoredMemory],
) -> tuple[ScoredMemory, ...]:
    seen: set[str] = set()
    out: list[ScoredMemory] = []
    for item in scored:
        key = item.memory.content_hash
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return tuple(out)


def select_under_token_budget(
    scored: Sequence[ScoredMemory],
    *,
    max_results: int,
    token_budget: int,
) -> tuple[ScoredMemory, ...]:
    selected: list[ScoredMemory] = []
    used = 0
    for item in scored:
        est = max(1, len(item.memory.content) // CHARS_PER_TOKEN_EST)
        if selected and used + est > token_budget:
            continue
        selected.append(item)
        used += est
        if len(selected) >= max_results:
            break
    return tuple(selected)


def retrieve_memories(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    request: RetrievalRequest,
    embeddings: Sequence[MemoryEmbeddingPersistenceRecord] = (),
    trace_id: UUID | None = None,
) -> RetrievalResult:
    """Retrieve with owner/visibility filters before any ranking."""

    filtered = filter_memories_for_owner(
        memories,
        world_id=request.world_id,
        owner_character_id=request.owner_character_id,
        visibility_allowlist=request.visibility_allowlist,
        status=request.status,
        as_of_phase_index=request.request_phase_index,
    )
    emb_by_memory = {
        e.memory_id: e
        for e in embeddings
        if e.is_active
        and e.owner_character_id == request.owner_character_id
        and e.world_id == request.world_id
    }
    used_semantic = request.query_embedding is not None and bool(emb_by_memory)
    scored: list[ScoredMemory] = []
    for memory in filtered:
        semantic: float | None = None
        if used_semantic and request.query_embedding is not None:
            emb = emb_by_memory.get(memory.id)
            if emb is not None:
                semantic = cosine_similarity(request.query_embedding, emb.embedding)
        scored.append(score_memory(memory, request=request, semantic=semantic))
    scored.sort(key=lambda s: s.score, reverse=True)
    diversified = diversify_by_content_hash(scored)
    selected = select_under_token_budget(
        diversified,
        max_results=request.max_results,
        token_budget=request.token_budget,
    )
    scores_payload: dict[str, Any] = {
        str(item.memory.id): {
            "score": float(item.score),
            "components": item.components,
        }
        for item in selected
    }
    trace = RetrievalTracePersistenceRecord(
        id=trace_id or uuid4(),
        world_id=request.world_id,
        owner_character_id=request.owner_character_id,
        request_phase_index=request.request_phase_index,
        query_text=request.query_text,
        filters={
            "visibility_allowlist": list(request.visibility_allowlist),
            "status": request.status,
        },
        candidate_memory_ids=tuple(m.memory.id for m in diversified[:50]),
        selected_memory_ids=tuple(m.memory.id for m in selected),
        scores=scores_payload,
        used_semantic=used_semantic,
        reranker_status="skipped",
    )
    return RetrievalResult(
        selected=selected,
        candidates=diversified,
        trace=trace,
        used_semantic=used_semantic,
    )
