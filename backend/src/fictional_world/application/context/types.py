"""Stage 1 sealed context package contracts (S1-KNOW-001)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class ContextTaskType(StrEnum):
    CHARACTER_DECISION = "character_decision"
    CHARACTER_REACTION = "character_reaction"
    SCENE_RESOLUTION = "scene_resolution"
    SCENE_NARRATION = "scene_narration"


class ContextSectionId(StrEnum):
    STABLE_IDENTITY = "stable_identity"
    CURRENT_STATE = "current_state"
    CURRENT_PERCEPTION = "current_perception"
    GOALS_AND_PLANS = "goals_and_plans"
    RELATIONSHIPS = "relationships"
    RECENT_MEMORY = "recent_memory"
    CAPABILITIES = "capabilities"
    KNOWN_LOCAL_MAP = "known_local_map"
    ALLOWED_ACTION_FAMILIES = "allowed_action_families"
    PRIVATE_BELIEFS = "private_beliefs"
    SCENE_WORKING = "scene_working"


STAGE1_ACTION_FAMILIES: tuple[str, ...] = (
    "wait",
    "observe",
    "rest",
    "continue_activity",
    "move",
    "communicate",
    "socialize",
    "interact_environment",
)


class ContextSection(StrictContract):
    section_id: ContextSectionId
    content: dict[str, Any] | str | list[Any]
    source_record_ids: tuple[str, ...] = ()
    token_estimate: int = Field(ge=0)
    trusted: bool = True
    content_hash: str = Field(min_length=1, max_length=128)


class SealedContextPackage(StrictContract):
    """Perspective-safe sealed context for one character and one snapshot."""

    schema_version: Literal["1.0"] = "1.0"
    package_id: UUID
    observer_id: UUID
    phase_snapshot_id: UUID
    task_type: ContextTaskType
    sections: tuple[ContextSection, ...]
    source_record_ids: tuple[str, ...] = ()
    omitted_sections: tuple[str, ...] = ()
    token_estimate: int = Field(ge=0)
    package_hash: str = Field(min_length=1, max_length=128)
    created_at: datetime
