"""Shared HTTP runtime helpers for Stage 1 / Stage 2 phase runners."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.orchestration.stage2_ops import STAGE2_CHARACTER_IDS
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.config.settings import AppSettings
from fictional_world.testing import Stage1FakeModelGateway, Stage2FakeModelGateway


async def is_stage2_world(uow: UnitOfWork, world_id: UUID) -> bool:
    """Detect Stage 2 fixtures via focus cast or seeded fixture name."""

    config = await uow.worlds.get_active_config(world_id)
    if config is not None:
        fixture = config.macro_simulation_policy.get("fixture")
        if fixture == "stage2":
            return True
        if fixture in {"stage0", "stage1"}:
            return False
    character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
    return all(character_id in character_ids for character_id in STAGE2_CHARACTER_IDS)


def require_fake_provider(settings: AppSettings) -> None:
    if settings.model_gateway.provider_mode != "fake":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Runtime API currently requires configured fake provider mode",
        )


async def phase_runner_for_world(
    uow: UnitOfWork,
    settings: AppSettings,
    world_id: UUID,
    *,
    force_stage2: bool = False,
) -> DeterministicPhaseRunner:
    """Build a DeterministicPhaseRunner with the correct stage profile."""

    require_fake_provider(settings)
    stage2 = force_stage2 or await is_stage2_world(uow, world_id)
    if stage2:
        return DeterministicPhaseRunner(
            uow,
            model_gateway=Stage2FakeModelGateway(),
            stage2=True,
        )
    return DeterministicPhaseRunner(
        uow,
        model_gateway=Stage1FakeModelGateway(),
        stage1=True,
    )


__all__ = [
    "is_stage2_world",
    "phase_runner_for_world",
    "require_fake_provider",
]
