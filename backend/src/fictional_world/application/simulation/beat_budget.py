"""Bounded reaction-beat budgets for scene categories."""

from __future__ import annotations

from enum import StrEnum


class SceneType(StrEnum):
    """Stable scene categories used by deterministic Stage 1 assembly."""

    SOLO_ACTION = "solo_action"
    SOCIAL_INTERACTION = "social_interaction"
    DIALOGUE = "dialogue"
    NEGOTIATION = "negotiation"
    TRAVEL = "travel"
    INVESTIGATION = "investigation"
    RESOURCE_CONFLICT = "resource_conflict"
    COMBAT = "combat"
    MAGIC_RITUAL = "magic_ritual"
    WORK_OR_TRAINING = "work_or_training"
    WORLD_EVENT_RESPONSE = "world_event_response"
    BACKGROUND = "background"


def beat_budget_for(scene_type: SceneType | str, participant_count: int) -> int:
    """Return the scene's mechanical beat cap, always clamped to ``1..12``."""

    if participant_count < 0:
        raise ValueError("participant_count cannot be negative")

    normalized_type = (
        scene_type.value if isinstance(scene_type, SceneType) else scene_type.strip().casefold()
    )
    if normalized_type in {SceneType.SOLO_ACTION, SceneType.BACKGROUND}:
        budget = 1
    elif normalized_type in {
        SceneType.SOCIAL_INTERACTION,
        SceneType.DIALOGUE,
        "social",
    }:
        budget = 4 if participant_count == 2 else 6
    elif normalized_type == SceneType.NEGOTIATION:
        budget = (participant_count * 2) + 1
    elif normalized_type == SceneType.COMBAT:
        budget = 6
    elif normalized_type in {SceneType.INVESTIGATION, SceneType.MAGIC_RITUAL}:
        budget = participant_count + 1
    else:
        budget = participant_count
    return max(1, min(12, budget))


__all__ = ["SceneType", "beat_budget_for"]
