"""Unit tests for Stage 3 arc / hook / faction / settlement helpers (S3-WORLD-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.domain.common.errors import InvalidAction, InvalidStateTransition
from fictional_world.domain.continuity.persistence import HookPersistenceRecord
from fictional_world.domain.stage3.persistence import (
    ArcPersistenceRecord,
    FactionPersistenceRecord,
)
from fictional_world.domain.world import (
    DEFAULT_PLOT_ARMOUR_BIAS,
    activate_arc,
    activate_hook,
    advance_arc_progress,
    apply_faction_daily_update,
    apply_settlement_indicator_update,
    can_activate_major_arc,
    can_activate_secondary_hook,
    close_arc,
    close_hook,
    count_active_major_arcs,
    count_active_secondary_hooks,
    default_plot_armour_bias,
    expire_hook,
)


def _arc(
    world_id: UUID,
    *,
    scope: str = "major",
    status: str = "dormant",
    progress: Decimal = Decimal("0"),
) -> ArcPersistenceRecord:
    return ArcPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        arc_key=f"arc-{uuid4().hex[:8]}",
        title="Caravan disappearances",
        arc_scope=scope,
        status=status,
        premise="Missing caravans threaten trade.",
        objective="Establish cause and stabilize routes.",
        progress=progress,
    )


def _hook(world_id: UUID, *, status: str = "dormant") -> HookPersistenceRecord:
    return HookPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        hook_key=f"hook-{uuid4().hex[:8]}",
        title="Marsh rumour",
        status=status,
        premise="A marsh guide mentions lights after dark.",
    )


def _faction(world_id: UUID) -> FactionPersistenceRecord:
    return FactionPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        faction_key="embervale_guild",
        name="Embervale Traders Guild",
        faction_type="guild",
        resources={"coin": "100", "influence": "0.4"},
        goals={"indicators": {"stability": "0.5"}},
        plans={"progress": "0.1"},
        plot_armour_bias=DEFAULT_PLOT_ARMOUR_BIAS,
    )


@pytest.fixture
def world_id() -> UUID:
    return uuid4()


def test_one_major_active_arc_enforced(world_id: UUID) -> None:
    active = _arc(world_id, status="active")
    dormant = _arc(world_id, status="dormant")
    arcs = (active, dormant)

    assert count_active_major_arcs(arcs) == 1
    assert can_activate_major_arc(arcs, candidate=active) is True
    assert can_activate_major_arc(arcs, candidate=dormant) is False

    with pytest.raises(InvalidAction, match="major arc slot"):
        activate_arc(dormant, arcs, start_phase_index=10)

    # Closing frees the slot.
    closed = close_arc(active, outcome="resolved", end_phase_index=20)
    assert closed.status == "resolved"
    remaining = (closed, dormant)
    assert can_activate_major_arc(remaining, candidate=dormant) is True
    activated = activate_arc(dormant, remaining, start_phase_index=21)
    assert activated.status == "active"
    assert activated.start_phase_index == 21


def test_secondary_arc_does_not_consume_major_slot(world_id: UUID) -> None:
    major = _arc(world_id, status="active", scope="major")
    secondary = _arc(world_id, status="dormant", scope="secondary")
    activated = activate_arc(secondary, (major, secondary), start_phase_index=5)
    assert activated.status == "active"
    assert activated.arc_scope == "secondary"
    assert count_active_major_arcs((major, activated)) == 1


def test_advance_and_close_arc(world_id: UUID) -> None:
    arc = _arc(world_id, status="active", progress=Decimal("0.2"))
    advanced = advance_arc_progress(arc, delta=Decimal("0.3"), phase_index=12)
    assert advanced.progress == Decimal("0.5")
    assert advanced.milestones["last_progress_phase_index"] == 12
    capped = advance_arc_progress(advanced, delta=Decimal("0.9"))
    assert capped.progress == Decimal("1")

    dormant = _arc(world_id, status="dormant")
    with pytest.raises(InvalidAction, match="cannot advance"):
        advance_arc_progress(dormant, delta=Decimal("0.1"))

    closed = close_arc(capped, outcome="failed", end_phase_index=30)
    assert closed.status == "failed"
    assert closed.end_phase_index == 30
    with pytest.raises(InvalidStateTransition):
        close_arc(closed, outcome="resolved", end_phase_index=31)


def test_hook_activate_limit_close_and_expire(world_id: UUID) -> None:
    h1 = _hook(world_id, status="active")
    h2 = _hook(world_id, status="active")
    h3 = _hook(world_id, status="dormant")
    hooks = (h1, h2, h3)

    assert count_active_secondary_hooks(hooks) == 2
    assert can_activate_secondary_hook(hooks, candidate=h3) is False
    with pytest.raises(InvalidAction, match="secondary hook slots"):
        activate_hook(h3, hooks)

    closed = close_hook(h1)
    assert closed.status == "resolved"
    freed = (closed, h2, h3)
    assert can_activate_secondary_hook(freed, candidate=h3) is True
    activated = activate_hook(h3, freed)
    assert activated.status == "active"

    expired = expire_hook(h2, cooldown_until_phase=40)
    assert expired.status == "abandoned"
    assert expired.cooldown_until_phase == 40
    # Idempotent expire on already-abandoned hook is allowed.
    again = expire_hook(expired)
    assert again.status == "abandoned"
    with pytest.raises(InvalidStateTransition):
        close_hook(expired)


def test_faction_daily_update_without_full_npc_sim(world_id: UUID) -> None:
    faction = _faction(world_id)
    focus_a = uuid4()
    focus_b = uuid4()
    bystander = uuid4()

    result = apply_faction_daily_update(
        faction,
        day_index=3,
        indicator_deltas={"stability": Decimal("-0.2"), "prosperity": Decimal("0.1")},
        resource_deltas={"coin": Decimal("-5")},
        focus_character_ids=(focus_a, focus_b),
        membership_character_ids=(focus_a, bystander),
        plan_progress_delta=Decimal("0.05"),
    )

    assert result.day_index == 3
    assert result.faction.plot_armour_bias == default_plot_armour_bias()
    assert result.faction.plot_armour_bias == Decimal("0")
    assert len(result.indicator_deltas) == 2
    stability = next(d for d in result.indicator_deltas if d.indicator_key == "stability")
    assert stability.next_value == Decimal("0.3")
    assert result.resource_deltas["coin"] == Decimal("-5")
    assert Decimal(str(result.faction.resources["coin"])) == Decimal("95")
    assert result.promote_causal_event is True
    assert result.affected_focus_character_ids == (focus_a,)

    # No focus overlap → no causal promotion; still updates aggregates.
    quiet = apply_faction_daily_update(
        faction,
        day_index=4,
        indicator_deltas={"stability": Decimal("0.05")},
        focus_character_ids=(focus_b,),
        membership_character_ids=(bystander,),
    )
    assert quiet.promote_causal_event is False
    assert quiet.affected_focus_character_ids == ()


def test_settlement_indicator_update(world_id: UUID) -> None:
    location_id = uuid4()
    first = apply_settlement_indicator_update(
        None,
        world_id=world_id,
        location_id=location_id,
        indicator_key="prosperity",
        day_index=1,
        delta=Decimal("0.4"),
    )
    assert first.value == Decimal("0.4")
    assert first.version == 0

    second = apply_settlement_indicator_update(
        first,
        world_id=world_id,
        location_id=location_id,
        indicator_key="prosperity",
        day_index=2,
        delta=Decimal("-0.1"),
    )
    assert second.value == Decimal("0.3")
    assert second.version == 1
    assert second.id == first.id
