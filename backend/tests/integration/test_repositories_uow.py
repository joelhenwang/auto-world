"""Integration tests for S0-DB-003 repositories and unit of work."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.events.persistence import (
    EventEffectRecord,
    OutboxMessageRecord,
    WorldEventRecord,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.phases.records import PhaseRunRecord
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)
from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError
from fictional_world.infrastructure.database.models import CharacterCardVersionRow
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _alembic(url: str, *args: str) -> None:
    env = {**dict(__import__("os").environ), "ALEMBIC_DATABASE_URL": url}
    subprocess.run(
        ["uv", "run", "alembic", "-c", str(ALEMBIC_INI), *args],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    )


@pytest.fixture
async def uow_factory(
    postgres_container: dict[str, str],
) -> async_sessionmaker[AsyncSession]:
    url = _normalize_url(postgres_container["url"])
    _alembic(url, "upgrade", "head")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


async def _seed_character_card(
    session: AsyncSession,
    *,
    character_id: uuid.UUID,
) -> uuid.UUID:
    card_id = uuid.uuid4()
    session.add(
        CharacterCardVersionRow(
            id=card_id,
            character_id=character_id,
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
            content_hash=hashlib.sha256(f"{character_id}-v1".encode()).hexdigest(),
        )
    )
    await session.flush()
    return card_id


def _base_state(character_id: uuid.UUID, card_id: uuid.UUID) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=character_id,
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


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_world_crud_clock_and_event_sequence(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        world = await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"w-{world_id.hex[:8]}",
                name="Test World",
                status="archived",
            )
        )
        assert world.current_event_sequence == 0
        clock = await uow.worlds.upsert_clock(
            WorldClockRecord(
                world_id=world_id,
                generation_number=1,
                year=312,
                month=3,
                day=14,
                phase_name="dawn",
                phase_ordinal=0,
                absolute_day_index=0,
                absolute_phase_index=0,
                resolution_mode="detailed",
                version=0,
            ),
            expected_version=None,
        )
        assert clock.phase_name == "dawn"
        locked = await uow.worlds.lock_for_event_sequence(world_id)
        advanced = await uow.worlds.advance_event_sequence(
            world_id, next_sequence=1, expected_version=locked.version
        )
        assert advanced.current_event_sequence == 1
        assert advanced.version == locked.version + 1
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        loaded = await uow.worlds.get(world_id)
        assert loaded is not None
        assert loaded.current_event_sequence == 1
        by_slug = await uow.worlds.get_by_slug(loaded.slug)
        assert by_slug is not None
        assert by_slug.id == world_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rollback_discards_phase_insert(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    phase_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"rb-{world_id.hex[:8]}",
                name="Rollback",
                status="archived",
            )
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.phases.insert(
            PhaseRunRecord(
                id=phase_id,
                world_id=world_id,
                absolute_phase_index=0,
                phase_name="dawn",
                resolution_mode="detailed",
                state="running",
                expected_character_count=1,
                idempotency_key=f"phase-{phase_id}",
            )
        )
        await uow.rollback()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        assert await uow.phases.get(phase_id) is None
        assert await uow.phases.find_by_idempotency_key(f"phase-{phase_id}") is None


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_character_state_optimistic_concurrency(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"ch-{world_id.hex[:8]}",
                name="Chars",
                status="archived",
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=character_id,
                world_id=world_id,
                entity_type="character",
                canonical_name="Alex",
                normalized_name="alex",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_character(
            CharacterRecord(
                entity_id=character_id,
                character_kind="focus",
                species_code="human",
            )
        )
        assert uow.session is not None
        card_id = await _seed_character_card(uow.session, character_id=character_id)
        state = await uow.characters.insert_state(_base_state(character_id, card_id))
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        current = await uow.characters.get_state_for_update(character_id)
        updated = await uow.characters.save_state(
            current.model_copy(update={"stamina": Decimal("75")}),
            expected_version=current.version,
        )
        assert updated.version == state.version + 1
        assert updated.stamina == Decimal("75")
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(OptimisticConcurrencyError):
            await uow.characters.save_state(
                _base_state(character_id, card_id).model_copy(update={"stamina": Decimal("10")}),
                expected_version=0,
            )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_event_observation_memory_outbox_and_versions(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    event_id = uuid.uuid4()
    effect_id = uuid.uuid4()
    obs_id = uuid.uuid4()
    mem_id = uuid.uuid4()
    outbox_id = uuid.uuid4()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"ev-{world_id.hex[:8]}",
                name="Events",
                status="archived",
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=character_id,
                world_id=world_id,
                entity_type="character",
                canonical_name="Sein",
                normalized_name="sein",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_character(
            CharacterRecord(
                entity_id=character_id,
                character_kind="focus",
                species_code="human",
            )
        )
        assert uow.session is not None
        card_id = await _seed_character_card(uow.session, character_id=character_id)
        await uow.characters.insert_state(_base_state(character_id, card_id))
        await uow.aggregate_versions.upsert(
            AggregateVersionRecord(
                world_id=world_id,
                aggregate_type="character_state",
                aggregate_id=character_id,
                version=0,
            ),
            expected_version=None,
        )
        event = await uow.events.insert(
            WorldEventRecord(
                id=event_id,
                world_id=world_id,
                sequence_number=1,
                absolute_phase_index=0,
                event_type="WORLD_TICK",
                canonical_summary="dawn breaks",
                structured_facts={"sky": "pale"},
                importance=Decimal("0.2"),
                visibility_class="public",
                source_kind="engine",
                idempotency_key=f"evt-{event_id}",
                consistency_status="consistent",
                effects=(
                    EventEffectRecord(
                        id=effect_id,
                        world_event_id=event_id,
                        effect_index=0,
                        effect_type="wait",
                        effect_payload={"duration": 1},
                        previous_state={},
                        resulting_state={},
                        validation_manifest={"ok": True},
                    ),
                ),
            )
        )
        assert len(event.effects) == 1
        await uow.observations.insert_many(
            [
                ObservationPersistenceRecord(
                    id=obs_id,
                    world_event_id=event_id,
                    observer_id=character_id,
                    observation_type="perceive_event",
                    perceived_summary="The sky lightens.",
                    perceived_facts={"sky": "pale"},
                    confidence=Decimal("0.9"),
                    visibility_reason="co-located",
                    source_sense_tags=("sight",),
                    content_hash=hashlib.sha256(b"obs1").hexdigest(),
                )
            ]
        )
        await uow.recent_memories.insert(
            RecentMemoryRecord(
                id=mem_id,
                world_id=world_id,
                owner_character_id=character_id,
                memory_type="episodic",
                content="Saw dawn at the gate.",
                salience=Decimal("0.6"),
                confidence=Decimal("0.9"),
                emotional_weight=Decimal("0.2"),
                visibility="private",
                occurred_phase_index=0,
                created_phase_index=0,
                decay_score=Decimal("1.0"),
                status="active",
                content_hash=hashlib.sha256(b"mem1").hexdigest(),
                source_event_id=event_id,
                source_observation_id=obs_id,
            )
        )
        await uow.outbox.insert(
            OutboxMessageRecord(
                id=outbox_id,
                world_event_id=event_id,
                message_type="image.enqueue",
                payload={"event_id": str(event_id)},
                idempotency_key=f"outbox-{outbox_id}",
                state="pending",
            )
        )
        await uow.aggregate_versions.verify(world_id, {f"character_state:{character_id}": 0})
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        found = await uow.events.find_by_idempotency_key(f"evt-{event_id}")
        assert found is not None
        assert found.id == event_id
        assert len(found.effects) == 1
        obs = await uow.observations.list_for_observer(character_id)
        assert len(obs) == 1
        mems = await uow.recent_memories.list_for_owner(character_id, world_id=world_id)
        assert len(mems) == 1
        assert mems[0].owner_character_id == character_id
        outbox = await uow.outbox.find_by_idempotency_key(f"outbox-{outbox_id}")
        assert outbox is not None
        with pytest.raises(OptimisticConcurrencyError):
            await uow.aggregate_versions.verify(world_id, {f"character_state:{character_id}": 99})
