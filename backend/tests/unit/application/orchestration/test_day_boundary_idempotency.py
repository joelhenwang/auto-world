"""Day-boundary restart / finalize idempotency (S2-QA-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fictional_world.application.memory.daily_consolidation import (
    consolidate_day,
    day_consolidation_idempotency_key,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord


def _obs(*, observer_id, summary: str) -> ObservationPersistenceRecord:
    return ObservationPersistenceRecord(
        id=uuid4(),
        world_event_id=uuid4(),
        observer_id=observer_id,
        observation_type="scene",
        perceived_summary=summary,
        perceived_facts={"note": summary},
        omitted_fact_keys=(),
        confidence=Decimal("0.80"),
        visibility_reason="direct_witness",
        source_sense_tags=("sight",),
        content_hash=uuid4().hex,
    )


@pytest.mark.unit
@pytest.mark.fault
def test_process_restart_at_day_boundary_reuses_day_run() -> None:
    """Simulate process death after day finalize then retry with the same prior.

    The day-consolidation idempotency key must address the same day_run; summaries
    and diaries must not duplicate across the restart boundary.
    """

    world_id = uuid4()
    owner = uuid4()
    day_index = 2
    obs = _obs(observer_id=owner, summary="Evening bells marked the end of day two.")

    completed = consolidate_day(
        world_id=world_id,
        day_index=day_index,
        character_ids=[owner],
        observations=[obs],
    )
    assert completed.day_run.status == "completed"
    assert completed.day_run.idempotency_key == day_consolidation_idempotency_key(
        world_id, day_index
    )
    assert completed.reused_prior is False
    assert completed.daily_audit.hard_violation_count == 0

    # Process restart: caller reloads the completed day_run and retries finalize.
    restarted = consolidate_day(
        world_id=world_id,
        day_index=day_index,
        character_ids=[owner],
        observations=[obs],
        prior=completed,
    )
    assert restarted.reused_prior is True
    assert restarted.day_run.id == completed.day_run.id
    assert restarted.day_run.idempotency_key == completed.day_run.idempotency_key
    assert restarted.characters[0].summary.id == completed.characters[0].summary.id
    assert restarted.characters[0].diary.id == completed.characters[0].diary.id
    assert restarted.daily_audit.id == completed.daily_audit.id
    assert restarted.daily_audit.hard_violation_count == 0


@pytest.mark.unit
def test_day_consolidation_keys_are_stable_per_world_day() -> None:
    world_a = uuid4()
    world_b = uuid4()
    assert day_consolidation_idempotency_key(world_a, 0) == f"day-consolidation:{world_a}:0"
    assert day_consolidation_idempotency_key(world_a, 0) == day_consolidation_idempotency_key(
        world_a, 0
    )
    assert day_consolidation_idempotency_key(world_a, 1) != day_consolidation_idempotency_key(
        world_a, 0
    )
    assert day_consolidation_idempotency_key(world_a, 0) != day_consolidation_idempotency_key(
        world_b, 0
    )
