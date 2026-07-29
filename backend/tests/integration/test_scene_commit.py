"""PostgreSQL integration proof for atomic idempotent Stage 1 scene commits."""

from __future__ import annotations

import hashlib
import subprocess
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.simulation import (
    CommitSceneCommand,
    EventCommitError,
    SceneCommitService,
)
from fictional_world.application.simulation.commit import expected_character_state_key
from fictional_world.application.simulation.scene_assembly import assemble_scenes
from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.common.enums import (
    ActionFamily,
    ResolutionLevel,
    Visibility,
)
from fictional_world.domain.effects import CreateClaimEffect, SpendResourceEffect
from fictional_world.domain.phases.records import PhaseRunRecord, PhaseSnapshotRecord
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    FallbackAction,
    NarrationConstraints,
    ReactionProposal,
    SceneResolution,
)
from fictional_world.domain.seed.records import LocationRecord
from fictional_world.domain.world.records import AggregateVersionRecord, WorldRecord
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
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE worldsim.world CASCADE"))
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield factory
    await engine.dispose()


async def _seed_scene_inputs(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    world_id = uuid.uuid4()
    phase_id = uuid.uuid4()
    snapshot_id = uuid.uuid4()
    mira_id = uuid.uuid4()
    dain_id = uuid.uuid4()
    inn_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(factory) as uow:
        assert uow.session is not None
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"scene-{world_id.hex[:8]}",
                name="Scene Commit World",
                status="active",
            )
        )
        await uow.characters.insert_entity(
            EntityRecord(
                id=inn_id,
                world_id=world_id,
                entity_type="location",
                canonical_name="Cinder Lantern Inn",
                normalized_name="cinder lantern inn",
                lifecycle_status="active",
            )
        )
        await uow.characters.insert_location(
            LocationRecord(
                entity_id=inn_id,
                location_type="building",
                region_code="embervale",
                canonical_description="A warm inn.",
            )
        )
        for character_id, name in ((mira_id, "Mira"), (dain_id, "Dain")):
            await uow.characters.insert_entity(
                EntityRecord(
                    id=character_id,
                    world_id=world_id,
                    entity_type="character",
                    canonical_name=name,
                    normalized_name=name.lower(),
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
            card_id = uuid.uuid4()
            uow.session.add(
                CharacterCardVersionRow(
                    id=card_id,
                    character_id=character_id,
                    version_number=1,
                    identity={"canonical_name": name},
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
            await uow.characters.set_character_card(character_id, card_version_id=card_id)
            await uow.characters.insert_state(
                CharacterStateRecord(
                    character_id=character_id,
                    location_id=inn_id,
                    life_status="alive",
                    stamina=Decimal("80"),
                    mana=Decimal("20"),
                    energy=Decimal("70"),
                    hunger=Decimal("20"),
                    pain=Decimal("0"),
                    stress=Decimal("10"),
                    social_need=Decimal("30"),
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
        await uow.phases.insert(
            PhaseRunRecord(
                id=phase_id,
                world_id=world_id,
                absolute_phase_index=1,
                phase_name="dawn",
                resolution_mode="detailed",
                state="resolving_scenes",
                expected_character_count=2,
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
                state_hash=hashlib.sha256(b"scene-snapshot").hexdigest(),
                sealed_at=datetime.now(UTC),
            )
        )
        await uow.commit()
    return world_id, phase_id, snapshot_id, mira_id, dain_id, inn_id


def _scene_command(
    *,
    world_id: uuid.UUID,
    phase_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    mira_id: uuid.UUID,
    dain_id: uuid.UUID,
    inn_id: uuid.UUID,
    observer_ids: tuple[uuid.UUID, ...],
    invalid_spend: bool = False,
) -> CommitSceneCommand:
    mira_attempt = ActionProposal(
        decision_request_id=uuid.uuid5(phase_id, "mira-attempt"),
        actor_id=mira_id,
        action_family=ActionFamily.COMMUNICATE,
        description="Mira asks Dain whether the east bridge is open.",
        utterance="Is the east bridge open?",
        target_entity_ids=(dain_id,),
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait by the hearth.",
        ),
    )
    dain_attempt = ActionProposal(
        decision_request_id=uuid.uuid5(phase_id, "dain-attempt"),
        actor_id=dain_id,
        action_family=ActionFamily.WAIT,
        description="Dain remains by the hearth.",
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Continue waiting.",
        ),
    )
    scene = assemble_scenes(
        phase_id,
        snapshot_id,
        (mira_attempt, dain_attempt),
        {mira_id: inn_id, dain_id: inn_id},
    )[0]
    reaction = ReactionProposal(
        reaction_request_id=uuid.uuid5(scene.scene_id, "dain-reaction"),
        scene_id=scene.scene_id,
        triggering_attempt_id=mira_attempt.decision_request_id,
        reactor_id=dain_id,
        action_family=ActionFamily.COMMUNICATE,
        description="Dain answers with his direct observation.",
        utterance="It was open at dawn.",
        target_entity_ids=(mira_id,),
    )
    effects = (
        (
            SpendResourceEffect(
                effect_key="invalid-overspend",
                source_attempt_ids=(mira_attempt.decision_request_id,),
                justification="Fault injection.",
                entity_id=mira_id,
                resource="stamina",
                amount=500,
            ),
        )
        if invalid_spend
        else (
            CreateClaimEffect(
                effect_key="mira-bridge-question",
                source_attempt_ids=(mira_attempt.decision_request_id,),
                justification="Mira's attempted utterance was accepted.",
                speaker_id=mira_id,
                listener_ids=(dain_id,),
                proposition=mira_attempt.utterance or "Is the east bridge open?",
            ),
        )
    )
    resolution = SceneResolution(
        resolution_request_id=uuid.uuid5(scene.scene_id, "resolution"),
        scene_id=scene.scene_id,
        level=ResolutionLevel.SUCCESS,
        accepted_attempt_ids=(
            mira_attempt.decision_request_id,
            dain_attempt.decision_request_id,
            reaction.reaction_request_id,
        ),
        effects=effects,
        canonical_summary="Mira asked about the bridge, and Dain said it was open at dawn.",
        narration_constraints=NarrationConstraints(maximum_words=120),
        visual_significance=0.1,
        confidence=0.95,
    )
    return CommitSceneCommand(
        world_id=world_id,
        phase_run_id=phase_id,
        absolute_phase_index=1,
        idempotency_key="stage1-scene-commit",
        scene=scene,
        proposals=(mira_attempt, dain_attempt),
        reactions=(reaction,),
        resolution=resolution,
        expected_versions={
            expected_character_state_key(mira_id): 0,
            expected_character_state_key(dain_id): 0,
        },
        observer_ids=observer_ids,
        knowledge_scope_hashes={
            observer_id: f"scope-{observer_id}" for observer_id in observer_ids
        },
    )


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_scene_commit_is_retry_safe_and_observer_scoped(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, phase_id, snapshot_id, mira_id, dain_id, inn_id = await _seed_scene_inputs(
        uow_factory
    )
    command = _scene_command(
        world_id=world_id,
        phase_id=phase_id,
        snapshot_id=snapshot_id,
        mira_id=mira_id,
        dain_id=dain_id,
        inn_id=inn_id,
        observer_ids=(mira_id,),
    )
    service = SceneCommitService()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        first = await service.commit(uow, command)
        await uow.commit()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        repeated = await service.commit(uow, command)
        await uow.commit()

    assert first.already_existed is False
    assert repeated.already_existed is True
    assert repeated.event_id == first.event_id
    assert repeated.stream_event_id == first.stream_event_id

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        assert uow.session is not None
        counts = (
            await uow.session.execute(
                text(
                    """
                    SELECT
                      (SELECT count(*) FROM worldsim.action_proposal),
                      (SELECT count(*) FROM worldsim.scene),
                      (SELECT count(*) FROM worldsim.reaction_proposal),
                      (SELECT count(*) FROM worldsim.scene_resolution),
                      (SELECT count(*) FROM worldsim.scene_run),
                      (SELECT count(*) FROM worldsim.narration),
                      (SELECT count(*) FROM worldsim.stream_event),
                      (SELECT count(*) FROM worldsim.world_event),
                      (SELECT count(*) FROM worldsim.outbox_message)
                    """
                )
            )
        ).one()
        assert tuple(counts) == (2, 1, 1, 1, 1, 1, 1, 1, 3)
        mira_observations = await uow.observations.list_for_observer(mira_id)
        dain_observations = await uow.observations.list_for_observer(dain_id)
        assert len(mira_observations) == 1
        assert dain_observations == []
        mira_memories = await uow.recent_memories.list_for_owner(mira_id, world_id=world_id)
        dain_memories = await uow.recent_memories.list_for_owner(dain_id, world_id=world_id)
        assert len(mira_memories) == 1
        assert dain_memories == []


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_scene_commit_rolls_back_all_projections_on_effect_failure(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, phase_id, snapshot_id, mira_id, dain_id, inn_id = await _seed_scene_inputs(
        uow_factory
    )
    command = _scene_command(
        world_id=world_id,
        phase_id=phase_id,
        snapshot_id=snapshot_id,
        mira_id=mira_id,
        dain_id=dain_id,
        inn_id=inn_id,
        observer_ids=(mira_id, dain_id),
        invalid_spend=True,
    )

    with pytest.raises(EventCommitError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await SceneCommitService().commit(uow, command)

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        assert uow.session is not None
        counts = (
            await uow.session.execute(
                text(
                    """
                    SELECT
                      (SELECT count(*) FROM worldsim.action_proposal),
                      (SELECT count(*) FROM worldsim.scene),
                      (SELECT count(*) FROM worldsim.world_event)
                    """
                )
            )
        ).one()
        assert tuple(counts) == (0, 0, 0)
        world = await uow.worlds.get(world_id)
        assert world is not None
        assert world.current_event_sequence == 0
