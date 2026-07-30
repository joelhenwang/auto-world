"""Integration tests: Stage 2 continuity schema constraints (S2-DB-001)."""

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
from fictional_world.domain.continuity.persistence import (
    ActivityPersistenceRecord,
    NpcProfilePersistenceRecord,
    RelationshipEdgePersistenceRecord,
    RoutePersistenceRecord,
)
from fictional_world.domain.knowledge.persistence import BeliefPersistenceRecord
from fictional_world.domain.seed.records import LocationRecord
from fictional_world.domain.world.records import WorldRecord
from fictional_world.infrastructure.database.models import CharacterCardVersionRow
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"

STAGE2_TABLES = {
    "route",
    "goal",
    "plan",
    "plan_step",
    "commitment",
    "relationship_edge",
    "relationship_evidence",
    "claim",
    "claim_listener",
    "belief",
    "belief_evidence",
    "secret_access",
    "activity",
    "activity_participant",
    "travel_progress",
    "hook",
    "narrative_metric",
    "npc_profile",
    "npc_lifecycle",
    "summary",
    "summary_source",
    "diary_entry",
    "day_run",
    "daily_audit",
    "scheduled_effect",
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


async def _seed_world_two_chars(
    factory: async_sessionmaker[AsyncSession],
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
    """Return world_id, mira_id, kael_id, origin_id, dest_id."""
    world_id = uuid.uuid4()
    mira_id = uuid.uuid4()
    kael_id = uuid.uuid4()
    origin_id = uuid.uuid4()
    dest_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(factory) as uow:
        assert uow.session is not None
        await uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=f"s2-{world_id.hex[:8]}",
                name="Stage2",
                status="active",
                language="en",
                content_rating="young_adult_soft_dark",
                current_event_sequence=0,
                version=0,
            )
        )
        for loc_id, name, norm in (
            (origin_id, "Inn", "inn"),
            (dest_id, "Market", "market"),
        ):
            await uow.characters.insert_entity(
                EntityRecord(
                    id=loc_id,
                    world_id=world_id,
                    entity_type="location",
                    canonical_name=name,
                    normalized_name=norm,
                    lifecycle_status="active",
                )
            )
            await uow.characters.insert_location(
                LocationRecord(
                    entity_id=loc_id,
                    location_type="building",
                    region_code="embervale",
                    capacity=40,
                    environment_tags=(norm,),
                    canonical_description=name,
                )
            )
        for char_id, name, kind in (
            (mira_id, "Mira", "focus"),
            (kael_id, "Kael", "temporary_npc"),
        ):
            await uow.characters.insert_entity(
                EntityRecord(
                    id=char_id,
                    world_id=world_id,
                    entity_type="character",
                    canonical_name=name,
                    normalized_name=name.lower(),
                    lifecycle_status="active",
                )
            )
            await uow.characters.insert_character(
                CharacterRecord(
                    entity_id=char_id,
                    character_kind=kind,
                    species_code="human",
                )
            )
            card_id = uuid.uuid4()
            uow.session.add(
                CharacterCardVersionRow(
                    id=card_id,
                    character_id=char_id,
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
                    content_hash=hashlib.sha256(f"{char_id}-v1".encode()).hexdigest(),
                )
            )
            await uow.session.flush()
            await uow.characters.set_character_card(char_id, card_version_id=card_id)
            await uow.characters.insert_state(
                CharacterStateRecord(
                    character_id=char_id,
                    location_id=origin_id,
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
    return world_id, mira_id, kael_id, origin_id, dest_id


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage2_tables_exist(migrated_engine: AsyncEngine) -> None:
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
    assert names >= STAGE2_TABLES


@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_stage2_migration_roundtrip(postgres_container: dict[str, str]) -> None:
    url = _normalize_url(postgres_container["url"])
    heads = _alembic(url, "heads").stdout.strip().splitlines()
    assert len(heads) == 1
    assert "0005_stage3_long_term_tables" in heads[0]
    _alembic(url, "upgrade", "head")
    _alembic(url, "downgrade", "-1")
    _alembic(url, "upgrade", "head")


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_relationship_edge(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, kael_id, _o, _d = await _seed_world_two_chars(uow_factory)
    edge = RelationshipEdgePersistenceRecord(
        source_character_id=mira_id,
        target_character_id=kael_id,
        world_id=world_id,
        familiarity=Decimal("0.2"),
        trust=Decimal("0.1"),
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.relationship_edges.insert(edge)
        await uow.commit()
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.relationship_edges.insert(
                RelationshipEdgePersistenceRecord(
                    source_character_id=mira_id,
                    target_character_id=kael_id,
                    world_id=world_id,
                )
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_belief_proposition(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, _k, _o, _d = await _seed_world_two_chars(uow_factory)
    belief = BeliefPersistenceRecord(
        id=uuid.uuid4(),
        world_id=world_id,
        character_id=mira_id,
        proposition_key="kael_is_kind",
        belief_text="Kael seems kind",
        confidence=Decimal("0.6"),
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.beliefs.insert(belief)
        await uow.commit()
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.beliefs.insert(
                BeliefPersistenceRecord(
                    id=uuid.uuid4(),
                    world_id=world_id,
                    character_id=mira_id,
                    proposition_key="kael_is_kind",
                    belief_text="Kael is kind",
                    confidence=Decimal("0.7"),
                )
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_duplicate_npc_profile(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, _m, kael_id, _o, _d = await _seed_world_two_chars(uow_factory)
    profile = NpcProfilePersistenceRecord(
        character_id=kael_id,
        world_id=world_id,
        display_name="Kael",
        similarity_fingerprint="fp-kael-1",
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.npcs.insert_profile(profile)
        await uow.commit()
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.npcs.insert_profile(
                NpcProfilePersistenceRecord(
                    character_id=kael_id,
                    world_id=world_id,
                    display_name="Kael Dup",
                    similarity_fingerprint="fp-kael-2",
                )
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_belief_confidence_above_one(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, _k, _o, _d = await _seed_world_two_chars(uow_factory)
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            assert uow.session is not None
            await uow.session.execute(
                text(
                    """
                    INSERT INTO worldsim.belief (
                        id, world_id, character_id, proposition_key, belief_text,
                        confidence, status, evidence_summary, version
                    ) VALUES (
                        :id, :world_id, :character_id, 'x', 'too sure',
                        1.5, 'active', '{}'::jsonb, 0
                    )
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "world_id": world_id,
                    "character_id": mira_id,
                },
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_rejects_route_nonpositive_distance(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, _m, _k, origin_id, dest_id = await _seed_world_two_chars(uow_factory)
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.routes.insert(
                RoutePersistenceRecord(
                    id=uuid.uuid4(),
                    world_id=world_id,
                    origin_location_id=origin_id,
                    destination_location_id=dest_id,
                    distance_units=Decimal("0"),
                    base_duration_phases=1,
                )
            )
            await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_travel_activity_requires_route(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    world_id, mira_id, _k, origin_id, dest_id = await _seed_world_two_chars(uow_factory)
    with pytest.raises(IntegrityError):
        async with SqlAlchemyUnitOfWork(uow_factory) as uow:
            await uow.activities.insert(
                ActivityPersistenceRecord(
                    id=uuid.uuid4(),
                    world_id=world_id,
                    owner_entity_id=mira_id,
                    activity_type="travel",
                    origin_location_id=origin_id,
                    destination_location_id=dest_id,
                    route_id=None,
                    started_phase_index=0,
                )
            )
            await uow.commit()

    route_id = uuid.uuid4()
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        await uow.routes.insert(
            RoutePersistenceRecord(
                id=route_id,
                world_id=world_id,
                origin_location_id=origin_id,
                destination_location_id=dest_id,
                distance_units=Decimal("3.5"),
                base_duration_phases=2,
            )
        )
        await uow.activities.insert(
            ActivityPersistenceRecord(
                id=uuid.uuid4(),
                world_id=world_id,
                owner_entity_id=mira_id,
                activity_type="travel",
                origin_location_id=origin_id,
                destination_location_id=dest_id,
                route_id=route_id,
                started_phase_index=0,
            )
        )
        await uow.commit()


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_scene_and_event_additive_columns(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as conn:
        scene_cols = await conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'worldsim' AND table_name = 'scene'
                """
            )
        )
        event_cols = await conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'worldsim' AND table_name = 'world_event'
                """
            )
        )
    scene_names = {r[0] for r in scene_cols.fetchall()}
    event_names = {r[0] for r in event_cols.fetchall()}
    assert {"continuation_id", "director_hook_id", "observer_eligibility"} <= scene_names
    assert {"director_provenance", "npc_provenance"} <= event_names
