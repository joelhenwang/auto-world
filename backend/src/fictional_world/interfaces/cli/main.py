"""Stage 0 CLI: seed, advance, reconcile, clock (S0-API-001)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import cast
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.orchestration.protocol import (
    PhaseAdvanceResult,
    ReconciliationReport,
)
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed import SeedImportResult, import_caldris_stage0
from fictional_world.config import settings_from_profile, validate_settings
from fictional_world.config.settings import repo_root
from fictional_world.infrastructure.database.session import database_url
from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from fictional_world.observability.logging import configure_logging

DEFAULT_PACK = repo_root() / "seed" / "worlds" / "caldris-embervale-v1"


def _normalize_url(raw: str) -> str:
    return raw.replace("postgresql+psycopg2://", "postgresql+psycopg://").replace(
        "postgresql://", "postgresql+psycopg://"
    )


def _resolve_database_url() -> str:
    if raw := os.environ.get("DATABASE_URL"):
        return _normalize_url(raw)
    settings = settings_from_profile(os.environ.get("APP_PROFILE", "stage0"))
    validate_settings(settings)
    return database_url(settings.database)


def _make_engine(url: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, factory


async def _with_uow[T](handler: Callable[[UnitOfWork], Awaitable[T]]) -> T:
    engine, factory = _make_engine(_resolve_database_url())
    try:
        async with SqlAlchemyUnitOfWork(factory) as uow:
            return await handler(cast(UnitOfWork, uow))
    finally:
        await engine.dispose()


async def _cmd_seed(pack: Path, fixture: str) -> None:
    async def handler(uow: UnitOfWork) -> SeedImportResult:
        result = await import_caldris_stage0(uow, root=pack, fixture_name=fixture)
        await uow.commit()
        return result

    result = await _with_uow(handler)
    print(
        json.dumps(
            {
                "seed_id": result.seed_id,
                "world_id": str(result.world_id),
                "event_id": str(result.event_id),
                "already_imported": result.already_imported,
                "manifest_hash": result.manifest_hash,
            },
            indent=2,
        )
    )


async def _cmd_advance(world_id: UUID) -> None:
    async def handler(uow: UnitOfWork) -> PhaseAdvanceResult:
        runner = DeterministicPhaseRunner(uow)
        result = await runner.request_phase_advance(world_id)
        await uow.commit()
        return result

    result = await _with_uow(handler)
    print(
        json.dumps(
            {
                "phase_run_id": str(result.phase_run_id),
                "absolute_phase_index": result.absolute_phase_index,
                "phase_name": result.phase_name,
                "already_completed": result.already_completed,
                "snapshot_id": str(result.snapshot_id) if result.snapshot_id else None,
                "event_ids": [str(eid) for eid in result.event_ids],
            },
            indent=2,
        )
    )


async def _cmd_reconcile(world_id: UUID) -> None:
    async def handler(uow: UnitOfWork) -> ReconciliationReport:
        runner = DeterministicPhaseRunner(uow)
        report = await runner.reconcile(world_id)
        await uow.commit()
        return report

    report = await _with_uow(handler)
    print(
        json.dumps(
            {
                "world_id": str(report.world_id),
                "active_phase_id": (
                    str(report.active_phase_id) if report.active_phase_id else None
                ),
                "tasks_created": report.tasks_created,
                "phase_completed": report.phase_completed,
                "notes": list(report.notes),
            },
            indent=2,
        )
    )


async def _cmd_clock(world_id: UUID) -> None:
    async def handler(uow: UnitOfWork) -> dict[str, object]:
        clock = await uow.worlds.get_clock(world_id)
        if clock is None:
            raise SystemExit(f"world clock not found: {world_id}")
        return cast(dict[str, object], clock.model_dump(mode="json"))

    payload = await _with_uow(handler)
    print(json.dumps(payload, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="world-cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    seed = sub.add_parser("seed", help="Import Caldris Stage 0 seed pack")
    seed.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    seed.add_argument("--fixture", default="stage0")

    advance = sub.add_parser("advance", help="Advance one deterministic phase")
    advance.add_argument("--world-id", type=UUID, required=True)

    reconcile = sub.add_parser("reconcile", help="Reconcile durable phase/tasks")
    reconcile.add_argument("--world-id", type=UUID, required=True)

    clock = sub.add_parser("clock", help="Show world clock")
    clock.add_argument("--world-id", type=UUID, required=True)

    return parser


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "seed":
        asyncio.run(_cmd_seed(args.pack, args.fixture))
    elif args.command == "advance":
        asyncio.run(_cmd_advance(args.world_id))
    elif args.command == "reconcile":
        asyncio.run(_cmd_reconcile(args.world_id))
    elif args.command == "clock":
        asyncio.run(_cmd_clock(args.world_id))
    else:
        parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
