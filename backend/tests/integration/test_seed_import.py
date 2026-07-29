"""Integration tests for S0-CONTENT-001 seed import."""

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
