"""Stage 3 repository ports (memory / rules / world / quality stubs)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from fictional_world.domain.stage3.persistence import (
    ArcPersistenceRecord,
    EmbeddingJobPersistenceRecord,
    EmbeddingModelVersionPersistenceRecord,
    EvaluatorRunPersistenceRecord,
    FactionPersistenceRecord,
    InjuryPersistenceRecord,
    MemoryEmbeddingPersistenceRecord,
    MemoryPersistenceRecord,
    MemorySourcePersistenceRecord,
    MonthRunPersistenceRecord,
    QualityFindingPersistenceRecord,
    StatStatePersistenceRecord,
)


class LongTermMemoryRepository(Protocol):
    async def get(self, memory_id: UUID) -> MemoryPersistenceRecord | None: ...

    async def insert(self, memory: MemoryPersistenceRecord) -> MemoryPersistenceRecord: ...

    async def insert_source(
        self, source: MemorySourcePersistenceRecord
    ) -> MemorySourcePersistenceRecord: ...

    async def list_for_owner(
        self,
        world_id: UUID,
        owner_character_id: UUID,
        *,
        visibility: str | None = None,
        status: str = "active",
    ) -> Sequence[MemoryPersistenceRecord]: ...


class MemoryEmbeddingRepository(Protocol):
    async def get(self, embedding_id: UUID) -> MemoryEmbeddingPersistenceRecord | None: ...

    async def insert(
        self, embedding: MemoryEmbeddingPersistenceRecord
    ) -> MemoryEmbeddingPersistenceRecord: ...


class EmbeddingModelVersionRepository(Protocol):
    async def get_active(self, model_key: str) -> EmbeddingModelVersionPersistenceRecord | None: ...

    async def insert(
        self, version: EmbeddingModelVersionPersistenceRecord
    ) -> EmbeddingModelVersionPersistenceRecord: ...


class EmbeddingJobRepository(Protocol):
    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> EmbeddingJobPersistenceRecord | None: ...

    async def insert(self, job: EmbeddingJobPersistenceRecord) -> EmbeddingJobPersistenceRecord: ...


class StatStateRepository(Protocol):
    async def get(
        self, character_id: UUID, stat_code: str
    ) -> StatStatePersistenceRecord | None: ...

    async def upsert(self, state: StatStatePersistenceRecord) -> StatStatePersistenceRecord: ...


class InjuryRepository(Protocol):
    async def get(self, injury_id: UUID) -> InjuryPersistenceRecord | None: ...

    async def insert(self, injury: InjuryPersistenceRecord) -> InjuryPersistenceRecord: ...


class FactionRepository(Protocol):
    async def get(self, faction_id: UUID) -> FactionPersistenceRecord | None: ...

    async def get_by_key(
        self, world_id: UUID, faction_key: str
    ) -> FactionPersistenceRecord | None: ...

    async def insert(self, faction: FactionPersistenceRecord) -> FactionPersistenceRecord: ...


class ArcRepository(Protocol):
    async def get(self, arc_id: UUID) -> ArcPersistenceRecord | None: ...

    async def get_by_key(self, world_id: UUID, arc_key: str) -> ArcPersistenceRecord | None: ...

    async def insert(self, arc: ArcPersistenceRecord) -> ArcPersistenceRecord: ...


class EvaluatorRunRepository(Protocol):
    async def get(self, run_id: UUID) -> EvaluatorRunPersistenceRecord | None: ...

    async def insert(self, run: EvaluatorRunPersistenceRecord) -> EvaluatorRunPersistenceRecord: ...

    async def insert_finding(
        self, finding: QualityFindingPersistenceRecord
    ) -> QualityFindingPersistenceRecord: ...


class MonthRunRepository(Protocol):
    async def get(self, month_run_id: UUID) -> MonthRunPersistenceRecord | None: ...

    async def get_by_world_month(
        self, world_id: UUID, month_index: int
    ) -> MonthRunPersistenceRecord | None: ...

    async def insert(self, month_run: MonthRunPersistenceRecord) -> MonthRunPersistenceRecord: ...
