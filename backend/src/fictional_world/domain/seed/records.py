"""Additional seed-oriented persistence records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]


class LocationRecord(StrictContract):
    entity_id: UUID
    parent_location_id: UUID | None = None
    location_type: str = Field(min_length=1, max_length=100)
    region_code: str = Field(min_length=1, max_length=100)
    coordinate_x: Decimal | None = None
    coordinate_y: Decimal | None = None
    elevation: Decimal | None = None
    capacity: int | None = None
    owner_entity_id: UUID | None = None
    environment_tags: tuple[str, ...] = ()
    canonical_description: str = Field(min_length=1, max_length=10_000)
    visual_profile_version: int = Field(default=1, ge=1)
    version: int = Field(default=0, ge=0)


class WorldConfigRecord(StrictContract):
    id: UUID
    world_id: UUID
    config_version: int = Field(ge=1)
    is_active: bool = False
    effective_from_phase_index: int = Field(default=0, ge=0)
    detailed_phase_names: tuple[str, ...]
    max_days: int = Field(ge=1)
    max_generations: int = Field(ge=1, le=3)
    plot_armour_level: Decimal = Field(default=Decimal("0"))
    director_privileges: JsonObject = Field(default_factory=dict)
    image_budget_per_day: int = Field(default=0, ge=0)
    macro_simulation_policy: JsonObject = Field(default_factory=dict)
    content_policy_version: str = Field(min_length=1, max_length=100)
    created_event_id: UUID | None = None
    created_at: datetime | None = None


class CharacterCardVersionRecord(StrictContract):
    id: UUID
    character_id: UUID
    version_number: int = Field(ge=1)
    identity: JsonObject = Field(default_factory=dict)
    backstory: str = ""
    appearance: JsonObject = Field(default_factory=dict)
    personality_traits: JsonObject = Field(default_factory=dict)
    values: JsonObject = Field(default_factory=dict)
    fears: JsonObject = Field(default_factory=dict)
    desires: JsonObject = Field(default_factory=dict)
    boundaries: JsonObject = Field(default_factory=dict)
    voice_profile: JsonObject = Field(default_factory=dict)
    initial_capabilities: JsonObject = Field(default_factory=dict)
    secret_manifest: JsonObject = Field(default_factory=dict)
    change_summary: str = Field(min_length=1, max_length=500)
    source_event_id: UUID | None = None
    content_hash: str = Field(min_length=1, max_length=128)
    created_at: datetime | None = None
