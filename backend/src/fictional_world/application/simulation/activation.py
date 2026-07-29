"""Deterministic Stage 1 character activation rules."""

from __future__ import annotations

from enum import StrEnum

from fictional_world.domain.characters.records import CharacterStateRecord


class EligibilityStatus(StrEnum):
    """Whether a character receives a primary decision request."""

    ELIGIBLE = "eligible"
    SKIPPED_DEAD = "skipped_dead"
    SKIPPED_UNCONSCIOUS = "skipped_unconscious"


def evaluate_activation(
    character_state: CharacterStateRecord,
) -> tuple[EligibilityStatus, str]:
    """Return deterministic Stage 1 eligibility and an audit-friendly reason."""

    life_status = character_state.life_status.strip().casefold()
    if life_status == "dead":
        return EligibilityStatus.SKIPPED_DEAD, "character is dead"
    if life_status == "unconscious":
        return EligibilityStatus.SKIPPED_UNCONSCIOUS, "character is unconscious"
    return EligibilityStatus.ELIGIBLE, "character can choose a primary action"


__all__ = ["EligibilityStatus", "evaluate_activation"]
