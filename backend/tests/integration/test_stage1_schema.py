"""Integration tests: Stage 1 action/scene schema constraints (S1-DB-001)."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from datetime import UTC, datetime
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
from fictional_world.domain.phases.records import PhaseRunRecord, PhaseSnapshotRecord
from fictional_world.domain.scenes.persistence import (
    ActionProposalRecord,
    SceneParticipantRecord,
    SceneRecord,
    SceneResolutionRecord,
)
from fictional_world.domain.seed.records import LocationRecord
from fictional_world.domain.world.records import WorldRecord
from fictional_world.infrastructure.database.models import CharacterCardVersionRow
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"

STAGE1_TABLES = {
    "action_proposal",
    "action_target",
    "narration",
    "player_control_session",
    "reaction_proposal",
    "scene",
    "scene_action",
    "scene_participant",
    "scene_resolution",
    "scene_run",
    "stream_event",
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


async def _seed_world_phase_snapshot(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    """Return world_id, phase_run_id, snapshot_id, mira_id, location_id."""
    world_id = uuid.uuid4()
    mira_id = uuid.uuid4()
    location_id = uuid.uuid4()
    phase_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(factory) as uow:
        assert uow.session is not None
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"s1-{world_id.hex[:8]}",
                name="Stage1",
                status="active",
                language="en",
                content_rating="young_adult_soft_dark",
                current_event_sequence=0,
                version=0,
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=location_id,
                world_id=world_id,
                entity_type="location",
                canonical_name="Inn",
                normalized_name="inn",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_location(
            LocationRecord(
                entity_id=location_id,
                location_type="building",
                region_code="embervale",
                capacity=40,
                environment_tags=("inn",),
                canonical_description="Inn",
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
            CharacterRecord(
                entity_id=mira_id,
                character_kind="focus",
                species_code="human",
            )
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
                location_id=location_id,
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
        await uow.phases.insert(
            PhaseRunRecord(
                id=phase_id,
                world_id=world_id,
                absolute_phase_index=0,
                phase_name="dawn",
                resolution_mode="detailed",
                state="generating_intents",
                expected_character_count=1,
                idempotency_key=f"phase:{phase_id}",
            )
        )
        await uow.snapshots.insert(
            PhaseSnapshotRecord(
                id=snapshot_id,
                phase_run_id=phase_id,
                world_id=world_id,
                source_event_sequence=0,
                world_clock_version=0,
                state_manifest={},
                state_hash=hashlib.sha256(b"snap").hexdigest(),
                sealed_at=datetime.now(UTC),
                characters=(),
            )
        )
        await uow.commit()
    return world_id, phase_id, snapshot_id, mira_id, location_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage1_tables_exist(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as conn:
        rows = await conn.execute(
            text(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'worldsim'
                """
            )
        )
        names = {r[0] for r in rows.fetchall()}
    assert names >= STAGE1_TABLES


