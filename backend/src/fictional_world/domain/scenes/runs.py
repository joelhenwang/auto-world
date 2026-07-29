"""Phase and scene operational aggregates."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import PhaseStage, RunStatus, SceneStage
from fictional_world.domain.time.fictional_time import FictionalTime


class PhaseRun(StrictContract):
    phase_id: UUID
    world_id: UUID
    fictional_time: FictionalTime
    status: RunStatus
    stage: PhaseStage
    snapshot_id: UUID | None = None
    expected_character_ids: tuple[UUID, ...] = ()
    action_proposal_ids: tuple[UUID, ...] = ()
    scene_ids: tuple[UUID, ...] = ()
    completed_scene_ids: tuple[UUID, ...] = ()
    image_outbox_ids: tuple[UUID, ...] = ()
    attempt_count: int = Field(default=0, ge=0)
    version: int = Field(ge=0)


class SceneRun(StrictContract):
    scene_id: UUID
    phase_id: UUID
    status: RunStatus
    stage: SceneStage
    participant_ids: tuple[UUID, ...] = Field(min_length=1)
    action_proposal_ids: tuple[UUID, ...] = Field(min_length=1)
    reaction_proposal_ids: tuple[UUID, ...] = ()
    resolution_id: UUID | None = None
    committed_event_id: UUID | None = None
    beat_count: int = Field(default=0, ge=0)
    beat_budget: int = Field(ge=1, le=12)
    high_impact: bool = False
    attempt_count: int = Field(default=0, ge=0)
    version: int = Field(ge=0)
