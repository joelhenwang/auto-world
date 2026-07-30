"""Unit tests for Stage 3 embedding / retrieval / reflection."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fictional_world.application.memory.embedding_pipeline import (
    EmbeddingGatewayPort,
    EmbeddingPipelineConfig,
    fake_deterministic_vector,
    memory_from_recent_like,
    plan_embedding_jobs,
    probe_embedding_capability,
    register_active_embedding_version,
    run_embedding_batch,
)
from fictional_world.application.memory.monthly_reflection import (
    TraitChangeProposal,
    apply_forgetting_weights,
    build_monthly_chapter,
    build_reflection_run,
    validate_trait_changes,
)
from fictional_world.application.memory.retrieval import (
    RetrievalRequest,
    filter_memories_for_owner,
    retrieve_memories,
)
from fictional_world.application.models.messages import EmbeddingRequest, EmbeddingResult
from fictional_world.domain.stage3.persistence import MemoryEmbeddingPersistenceRecord


class _OkEmbedder:
    def __init__(self, dim: int = 2048) -> None:
        self.dim = dim

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        vectors = tuple(fake_deterministic_vector(t, dimension=self.dim) for t in request.texts)
        return EmbeddingResult(
            vectors=vectors,
            resolved_model="fake/embed",
            dimensions=self.dim,
            input_tokens=1,
            latency_ms=1,
        )


class _MismatchEmbedder:
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        return EmbeddingResult(
            vectors=((0.1, 0.2),),
            resolved_model="fake/embed",
            dimensions=2,
            input_tokens=1,
            latency_ms=1,
        )


class _FailOnceEmbedder:
    def __init__(self) -> None:
        self.calls = 0
        self.ok = _OkEmbedder()

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("provider outage")
        return await self.ok.embed(request)


@pytest.mark.asyncio
async def test_dimension_mismatch_rejected() -> None:
    probe = await probe_embedding_capability(_MismatchEmbedder(), config=EmbeddingPipelineConfig())
    assert probe.ok is False
    with pytest.raises(ValueError, match="dimension mismatch"):
        register_active_embedding_version(config=EmbeddingPipelineConfig(), probe=probe)


@pytest.mark.asyncio
async def test_duplicate_embedding_job_skipped() -> None:
    world_id = uuid4()
    owner = uuid4()
    mem = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="oath at the square",
        salience=Decimal("0.9"),
    )
    config = EmbeddingPipelineConfig()
    first = plan_embedding_jobs([mem], config=config)
    assert len(first) == 1
    second = plan_embedding_jobs(
        [mem],
        config=config,
        existing_idempotency_keys={first[0].idempotency_key},
    )
    assert second == ()


@pytest.mark.asyncio
async def test_partial_batch_failure_keeps_successes() -> None:
    world_id = uuid4()
    owner = uuid4()
    m1 = memory_from_recent_like(
        memory_id=uuid4(), world_id=world_id, owner_character_id=owner, content="one"
    )
    m2 = memory_from_recent_like(
        memory_id=uuid4(), world_id=world_id, owner_character_id=owner, content="two"
    )
    config = EmbeddingPipelineConfig()
    jobs = plan_embedding_jobs([m1, m2], config=config)
    # Force first job to fail by removing memory from map for first only via custom gateway
    gateway = _FailOnceEmbedder()
    result = await run_embedding_batch(gateway, memories=[m1, m2], jobs=jobs, config=config)
    assert len(result.failed_job_ids) == 1
    assert len(result.completed_job_ids) == 1
    assert len(result.embeddings) == 1


def test_secret_cannot_enter_other_owner_candidates() -> None:
    world_id = uuid4()
    mira = uuid4()
    dain = uuid4()
    secret = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=mira,
        content="Mira's secret ledger",
        visibility="private",
        salience=Decimal("1.0"),
    )
    other = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=dain,
        content="Dain saw nothing",
        visibility="private",
    )
    filtered = filter_memories_for_owner(
        [secret, other],
        world_id=world_id,
        owner_character_id=dain,
    )
    assert [m.id for m in filtered] == [other.id]
    result = retrieve_memories(
        [secret, other],
        request=RetrievalRequest(
            world_id=world_id,
            owner_character_id=dain,
            query_text="secret ledger",
            request_phase_index=20,
        ),
    )
    assert secret.id not in result.trace.candidate_memory_ids
    assert secret.id not in result.trace.selected_memory_ids


def test_no_embedding_fallback_still_ranks() -> None:
    world_id = uuid4()
    owner = uuid4()
    old = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="promised to return the ember key",
        salience=Decimal("0.95"),
        phase_index=5,
    )
    old = old.model_copy(
        update={
            "goal_relevance": Decimal("0.9"),
            "unresolved_commitment": Decimal("0.8"),
        }
    )
    recent = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="ate bread",
        salience=Decimal("0.1"),
        phase_index=100,
    )
    result = retrieve_memories(
        [old, recent],
        request=RetrievalRequest(
            world_id=world_id,
            owner_character_id=owner,
            query_text="ember key promise",
            request_phase_index=100,
        ),
    )
    assert result.used_semantic is False
    assert result.selected[0].memory.id == old.id


def test_diversity_dedupes_duplicate_content_hash() -> None:
    world_id = uuid4()
    owner = uuid4()
    a = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="same event twice",
        salience=Decimal("0.8"),
    )
    b = a.model_copy(update={"id": uuid4(), "salience": Decimal("0.7")})
    result = retrieve_memories(
        [a, b],
        request=RetrievalRequest(
            world_id=world_id,
            owner_character_id=owner,
            query_text="event",
            request_phase_index=10,
        ),
    )
    assert len(result.selected) == 1


def test_unsupported_trait_change_rejected() -> None:
    mid = uuid4()
    bad = TraitChangeProposal(
        trait_key="courage",
        value_before=Decimal("0.40"),
        value_after=Decimal("0.90"),
        evidence_memory_ids=(mid,),
    )
    validated = validate_trait_changes([bad], available_memory_ids={mid})
    assert validated.accepted == ()
    assert "delta_exceeds_maximum" in validated.rejection_reasons["courage"]


def test_reflection_requires_multiple_sources_and_preserves_identity_decay() -> None:
    world_id = uuid4()
    owner = uuid4()
    m1 = memory_from_recent_like(
        memory_id=uuid4(), world_id=world_id, owner_character_id=owner, content="stood ground"
    )
    m2 = memory_from_recent_like(
        memory_id=uuid4(), world_id=world_id, owner_character_id=owner, content="kept oath"
    )
    identity = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="I am Mira of Embervale",
        memory_type="identity",
    )
    chapter = build_monthly_chapter(
        [m1, m2, identity],
        world_id=world_id,
        owner_character_id=owner,
        month_index=1,
        start_phase_index=0,
        end_phase_index=299,
    )
    proposal = TraitChangeProposal(
        trait_key="steadfastness",
        value_before=Decimal("0.40"),
        value_after=Decimal("0.45"),
        evidence_memory_ids=(m1.id, m2.id),
    )
    run = build_reflection_run(
        world_id=world_id,
        owner_character_id=owner,
        month_index=1,
        chapter=chapter,
        proposals=[proposal],
        available_memory_ids={m1.id, m2.id, identity.id},
    )
    assert "steadfastness" in run.accepted_trait_changes
    decayed = apply_forgetting_weights([m1, identity], decay_factor=Decimal("0.5"))
    by_id = {m.id: m for m in decayed}
    assert by_id[identity.id].decay_score == identity.decay_score
    assert by_id[m1.id].decay_score < m1.decay_score


@pytest.mark.asyncio
async def test_semantic_path_with_embeddings() -> None:
    world_id = uuid4()
    owner = uuid4()
    mem = memory_from_recent_like(
        memory_id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        content="passage: the sealed ember",
        salience=Decimal("0.5"),
    )
    vec = fake_deterministic_vector(mem.content)
    emb = MemoryEmbeddingPersistenceRecord(
        id=uuid4(),
        memory_id=mem.id,
        world_id=world_id,
        owner_character_id=owner,
        embedding_model_key="nemotron-embed",
        embedding_version=1,
        dimension=2048,
        prefix_type="passage",
        embedded_content_hash=mem.content_hash,
        embedding=vec,
    )
    result = retrieve_memories(
        [mem],
        request=RetrievalRequest(
            world_id=world_id,
            owner_character_id=owner,
            query_text="ember",
            request_phase_index=10,
            query_embedding=vec,
        ),
        embeddings=[emb],
    )
    assert result.used_semantic is True
    assert result.trace.selected_memory_ids == (mem.id,)


# silence unused protocol import for type checkers using the port in annotations
_gateway_port: type[EmbeddingGatewayPort] = EmbeddingGatewayPort
