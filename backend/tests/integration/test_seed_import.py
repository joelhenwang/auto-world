"""Integration tests for S0-CONTENT-001 / S2-CONTENT-001 seed import."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.seed import (
    WORLD_SEEDED,
    SeedImporter,
    SeedImportError,
    import_caldris_stage0,
    import_caldris_stage1,
    import_caldris_stage2,
    load_seed_pack,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"
MIRA_PRIVATE_FRAGMENT = "falsified north-route report"


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


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_import_empty_and_repeat(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        first = await import_caldris_stage0(uow, root=PACK)
        await uow.commit()
    assert first.already_imported is False
    assert first.event_id is not None
    assert first.seed_keys["world/caldris"] == str(seed_uuid("world/caldris"))
    assert first.seed_keys["character/mira-talren"] == str(seed_uuid("character/mira-talren"))

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        second = await import_caldris_stage0(uow, root=PACK)
        await uow.commit()
        event = await uow.events.get(first.event_id)
    assert second.already_imported is True
    assert second.world_id == first.world_id
    assert second.event_id == first.event_id
    assert event is not None
    assert event.event_type == WORLD_SEEDED
    assert event.structured_facts["manifest_hash"] == first.manifest_hash


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_broken_reference_rolls_back(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    pack = load_seed_pack(PACK, fixture_name="stage0")
    broken = pack.model_copy(
        update={
            "characters": {
                "character/mira-talren": {
                    **pack.characters["character/mira-talren"],
                    "character": {
                        **pack.characters["character/mira-talren"]["character"],
                        "current_location": "location/does-not-exist",
                    },
                }
            }
        }
    )
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        with pytest.raises(SeedImportError):
            await SeedImporter(uow).import_pack(broken)
        await uow.rollback()

    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        world = await uow.worlds.get_by_slug("caldris")
    assert world is None


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_secret_separation_fixture(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        result = await import_caldris_stage0(uow, root=PACK)
        await uow.commit()
        mira_id = seed_uuid("character/mira-talren")
        card_id = seed_uuid("character/mira-talren/card/v1")
        card = await uow.characters.get_card(card_id)
        event = await uow.events.get(result.event_id) if result.event_id else None
        state = await uow.characters.get_state(mira_id)

    assert card is not None
    secrets = card.secret_manifest
    beliefs = secrets.get("private_beliefs", [])
    assert any(MIRA_PRIVATE_FRAGMENT in str(item.get("proposition", "")) for item in beliefs)
    assert event is not None
    facts_blob = str(event.structured_facts)
    assert MIRA_PRIVATE_FRAGMENT not in facts_blob
    assert "director_only" not in facts_blob
    assert state is not None
    assert state.location_id == seed_uuid("location/veycross/cinder-lantern-inn")


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_import_caldris_stage1_two_characters(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        result = await import_caldris_stage1(uow, root=PACK)
        await uow.commit()
        char_keys = [k for k in result.seed_keys if k.startswith("character/")]
        edges = await uow.relationship_edges.list_for_source(
            seed_uuid("character/mira-talren"), world_id=result.world_id
        )
        routes = await uow.routes.list_for_world(result.world_id)

    assert set(char_keys) == {"character/mira-talren", "character/dain-arcen"}
    assert len(edges) == 1
    assert edges[0].target_character_id == seed_uuid("character/dain-arcen")
    # Stage 1 activates inn/market/bridge — only routes among those endpoints.
    assert len(routes) >= 1
    assert "character/iri-voss" not in result.seed_keys
    assert "character/torren-kest" not in result.seed_keys


@pytest.mark.integration
@pytest.mark.requires_docker
@pytest.mark.asyncio
async def test_import_caldris_stage2_four_characters(
    uow_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with SqlAlchemyUnitOfWork(uow_factory) as uow:
        result = await import_caldris_stage2(uow, root=PACK)
        await uow.commit()

        char_keys = sorted(k for k in result.seed_keys if k.startswith("character/"))
        assert char_keys == [
            "character/dain-arcen",
            "character/iri-voss",
            "character/mira-talren",
            "character/torren-kest",
        ]

        iri_state = await uow.characters.get_state(seed_uuid("character/iri-voss"))
        torren_state = await uow.characters.get_state(seed_uuid("character/torren-kest"))
        assert iri_state is not None
        assert torren_state is not None
        assert iri_state.location_id == seed_uuid("location/veycross/lantern-annex")
        assert torren_state.location_id == seed_uuid("location/veycross/river-forge")

        routes = await uow.routes.list_for_world(result.world_id)
        assert len(routes) >= 1

        mira_edges = await uow.relationship_edges.list_for_source(
            seed_uuid("character/mira-talren"), world_id=result.world_id
        )
        iri_edges = await uow.relationship_edges.list_for_source(
            seed_uuid("character/iri-voss"), world_id=result.world_id
        )
        assert len(mira_edges) >= 2  # Dain + Iri
        assert len(iri_edges) >= 2  # Mira + Torren

        mira_goals = await uow.goals.list_for_owner(
            seed_uuid("character/mira-talren"), world_id=result.world_id
        )
        iri_goals = await uow.goals.list_for_owner(
            seed_uuid("character/iri-voss"), world_id=result.world_id
        )
        torren_goals = await uow.goals.list_for_owner(
            seed_uuid("character/torren-kest"), world_id=result.world_id
        )
        assert len(mira_goals) >= 2
        assert len(iri_goals) >= 2
        assert len(torren_goals) >= 2

        iri_beliefs = await uow.beliefs.list_for_character(
            seed_uuid("character/iri-voss"), world_id=result.world_id
        )
        torren_beliefs = await uow.beliefs.list_for_character(
            seed_uuid("character/torren-kest"), world_id=result.world_id
        )
        assert len(iri_beliefs) >= 1
        assert "deliberate interference" in iri_beliefs[0].belief_text
        assert len(torren_beliefs) >= 1
        assert "nonstandard internal pattern" in torren_beliefs[0].belief_text

        secrets = await uow.secret_access.list_for_holder(
            seed_uuid("character/iri-voss"), world_id=result.world_id
        )
        assert len(secrets) >= 1
        assert secrets[0].access_level == "owner"
        assert secrets[0].owner_character_id == secrets[0].holder_character_id
