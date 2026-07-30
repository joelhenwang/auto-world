"""Stage 3 embedding pipeline and version registry (S3-MEM-001)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from fictional_world.application.models.messages import EmbeddingRequest, EmbeddingResult
from fictional_world.domain.stage3.persistence import (
    EmbeddingJobPersistenceRecord,
    EmbeddingModelVersionPersistenceRecord,
    MemoryEmbeddingPersistenceRecord,
    MemoryPersistenceRecord,
)

DEFAULT_MODEL_KEY = "nemotron-embed"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL_SLUG = "nvidia/nemotron-3-embed-1b:free"
DEFAULT_DIMENSION = 2048
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "


class EmbeddingGatewayPort(Protocol):
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...


@dataclass(frozen=True, slots=True)
class EmbeddingPipelineConfig:
    model_key: str = DEFAULT_MODEL_KEY
    provider: str = DEFAULT_PROVIDER
    model_slug: str = DEFAULT_MODEL_SLUG
    dimension: int = DEFAULT_DIMENSION
    query_prefix: str = QUERY_PREFIX
    passage_prefix: str = PASSAGE_PREFIX
    embedding_version: int = 1


@dataclass(frozen=True, slots=True)
class CapabilityProbeResult:
    ok: bool
    observed_dimension: int | None
    error: str | None = None


def embedding_job_idempotency_key(
    memory_id: UUID,
    *,
    model_key: str,
    embedding_version: int,
    content_hash: str,
) -> str:
    return f"embed:{memory_id}:{model_key}:v{embedding_version}:{content_hash}"


def prefixed_text(text: str, *, prefix_type: str, config: EmbeddingPipelineConfig) -> str:
    if prefix_type == "query":
        return f"{config.query_prefix}{text}"
    if prefix_type == "passage":
        return f"{config.passage_prefix}{text}"
    msg = f"unsupported prefix_type: {prefix_type}"
    raise ValueError(msg)


async def probe_embedding_capability(
    gateway: EmbeddingGatewayPort,
    *,
    config: EmbeddingPipelineConfig,
    request_id: str | None = None,
) -> CapabilityProbeResult:
    """Probe provider dimension; reject mismatch against configured baseline."""

    try:
        result = await gateway.embed(
            EmbeddingRequest(
                request_id=request_id or f"embed-probe:{uuid4()}",
                model_profile_id=config.model_key,
                texts=(prefixed_text("capability probe", prefix_type="passage", config=config),),
                input_type="passage",
                dimensions=config.dimension,
                metadata={"purpose": "capability_probe"},
            )
        )
    except Exception as exc:
        return CapabilityProbeResult(ok=False, observed_dimension=None, error=str(exc))
    if result.dimensions != config.dimension:
        return CapabilityProbeResult(
            ok=False,
            observed_dimension=result.dimensions,
            error=(
                f"dimension mismatch: observed {result.dimensions} != configured {config.dimension}"
            ),
        )
    if len(result.vectors) != 1 or len(result.vectors[0]) != config.dimension:
        return CapabilityProbeResult(
            ok=False,
            observed_dimension=len(result.vectors[0]) if result.vectors else None,
            error="vector length mismatch",
        )
    return CapabilityProbeResult(ok=True, observed_dimension=result.dimensions)


def register_active_embedding_version(
    *,
    config: EmbeddingPipelineConfig,
    probe: CapabilityProbeResult,
    version_id: UUID | None = None,
) -> EmbeddingModelVersionPersistenceRecord:
    if not probe.ok:
        msg = probe.error or "capability probe failed"
        raise ValueError(msg)
    return EmbeddingModelVersionPersistenceRecord(
        id=version_id or uuid4(),
        model_key=config.model_key,
        provider=config.provider,
        model_slug=config.model_slug,
        dimension=config.dimension,
        query_prefix=config.query_prefix,
        passage_prefix=config.passage_prefix,
        embedding_version=config.embedding_version,
        is_active=True,
        capability_probe={
            "ok": True,
            "observed_dimension": probe.observed_dimension,
        },
    )


def plan_embedding_jobs(
    memories: Sequence[MemoryPersistenceRecord],
    *,
    config: EmbeddingPipelineConfig,
    existing_idempotency_keys: set[str] | None = None,
) -> tuple[EmbeddingJobPersistenceRecord, ...]:
    """Create pending jobs; skip duplicates by idempotency key."""

    known = existing_idempotency_keys or set()
    jobs: list[EmbeddingJobPersistenceRecord] = []
    for memory in memories:
        key = embedding_job_idempotency_key(
            memory.id,
            model_key=config.model_key,
            embedding_version=config.embedding_version,
            content_hash=memory.content_hash,
        )
        if key in known:
            continue
        known.add(key)
        jobs.append(
            EmbeddingJobPersistenceRecord(
                id=uuid4(),
                world_id=memory.world_id,
                memory_id=memory.id,
                embedding_model_key=config.model_key,
                embedding_version=config.embedding_version,
                status="pending",
                idempotency_key=key,
            )
        )
    return tuple(jobs)


@dataclass(frozen=True, slots=True)
class EmbeddingBatchResult:
    embeddings: tuple[MemoryEmbeddingPersistenceRecord, ...]
    completed_job_ids: tuple[UUID, ...]
    failed_job_ids: tuple[UUID, ...]
    errors: tuple[str, ...]


async def run_embedding_batch(
    gateway: EmbeddingGatewayPort,
    *,
    memories: Sequence[MemoryPersistenceRecord],
    jobs: Sequence[EmbeddingJobPersistenceRecord],
    config: EmbeddingPipelineConfig,
    request_id: str | None = None,
) -> EmbeddingBatchResult:
    """Embed a batch; partial failure leaves successful rows usable."""

    by_id = {m.id: m for m in memories}
    embeddings: list[MemoryEmbeddingPersistenceRecord] = []
    completed: list[UUID] = []
    failed: list[UUID] = []
    errors: list[str] = []

    for job in jobs:
        memory = by_id.get(job.memory_id)
        if memory is None:
            failed.append(job.id)
            errors.append(f"missing memory {job.memory_id}")
            continue
        try:
            result = await gateway.embed(
                EmbeddingRequest(
                    request_id=request_id or f"embed-job:{job.id}",
                    model_profile_id=config.model_key,
                    texts=(prefixed_text(memory.content, prefix_type="passage", config=config),),
                    input_type="passage",
                    dimensions=config.dimension,
                    metadata={"job_id": str(job.id)},
                )
            )
            if result.dimensions != config.dimension:
                raise ValueError(f"dimension mismatch: {result.dimensions} != {config.dimension}")
            vector = result.vectors[0]
            if len(vector) != config.dimension:
                raise ValueError("vector length mismatch")
            embeddings.append(
                MemoryEmbeddingPersistenceRecord(
                    id=uuid4(),
                    memory_id=memory.id,
                    world_id=memory.world_id,
                    owner_character_id=memory.owner_character_id,
                    embedding_model_key=config.model_key,
                    embedding_version=config.embedding_version,
                    dimension=config.dimension,
                    prefix_type="passage",
                    embedded_content_hash=memory.content_hash,
                    embedding=vector,
                    is_active=True,
                )
            )
            completed.append(job.id)
        except Exception as exc:
            failed.append(job.id)
            errors.append(f"{job.id}: {exc}")

    return EmbeddingBatchResult(
        embeddings=tuple(embeddings),
        completed_job_ids=tuple(completed),
        failed_job_ids=tuple(failed),
        errors=tuple(errors),
    )


def content_hash_for_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def zero_vector(dimension: int = DEFAULT_DIMENSION) -> tuple[float, ...]:
    return tuple(0.0 for _ in range(dimension))


def fake_deterministic_vector(
    text: str, *, dimension: int = DEFAULT_DIMENSION
) -> tuple[float, ...]:
    """Deterministic non-zero vector for offline tests (not a real embedding)."""

    digest = hashlib.sha256(text.encode()).digest()
    values: list[float] = []
    i = 0
    while len(values) < dimension:
        b = digest[i % len(digest)]
        values.append((b / 255.0) * 2.0 - 1.0)
        i += 1
        if i % len(digest) == 0:
            digest = hashlib.sha256(digest + text.encode()).digest()
    # L2 normalize lightly
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return tuple(v / norm for v in values)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(dot / (na * nb))


def memory_from_recent_like(
    *,
    memory_id: UUID,
    world_id: UUID,
    owner_character_id: UUID,
    content: str,
    salience: Decimal = Decimal("0.5"),
    visibility: str = "private",
    phase_index: int = 0,
    memory_type: str = "episodic",
) -> MemoryPersistenceRecord:
    return MemoryPersistenceRecord(
        id=memory_id,
        world_id=world_id,
        owner_character_id=owner_character_id,
        memory_type=memory_type,
        content=content,
        salience=salience,
        confidence=Decimal("0.8"),
        emotional_weight=Decimal("0.3"),
        visibility=visibility,
        occurred_phase_index=phase_index,
        created_phase_index=phase_index,
        decay_score=Decimal("1.0"),
        content_hash=content_hash_for_text(content),
    )
