"""Observer eligibility matrix (S2-KNOW-001)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.application.knowledge import (
    ObserverPresence,
    classify_observer_eligibility,
    eligible_observers,
)
from fictional_world.domain.knowledge import ObserverEligibility


def _presence(**kwargs: object) -> ObserverPresence:
    base: dict[str, object] = {"character_id": uuid4()}
    base.update(kwargs)
    return ObserverPresence.model_validate(base)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, ObserverEligibility.ABSENT),
        (
            {"co_located": True, "line_of_sight": True, "hearing_range": True, "close_range": True},
            ObserverEligibility.DIRECT_WITNESS,
        ),
        (
            {
                "co_located": True,
                "line_of_sight": True,
                "hearing_range": True,
                "precise_close": True,
                "close_range": True,
            },
            ObserverEligibility.DIRECT_WITNESS,
        ),
        (
            {"co_located": True, "line_of_sight": True, "hearing_range": True},
            ObserverEligibility.PARTIAL,
        ),
        (
            {"hearing_range": True, "attention": True},
            ObserverEligibility.HEARING_ONLY,
        ),
        (
            {"co_located": True, "line_of_sight": True, "concealment_blocks_sight": True},
            ObserverEligibility.ABSENT,
        ),
        (
            {
                "co_located": True,
                "line_of_sight": True,
                "concealment_blocks_sight": True,
                "hearing_range": True,
            },
            ObserverEligibility.HEARING_ONLY,
        ),
        (
            {"eligibility_override": ObserverEligibility.PARTIAL},
            ObserverEligibility.PARTIAL,
        ),
    ],
)
def test_eligibility_matrix(kwargs: dict[str, object], expected: ObserverEligibility) -> None:
    assert classify_observer_eligibility(_presence(**kwargs)) is expected


@pytest.mark.unit
def test_absent_excluded_from_eligible_list() -> None:
    present = _presence(
        co_located=True,
        line_of_sight=True,
        hearing_range=True,
        close_range=True,
    )
    absent = _presence()
    result = eligible_observers([present, absent])
    assert len(result) == 1
    assert result[0][0].character_id == present.character_id
    assert result[0][1] is ObserverEligibility.DIRECT_WITNESS
