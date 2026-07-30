"""Visual prompt compiler — builds image prompt spec from committed scene state.

Handbook 16 §7; S4-IMG-002.

Characters do NOT author their own authoritative visual prompts (handbook §7).
Prompts are compiled deterministically from committed event/scene metadata
plus allowed visual profile constraints.

The result is a structured dict (ImagePromptSpecification) that the
application service attaches to the image_job.prompt_spec field before
enqueueing.  The dict is intentionally schemaless at this layer — downstream
services and workflow binding adapters consume it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ParticipantSpec:
    """Appearance info for one participant in a scene."""

    entity_id: UUID
    name: str
    role: str = "primary"
    position: str = ""
    expression: str = ""
    outfit_version: str | None = None
    visible_injuries: list[str] = field(default_factory=list)
    appearance_notes: str = ""


@dataclass(frozen=True)
class ScenePromptInput:
    """All facts needed to compile a prompt for one image job."""

    world_id: UUID
    source_event_id: UUID
    source_scene_id: UUID | None
    asset_class: str
    location_name: str
    location_notes: str
    time_of_day: str
    weather: str
    participants: list[ParticipantSpec] = field(default_factory=list)
    action_outcome: str = ""
    tone: str = ""
    camera: str = "medium shot"
    composition_notes: str = ""
    style_profile: dict[str, Any] = field(default_factory=dict)
    prohibited_additions: list[str] = field(default_factory=list)


def compile_prompt(inp: ScenePromptInput) -> dict[str, Any]:
    """Return a structured ImagePromptSpecification dict.

    This function is deterministic and pure — no I/O.
    """
    subject_specs = [
        {
            "entity_id": str(p.entity_id),
            "name": p.name,
            "role": p.role,
            "position": p.position,
            "expression": p.expression,
            "outfit_version": p.outfit_version,
            "visible_injuries": list(p.visible_injuries),
            "appearance_notes": p.appearance_notes,
        }
        for p in inp.participants
    ]

    positive_parts: list[str] = []
    if inp.location_name:
        positive_parts.append(inp.location_name)
    if inp.time_of_day:
        positive_parts.append(inp.time_of_day)
    if inp.weather:
        positive_parts.append(inp.weather)
    for p in inp.participants:
        if p.name:
            positive_parts.append(p.name)
        if p.expression:
            positive_parts.append(p.expression)
    if inp.action_outcome:
        positive_parts.append(inp.action_outcome)
    if inp.tone:
        positive_parts.append(inp.tone)
    if inp.camera:
        positive_parts.append(inp.camera)

    style_positive: str = inp.style_profile.get("positive_style", "")
    if style_positive:
        positive_parts.append(style_positive)

    style_negative: str = inp.style_profile.get("negative_style", "")
    negative_parts: list[str] = []
    if style_negative:
        negative_parts.append(style_negative)
    negative_parts.extend(inp.prohibited_additions)
    default_negatives = [
        "low quality",
        "blurry",
        "watermark",
        "text",
        "extra fingers",
        "deformed",
        "extra limbs",
    ]
    negative_parts.extend(default_negatives)

    return {
        "source_event_id": str(inp.source_event_id),
        "source_scene_id": str(inp.source_scene_id) if inp.source_scene_id else None,
        "asset_class": inp.asset_class,
        "subject_specs": subject_specs,
        "location": inp.location_name,
        "location_notes": inp.location_notes,
        "time_weather_lighting": f"{inp.time_of_day}, {inp.weather}",
        "interaction": inp.action_outcome,
        "camera": inp.camera,
        "composition": inp.composition_notes,
        "tone": inp.tone,
        "style_profile": inp.style_profile,
        "positive_prompt": ", ".join(p for p in positive_parts if p),
        "negative_prompt": ", ".join(p for p in negative_parts if p),
        "prohibited_additions": list(inp.prohibited_additions),
        "provenance": {
            "world_id": str(inp.world_id),
            "compiler_version": "1.0",
        },
    }
