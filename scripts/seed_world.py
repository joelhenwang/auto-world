#!/usr/bin/env python3
"""Import the Caldris Stage 0 seed pack into the configured database."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed import (
    import_caldris_stage0,
    load_seed_pack,
    validate_seed_pack,
)
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


async def _run(pack_root: Path, fixture: str) -> None:
    url = _normalize_url(
        os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://worldsim:worldsim@127.0.0.1:5432/worldsim",
        )
    )
    pack = load_seed_pack(pack_root, fixture_name=fixture)
    report = validate_seed_pack(pack)
    if not report.ok:
        for issue in report.result.issues:
            print(f"ERROR {issue.code}: {issue.message}")
        raise SystemExit(1)

    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with SqlAlchemyUnitOfWork(factory) as uow:
            result = await import_caldris_stage0(
                cast(UnitOfWork, uow), root=pack_root, fixture_name=fixture
            )
            await uow.commit()
    finally:
        await engine.dispose()

    print(
        f"seed_id={result.seed_id} world_id={result.world_id} "
        f"event_id={result.event_id} already_imported={result.already_imported} "
        f"manifest_hash={result.manifest_hash}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--fixture", default="stage0")
    args = parser.parse_args()
    asyncio.run(_run(args.pack, args.fixture))


if __name__ == "__main__":
    main()
