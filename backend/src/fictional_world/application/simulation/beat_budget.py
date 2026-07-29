"""Bounded reaction-beat budgets for scene categories."""

from __future__ import annotations

from enum import StrEnum


class SceneType(StrEnum):
    """Stable scene categories used by deterministic scene assembly."""

    SOLO_ACTION = "solo_action"
    SOCIAL_INTERACTION = "social_interaction"
    DIALOGUE = "dialogue"
    NEGOTIATION = "negotiation"
    TRAVEL = "travel"
    INVESTIGATION = "investigation"
    RESOURCE_CONFLICT = "resource_conflict"
    COMBAT = "combat"
    NONLETHAL_CONFLICT = "nonlethal_conflict"
    MAGIC_RITUAL = "magic_ritual"
    WORK_OR_TRAINING = "work_or_training"
    WORLD_EVENT_RESPONSE = "world_event_response"
    BACKGROUND = "background"
    NPC_BATCH = "npc_batch"


# Absolute hard maximum from handbook ``05`` §9.4 / ``07`` §12.3.
HARD_MAX_BEATS = 12


def beat_budget_for(scene_type: SceneType | str, participant_count: int) -> int:
    """Return the scene's mechanical beat cap, always clamped to ``1..12``.

    Stage 2 handbook ``27`` S2-SIM-002 budgets (expressed as beats):

    - two-person conversation: 2 exchange rounds → 4 beats;
    - group conversation: 6 total character beats;
    - negotiation: 1 proposal + 1 response per participant (+ Stage 1 closing);
    - nonlethal conflict: 3 attempt/reaction exchanges → 6 beats;
    - background NPC / NPC batch: 1 compact group beat.
    """

    if participant_count < 0:
        raise ValueError("participant_count cannot be negative")

    normalized_type = _normalize_type(scene_type)
    if normalized_type in {
        SceneType.SOLO_ACTION,
        SceneType.BACKGROUND,
        SceneType.NPC_BATCH,
        "background_npc",
        "background_npc_response",
    }:
        budget = 1
    elif normalized_type in {
        SceneType.SOCIAL_INTERACTION,
        SceneType.DIALOGUE,
        "social",
        "two_person_conversation",
        "group_conversation",
    }:
        # Two-person: 2 exchange rounds (4 beats). Group: 6 total beats.
        budget = 4 if participant_count == 2 else 6
    elif normalized_type == SceneType.NEGOTIATION:
        # 1 proposal + 1 response per participant, plus one closing beat (07 §12.3).
        budget = (participant_count * 2) + 1
    elif normalized_type in {SceneType.COMBAT, SceneType.NONLETHAL_CONFLICT}:
        # 3 attempt/reaction exchanges before continuation.
        budget = 6
    elif normalized_type in {SceneType.INVESTIGATION, SceneType.MAGIC_RITUAL}:
        budget = participant_count + 1
    else:
        budget = participant_count
    return max(1, min(HARD_MAX_BEATS, budget))


def exchange_rounds_for(scene_type: SceneType | str, participant_count: int) -> int:
    """Return handbook exchange-round count where applicable (else beat count)."""

    normalized_type = _normalize_type(scene_type)
    if (
        normalized_type
        in {
            SceneType.SOCIAL_INTERACTION,
            SceneType.DIALOGUE,
            "social",
            "two_person_conversation",
        }
        and participant_count == 2
    ):
        return 2
    if normalized_type in {SceneType.COMBAT, SceneType.NONLETHAL_CONFLICT}:
        return 3
    return beat_budget_for(scene_type, participant_count)


def _normalize_type(scene_type: SceneType | str) -> str:
    if isinstance(scene_type, SceneType):
        return scene_type.value
    return scene_type.strip().casefold()


__all__ = [
    "HARD_MAX_BEATS",
    "SceneType",
    "beat_budget_for",
    "exchange_rounds_for",
]
