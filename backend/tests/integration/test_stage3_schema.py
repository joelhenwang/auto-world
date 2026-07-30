"""Integration tests: Stage 3 long-term schema constraints (S3-DB-001)."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.seed.records import LocationRecord
from fictional_world.domain.stage3.persistence import (
    ArcPersistenceRecord,
    EmbeddingJobPersistenceRecord,
    EmbeddingModelVersionPersistenceRecord,
    EvaluatorRunPersistenceRecord,
    FactionPersistenceRecord,
    InjuryPersistenceRecord,
    MemoryEmbeddingPersistenceRecord,
    MemoryPersistenceRecord,
    MonthRunPersistenceRecord,
    QualityFindingPersistenceRecord,
    StatStatePersistenceRecord,
)
from fictional_world.domain.world.records import WorldRecord
from fictional_world.infrastructure.database.models import CharacterCardVersionRow
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"

STAGE3_TABLES = {
    "memory",
    "memory_source",
    "embedding_model_version",
    "memory_embedding",
    "embedding_job",
    "retrieval_trace",
    "monthly_chapter",
    "reflection_run",
    "character_trait_version",
    "stat_state",
    "stat_potential",
    "skill_definition",
    "skill_state",
    "skill_progress_evidence",
    "spell_definition",
    "known_spell",
    "magic_affinity",
    "item",
    "inventory_entry",
    "equipment_state",
    "condition",
    "injury",
    "recovery_plan",
    "faction",
    "faction_membership",
    "faction_relation",
    "faction_state",
    "settlement_indicator",
    "arc",
    "trope_usage",
    "novelty_signature",
    "evaluator_run",
    "quality_finding",
    "export_run",
    "month_run",
}


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _alembic(url: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**dict(__import__("os").environ), "ALEMBIC_DATABASE_URL": url}
    return subprocess.run(
        ["uv", "run", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.fixture
async def migrated_engine(postgres_container: dict[str, str]) -> AsyncEngine:
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    yield engine
    await engine.dispose()


@pytest.fixture
async def uow_factory(migrated_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(migrated_engine, expire_on_commit=False, class_=AsyncSession)


async def _seed_world_char(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    world_id = uuid.uuid4()
    mira_id = uuid.uuid4()
    loc_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(factory) as uow:
        assert uow.session is not None
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"s3-{world_id.hex[:8]}",
                name="Stage3",
                status="active",
                language="en",
                content_rating="young_adult_soft_dark",
                current_event_sequence=0,
                version=0,
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=loc_id,
                world_id=world_id,
                entity_type="location",
                canonical_name="Square",
                normalized_name="square",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_location(
            LocationRecord(
                entity_id=loc_id,
                location_type="plaza",
                region_code="embervale",
                capacity=40,
                environment_tags=("square",),
                canonical_description="Town square",
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=mira_id,
                world_id=world_id,
                entity_type="character",
                canonical_name="Mira",
                normalized_name="mira",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_character(
            CharacterRecord(entity_id=mira_id, character_kind="focus", species_code="human")
        )
        card_id = uuid.uuid4()
        uow.session.add(
            CharacterCardVersionRow(
                id=card_id,
                character_id=mira_id,
                version_number=1,
                identity={},
                backstory="",
                appearance={},
                personality_traits={},
                values={},
                fears={},
                desires={},
                boundaries={},
                voice_profile={},
                initial_capabilities={},
                secret_manifest={},
                change_summary="v1",
                content_hash=hashlib.sha256(f"{mira_id}-v1".encode()).hexdigest(),
            )
        )
        await uow.session.flush()
        await uow.characters.set_character_card(mira_id, card_version_id=card_id)
        await uow.characters.insert_state(
            CharacterStateRecord(
                character_id=mira_id,
                location_id=loc_id,
                life_status="alive",
                stamina=Decimal("80"),
                mana=Decimal("50"),
                energy=Decimal("70"),
                hunger=Decimal("20"),
                pain=Decimal("0"),
                stress=Decimal("10"),
                social_need=Decimal("40"),
                valence=Decimal("0.1"),
                arousal=Decimal("0.2"),
                dominance=Decimal("0.0"),
                current_card_version_id=card_id,
                version=0,
            )
        )
        await uow.commit()
    return world_id, mira_id, loc_id


@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage3_tables_exist_and_roundtrip(postgres_container: dict[str, str]) -> None:
    url = _normalize_url(postgres_container["url"])
    heads = _alembic(url, "heads").stdout.strip().splitlines()
    assert len(heads) == 1
    assert "0007_stage4_img" in heads[0]
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'worldsim'")
        )
        names = {row[0] for row in rows.fetchall()}
        assert STAGE3_TABLES.issubset(names)
    await engine.dispose()
    _alembic(url, "downgrade", "-1")
    _alembic(url, "upgrade", "head")


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_memory_owner_visibility_and_embedding_vector(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, _loc_id = await _seed_world_char(uow_factory)
    memory_id = uuid.uuid4()
    content = "Mira remembers the ember oath"
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        mem = await uow.long_term_memories.insert(
            MemoryPersistenceRecord(
                id=memory_id,
                world_id=world_id,
                owner_character_id=mira_id,
                memory_type="episodic",
                content=content,
                salience=Decimal("0.9000"),
                confidence=Decimal("0.8000"),
                emotional_weight=Decimal("0.7000"),
                visibility="private",
                occurred_phase_index=10,
                created_phase_index=10,
                decay_score=Decimal("1.0000"),
                content_hash=content_hash,
            )
        )
        assert mem.visibility == "private"
        listed = await uow.long_term_memories.list_for_owner(
            world_id, mira_id, visibility="private"
        )
        assert len(listed) == 1
        await uow.embedding_model_versions.insert(
            EmbeddingModelVersionPersistenceRecord(
                id=uuid.uuid4(),
                model_key="nemotron-embed",
                provider="openrouter",
                model_slug="nvidia/nemotron-3-embed-1b:free",
                dimension=2048,
                query_prefix="query: ",
                passage_prefix="passage: ",
                embedding_version=1,
                is_active=True,
            )
        )
        vector = tuple(0.0 for _ in range(2048))
        emb = await uow.memory_embeddings.insert(
            MemoryEmbeddingPersistenceRecord(
                id=uuid.uuid4(),
                memory_id=memory_id,
                world_id=world_id,
                owner_character_id=mira_id,
                embedding_model_key="nemotron-embed",
                embedding_version=1,
                dimension=2048,
                prefix_type="passage",
                embedded_content_hash=content_hash,
                embedding=vector,
            )
        )
        assert emb.dimension == 2048
        assert len(emb.embedding) == 2048
        await uow.embedding_jobs.insert(
            EmbeddingJobPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                memory_id=memory_id,
                embedding_model_key="nemotron-embed",
                embedding_version=1,
                idempotency_key=f"embed:{memory_id}:v1",
            )
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(IntegrityError):
            await uow.long_term_memories.insert(
                MemoryPersistenceRecord(
                    id=uuid.uuid4(),
                    world_id=world_id,
                    owner_character_id=mira_id,
                    memory_type="episodic",
                    content=content,
                    salience=Decimal("0.5000"),
                    confidence=Decimal("0.5000"),
                    emotional_weight=Decimal("0.5000"),
                    visibility="private",
                    occurred_phase_index=11,
                    created_phase_index=11,
                    decay_score=Decimal("1.0000"),
                    content_hash=content_hash,
                )
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stats_arcs_factions_evaluator_constraints(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, _loc_id = await _seed_world_char(uow_factory)
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.stat_states.upsert(
            StatStatePersistenceRecord(
                character_id=mira_id,
                world_id=world_id,
                stat_code="will",
                current_value=Decimal("42.0000"),
                dynamic_potential_cap=Decimal("80.0000"),
                growth_rate=Decimal("0.2000"),
                adaptability=Decimal("0.5000"),
            )
        )
        await uow.injuries.insert(
            InjuryPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                character_id=mira_id,
                body_region="left_arm",
                injury_type="bruise",
                severity=Decimal("0.3000"),
            )
        )
        await uow.factions.insert(
            FactionPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                faction_key="ashen-circle",
                name="Ashen Circle",
                faction_type="guild",
            )
        )
        await uow.arcs.insert(
            ArcPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                arc_key="ember-mystery",
                title="Ember Mystery",
                arc_scope="major",
                status="active",
                premise="A sealed ember stirs",
                objective="Learn the truth without burning the town",
            )
        )
        run = await uow.evaluator_runs.insert(
            EvaluatorRunPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                scope="scene",
                idempotency_key=f"eval:{world_id.hex[:8]}:1",
            )
        )
        await uow.evaluator_runs.insert_finding(
            QualityFindingPersistenceRecord(
                id=uuid.uuid4(),
                evaluator_run_id=run.id,
                world_id=world_id,
                finding_code="repetition_soft",
                message="Mild location reuse",
                can_mutate_canon=False,
            )
        )
        await uow.month_runs.insert(
            MonthRunPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                month_index=1,
                start_day_index=0,
                end_day_index=29,
                idempotency_key=f"month:{world_id}:1",
            )
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(IntegrityError):
            await uow.arcs.insert(
                ArcPersistenceRecord(
                    id=uuid.uuid4(),
                    world_id=world_id,
                    arc_key="second-major",
                    title="Second Major",
                    arc_scope="major",
                    status="active",
                    premise="another",
                    objective="conflict",
                )
            )
            await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(IntegrityError):
            await uow.evaluator_runs.insert_finding(
                QualityFindingPersistenceRecord(
                    id=uuid.uuid4(),
                    evaluator_run_id=run.id,
                    world_id=world_id,
                    finding_code="bad",
                    message="must not mutate",
                    can_mutate_canon=True,
                )
            )
            await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(IntegrityError):
            await uow.stat_states.upsert(
                StatStatePersistenceRecord(
                    character_id=mira_id,
                    world_id=world_id,
                    stat_code="overflow",
                    current_value=Decimal("101.0000"),
                    dynamic_potential_cap=Decimal("100.0000"),
                    growth_rate=Decimal("0.1000"),
                    adaptability=Decimal("0.1000"),
                )
            )
            await uow.commit()
