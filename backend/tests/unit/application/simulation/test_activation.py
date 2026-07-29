"""Unit tests for deterministic character activation."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest

from fictional_world.application.simulation.activation import (
    EligibilityStatus,
    evaluate_activation,
)
from fictional_world.domain.characters.records import CharacterStateRecord


def _state(life_status: str) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=UUID(int=1),
        location_id=UUID(int=2),
        life_status=life_status,
        stamina=Decimal("80"),
        mana=Decimal("20"),
        energy=Decimal("70"),
        hunger=Decimal("10"),
        pain=Decimal("0"),
        stress=Decimal("10"),
        social_need=Decimal("20"),
        valence=Decimal("0.2"),
        arousal=Decimal("0.1"),
        dominance=Decimal("0.1"),
        current_card_version_id=UUID(int=3),
        version=0,
    )


def test_alive_character_is_eligible() -> None:
    status, reason = evaluate_activation(_state("alive"))

    assert status is EligibilityStatus.ELIGIBLE
    assert reason == "character can choose a primary action"


@pytest.mark.parametrize(
    ("life_status", "expected_status", "expected_reason"),
    [
        ("dead", EligibilityStatus.SKIPPED_DEAD, "character is dead"),
        (
            "unconscious",
            EligibilityStatus.SKIPPED_UNCONSCIOUS,
            "character is unconscious",
        ),
    ],
)
def test_incapacitated_character_has_explicit_skip_status(
    life_status: str,
    expected_status: EligibilityStatus,
    expected_reason: str,
) -> None:
    assert evaluate_activation(_state(life_status)) == (expected_status, expected_reason)
