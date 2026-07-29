"""Integration tests for S0-SIM-002 atomic event commit."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.simulation.commit import (
    CommitOperationCommand,
    EventCommitError,
    EventCommitService,
    expected_character_state_key,
)
from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.common.enums import MemoryKind, ResourceKind
from fictional_world.domain.effects import (
    CreateRecentMemoryEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.world.records import AggregateVersionRecord, WorldRecord
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


async def _seed_world_and_character(
    uow: SqlAlchemyUnitOfWork,
    *,
    world_id: uuid.UUID,
    character_id: uuid.UUID,
    stamina: Decimal = Decimal("80"),
) -> uuid.UUID:
    await uow.worlds.insert(
        WorldRecord(
            id=world_id,
            slug=f"w-{world_id.hex[:8]}",
            name="Commit World",
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
    card_id = uuid.uuid4()
    uow.session.add(
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
    await uow.session.flush()
    await uow.characters.insert_state(
        CharacterStateRecord(
            character_id=character_id,
            life_status="alive",
            stamina=stamina,
            mana=Decimal("50"),
            energy=Decimal("70"),
            hunger=Decimal("20"),
            pain=Decimal("0"),
            stress=Decimal("10"),
            social_need=Decimal("40"),
            valence=Decimal("0"),
            arousal=Decimal("0"),
            dominance=Decimal("0"),
            current_card_version_id=card_id,
            version=0,
        )
    )
    await uow.aggregate_versions.upsert(
        AggregateVersionRecord(
            world_id=world_id,
            aggregate_type="character_state",
            aggregate_id=character_id,
            version=0,
        ),
        expected_version=None,
    )
    return card_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_commit_applies_effects_and_side_tables(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    service = EventCommitService()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await _seed_world_and_character(uow, world_id=world_id, character_id=character_id)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        result = await service.commit(
            uow,
            CommitOperationCommand(
                world_id=world_id,
                idempotency_key=f"commit-{uuid.uuid4()}",
                canonical_summary="Alex waits and notes the dawn.",
                observer_ids=(character_id,),
                expected_versions={expected_character_state_key(character_id): 0},
                effects=(
                    WaitEffect(
                        effect_key="wait-1",
                        justification="pause",
                        entity_id=character_id,
                    ),
                    SpendResourceEffect(
                        effect_key="spend-1",
                        justification="exertion",
                        entity_id=character_id,
                        resource=ResourceKind.STAMINA,
                        amount=5.0,
                    ),
                    CreateRecentMemoryEffect(
                        effect_key="mem-1",
                        justification="note",
                        owner_character_id=character_id,
                        memory_kind=MemoryKind.EPISODIC,
                        text="Dawn at the gate.",
                        salience=0.5,
                        confidence=0.9,
                    ),
                ),
            ),
        )
        await uow.commit()

    assert result.already_existed is False
    assert result.sequence_number == 1
    assert result.effect_count == 3
    assert result.observation_count >= 1
    assert result.memory_count == 1

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        world = await uow.worlds.get(world_id)
        assert world is not None
        assert world.current_event_sequence == 1
        state = await uow.characters.get_state(character_id)
        assert state is not None
        assert state.stamina == Decimal("75")
        assert state.version == 1
        event = await uow.events.get(result.event_id)
        assert event is not None
        assert len(event.effects) == 3
        mems = await uow.recent_memories.list_for_owner(character_id, world_id=world_id)
        assert len(mems) == 1
        found_outbox = await uow.outbox.find_by_idempotency_key(f"outbox:{event.idempotency_key}")
        assert found_outbox is not None
        assert found_outbox.world_event_id == result.event_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_duplicate_idempotency_returns_existing(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    key = f"dup-{uuid.uuid4()}"
    service = EventCommitService()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await _seed_world_and_character(uow, world_id=world_id, character_id=character_id)
        await uow.commit()

    command = CommitOperationCommand(
        world_id=world_id,
        idempotency_key=key,
        canonical_summary="idle",
        expected_versions={expected_character_state_key(character_id): 0},
        effects=(WaitEffect(effect_key="w", justification="idle", entity_id=character_id),),
        enqueue_outbox=False,
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        first = await service.commit(uow, command)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        second = await service.commit(uow, command)
        await uow.commit()

    assert first.already_existed is False
    assert second.already_existed is True
    assert first.event_id == second.event_id
    assert first.sequence_number == second.sequence_number

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        world = await uow.worlds.get(world_id)
        assert world is not None
        assert world.current_event_sequence == 1


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_validation_failure_rolls_back(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    service = EventCommitService()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await _seed_world_and_character(
            uow, world_id=world_id, character_id=character_id, stamina=Decimal("2")
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(EventCommitError) as err:
            await service.commit(
                uow,
                CommitOperationCommand(
                    world_id=world_id,
                    idempotency_key=f"bad-{uuid.uuid4()}",
                    canonical_summary="overspend",
                    expected_versions={expected_character_state_key(character_id): 0},
                    effects=(
                        SpendResourceEffect(
                            effect_key="spend",
                            justification="too much",
                            entity_id=character_id,
                            resource=ResourceKind.STAMINA,
                            amount=50.0,
                        ),
                    ),
                ),
            )
        assert err.value.validation is not None
        assert not err.value.validation.ok
        # Exception path auto-rollbacks on UoW exit

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        world = await uow.worlds.get(world_id)
        assert world is not None
        assert world.current_event_sequence == 0
        state = await uow.characters.get_state(character_id)
        assert state is not None
        assert state.stamina == Decimal("2")
        assert state.version == 0


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_optimistic_version_conflict(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id = uuid.uuid4()
    character_id = uuid.uuid4()
    service = EventCommitService()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await _seed_world_and_character(uow, world_id=world_id, character_id=character_id)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(OptimisticConcurrencyError):
            await service.commit(
                uow,
                CommitOperationCommand(
                    world_id=world_id,
                    idempotency_key=f"conflict-{uuid.uuid4()}",
                    canonical_summary="stale",
                    expected_versions={expected_character_state_key(character_id): 99},
                    effects=(
                        WaitEffect(
                            effect_key="w",
                            justification="idle",
                            entity_id=character_id,
                        ),
                    ),
                ),
            )
