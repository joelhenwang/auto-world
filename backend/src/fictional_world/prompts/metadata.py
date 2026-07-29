"""Validated metadata for versioned prompt assets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fictional_world.application.models.roles import ModelRole


class PromptMeta(BaseModel):
    """Immutable metadata describing one registered prompt version."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    prompt_id: str = Field(pattern=r"^[a-z][a-z0-9_]*_v[1-9][0-9]*$")
    role: ModelRole
    version: int = Field(ge=1)
    status: Literal["active", "inactive"] = "active"
    compatible_schema: str = Field(min_length=3, max_length=100)
    input_sections: tuple[str, ...] = Field(min_length=1)
    sampling_profile: str = Field(pattern=r"^[a-z][a-z0-9_]*_v[1-9][0-9]*$")

    @field_validator("input_sections")
    @classmethod
    def validate_input_sections(cls, sections: tuple[str, ...]) -> tuple[str, ...]:
        """Require unique, normalized Jinja variable names."""

        if len(set(sections)) != len(sections):
            raise ValueError("input_sections must be unique")
        if any(not section.isidentifier() or section.startswith("_") for section in sections):
            raise ValueError("input_sections must contain public Python identifiers")
        return sections
