"""Fictional time value object (handbook ``05`` field names)."""

from __future__ import annotations

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import DayPhase


class FictionalTime(StrictContract):
    generation_index: int = Field(ge=1, le=3)
    world_day_index: int = Field(ge=1)
    phase: DayPhase
    absolute_phase_index: int = Field(ge=0)
    calendar_label: str | None = Field(default=None, max_length=200)
