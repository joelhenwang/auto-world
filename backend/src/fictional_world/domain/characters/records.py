"""Character persistence records (Stage 0 surface for S0-DB-003)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class CharacterStateRecord(StrictContract):
    character_id: UUID
    location_id: UUID | None = None
    life_status: str = Field(min_length=1, max_length=50)
    stamina: Decimal
    mana: Decimal
    energy: Decimal
    hunger: Decimal
    pain: Decimal
    stress: Decimal
    social_need: Decimal
    valence: Decimal
    arousal: Decimal
    dominance: Decimal
    active_activity_id: UUID | None = None
    current_card_version_id: UUID
    last_source_event_id: UUID | None = None
    version: int = Field(ge=0)
    updated_at: datetime | None = None


class EntityRecord(StrictContract):
    id: UUID
    world_id: UUID
    entity_type: str = Field(min_length=1, max_length=50)
    canonical_name: str = Field(min_length=1, max_length=200)
    normalized_name: str = Field(min_length=1, max_length=200)
    lifecycle_status: str = Field(min_length=1, max_length=50)
    created_event_id: UUID | None = None
    archived_event_id: UUID | None = None
    created_at: datetime | None = None
    archived_at: datetime | None = None


class CharacterRecord(StrictContract):
    entity_id: UUID
    character_kind: str = Field(min_length=1, max_length=50)
    species_code: str = Field(min_length=1, max_length=100)
    current_card_version_id: UUID | None = None
    version: int = Field(default=0, ge=0)