@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage1_migration_roundtrip(postgres_container: dict[str, str]) -> None:
    url = _normalize_url(postgres_container["url"])
    heads = _alembic(url, "heads").stdout.strip().splitlines()
    assert len(heads) == 1
    assert "0004_stage2_continuity_tables" in heads[0]
    _alembic(url, "upgrade", "head")
    _alembic(url, "downgrade", "-1")
    _alembic(url, "upgrade", "head")


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_primary_action(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    _world_id, phase_id, snapshot_id, mira_id, _loc = await _seed_world_phase_snapshot(uow_factory)
    proposal = ActionProposalRecord(
        id=uuid.uuid4(),
        phase_run_id=phase_id,
        snapshot_id=snapshot_id,
        actor_id=mira_id,
        action_family="wait",
        intent="Wait by the hearth",
        visibility="observable",
        idempotency_key=f"action:{uuid.uuid4()}",
        fallback_action={"action_family": "wait", "description": "keep waiting"},
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.action_proposals.insert(proposal)
        await uow.commit()

    dup = ActionProposalRecord(
        id=uuid.uuid4(),
        phase_run_id=phase_id,
        snapshot_id=snapshot_id,
        actor_id=mira_id,
        action_family="observe",
        intent="Look around",
        visibility="observable",
        idempotency_key=f"action:{uuid.uuid4()}",
        fallback_action={"action_family": "wait", "description": "wait"},
    )
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.action_proposals.insert(dup)
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_scene_participant(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    _world_id, phase_id, snapshot_id, mira_id, location_id = await _seed_world_phase_snapshot(
        uow_factory
    )
    scene_id = uuid.uuid4()
    proposal_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.action_proposals.insert(
            ActionProposalRecord(
                id=proposal_id,
                phase_run_id=phase_id,
                snapshot_id=snapshot_id,
                actor_id=mira_id,
                action_family="wait",
                intent="Wait",
                visibility="observable",
                idempotency_key=f"action:{proposal_id}",
                fallback_action={"action_family": "wait", "description": "wait"},
            )
        )
        await uow.scenes.insert(
            SceneRecord(
                id=scene_id,
                phase_run_id=phase_id,
                snapshot_id=snapshot_id,
                location_id=location_id,
                scene_type="solo",
                state="drafted",
                beat_budget=3,
                idempotency_key=f"scene:{scene_id}",
                participants=(
                    SceneParticipantRecord(
                        scene_id=scene_id,
                        entity_id=mira_id,
                        participant_role="actor",
                    ),
                ),
            )
        )
        await uow.commit()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        assert uow.session is not None
        with pytest.raises(IntegrityError):
            await uow.session.execute(
                text(
                    """
                    INSERT INTO worldsim.scene_participant
                      (scene_id, entity_id, participant_role, reaction_eligible, joined_at_beat)
                    VALUES
                      (:scene_id, :entity_id, 'observer', true, 0)
                    """
                ),
                {"scene_id": scene_id, "entity_id": mira_id},
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_resolution_idempotency(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    _world_id, phase_id, snapshot_id, mira_id, location_id = await _seed_world_phase_snapshot(
        uow_factory
    )
    scene_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.scenes.insert(
            SceneRecord(
                id=scene_id,
                phase_run_id=phase_id,
                snapshot_id=snapshot_id,
                location_id=location_id,
                scene_type="solo",
                state="drafted",
                beat_budget=2,
                idempotency_key=f"scene:{scene_id}",
                participants=(
                    SceneParticipantRecord(
                        scene_id=scene_id,
                        entity_id=mira_id,
                        participant_role="actor",
                    ),
                ),
            )
        )
        await uow.scene_resolutions.insert(
            SceneResolutionRecord(
                id=uuid.uuid4(),
                scene_id=scene_id,
                resolution_level="success",
                canonical_summary="Mira waits.",
                confidence=Decimal("0.9"),
                visual_significance=Decimal("0.1"),
                idempotency_key="resolution:once",
            )
        )
        await uow.commit()

    scene2 = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.scenes.insert(
            SceneRecord(
                id=scene2,
                phase_run_id=phase_id,
                snapshot_id=snapshot_id,
                location_id=location_id,
                scene_type="solo",
                state="drafted",
                beat_budget=2,
                idempotency_key=f"scene:{scene2}",
                participants=(
                    SceneParticipantRecord(
                        scene_id=scene2,
                        entity_id=mira_id,
                        participant_role="actor",
                    ),
                ),
            )
        )
        with pytest.raises(IntegrityError):
            await uow.scene_resolutions.insert(
                SceneResolutionRecord(
                    id=uuid.uuid4(),
                    scene_id=scene2,
                    resolution_level="success",
                    canonical_summary="Again.",
                    confidence=Decimal("0.9"),
                    visual_significance=Decimal("0.1"),
                    idempotency_key="resolution:once",
                )
            )
            await uow.commit()
