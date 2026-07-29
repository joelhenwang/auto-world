"""Shared entity/provenance contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import EntityKind, SourceKind


class EntityRef(StrictContract):
    entity_id: UUID
    kind: EntityKind
    display_name: str = Field(min_length=1, max_length=200)


class Provenance(StrictContract):
    source_kind: SourceKind
    source_id: UUID
    model_slug: str | None = Field(default=None, max_length=200)
    provider: str | None = Field(default=None, max_length=100)
    prompt_version: str | None = Field(default=None, max_length=100)
    schema_version: str = Field(default="1.0", max_length=30)
    seed: int | None = None
    created_at: datetime


class PhaseSnapshotRef(StrictContract):
    snapshot_id: UUID
    phase_id: UUID
    world_state_version: int = Field(ge=0)
    state_hash: str = Field(min_length=32, max_length=128)
    created_at: datetime
