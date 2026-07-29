"""Unit tests for S2-SIM-001 calendar, activation, activities, and travel."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest

from fictional_world.application.simulation.activation import (
    ActivationDecision,
    EligibilityStatus,
    SleepSchedule,
    evaluate_activation,
    evaluate_activation_decision,
)
from fictional_world.application.simulation.activity import (
    ActivityError,
    TravelerSnapshot,
    advance_activity,
    advance_travel,
    detect_intersecting_travel,
    interrupt_activity,
    invalidate_for_inactive_route,
    start_activity,
    start_travel_progress,
)
from fictional_world.application.simulation.request_estimate import estimate_phase_model_requests
from fictional_world.application.simulation.time import (
    STAGE2_PHASE_PROFILE,
    PhaseProfile,
    full_day_phase_sequence,
    is_phase_enabled,
    phase_profile_names,
    walk_full_day,
)
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.continuity.persistence import RoutePersistenceRecord
from fictional_world.domain.continuity.statuses import ActivityStatus, TravelProgressStatus
from fictional_world.domain.time.fictional_time import FictionalTime


def _state(
    *,
    life_status: str = "alive",
    character_id: int = 1,
    activity_id: UUID | None = None,
) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=UUID(int=character_id),
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
        active_activity_id=activity_id,
        current_card_version_id=UUID(int=3),
        version=0,
    )


def _route(
    *,
    route_id: int = 10,
    distance: str = "10",
    duration: int = 5,
    status: str = "active",
    origin: int = 100,
    destination: int = 200,
) -> RoutePersistenceRecord:
    return RoutePersistenceRecord(
        id=UUID(int=route_id),
        world_id=UUID(int=1),
        origin_location_id=UUID(int=origin),
        destination_location_id=UUID(int=destination),
        distance_units=Decimal(distance),
        base_duration_phases=duration,
        status=status,
        version=0,
    )


@pytest.mark.unit
def test_stage2_profile_includes_all_ten_phases() -> None:
    names = phase_profile_names(PhaseProfile.STAGE2)
    assert names == tuple(phase.value for phase in DayPhase)
    assert len(full_day_phase_sequence()) == 10
    assert full_day_phase_sequence() == STAGE2_PHASE_PROFILE
    for phase in DayPhase:
        assert is_phase_enabled(phase, profile=PhaseProfile.STAGE2)


@pytest.mark.unit
def test_full_day_phase_sequence_advances_day_at_midnight() -> None:
    start = FictionalTime(
        generation_index=1,
        world_day_index=1,
        phase=DayPhase.DAWN,
        absolute_phase_index=0,
    )
    clocks = walk_full_day(start)
    assert [clock.phase for clock in clocks[:10]] == list(DayPhase)
    assert clocks[10].phase is DayPhase.DAWN
    assert clocks[10].world_day_index == 2
    assert clocks[10].absolute_phase_index == 10


@pytest.mark.unit
def test_stage1_activation_compat_unchanged() -> None:
    assert evaluate_activation(_state())[0] is EligibilityStatus.ELIGIBLE
    assert evaluate_activation(_state(life_status="dead"))[0] is EligibilityStatus.SKIPPED_DEAD


@pytest.mark.unit
def test_sleeping_character_skipped_unless_woken() -> None:
    sleeping = evaluate_activation_decision(
        _state(),
        phase=DayPhase.NIGHT,
        consciousness_status="asleep",
    )
    assert sleeping.decision is ActivationDecision.SLEEP
    assert sleeping.requires_model is False

    woken = evaluate_activation_decision(
        _state(),
        phase=DayPhase.NIGHT,
        consciousness_status="asleep",
        interruption_candidate=True,
    )
    assert woken.decision is ActivationDecision.FULL_DECISION
    assert woken.requires_model is True


@pytest.mark.unit
def test_scheduled_sleep_uses_default_night_window() -> None:
    result = evaluate_activation_decision(_state(), phase=DayPhase.MIDNIGHT)
    assert result.decision is ActivationDecision.SLEEP

    morning = evaluate_activation_decision(_state(), phase=DayPhase.MORNING)
    assert morning.decision is ActivationDecision.FULL_DECISION


@pytest.mark.unit
def test_travel_continues_without_llm() -> None:
    activity = start_activity(
        activity_id=UUID(int=50),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=1),
        activity_type="travel",
        started_phase_index=0,
        route_id=UUID(int=10),
        origin_location_id=UUID(int=100),
        destination_location_id=UUID(int=200),
    )
    result = evaluate_activation_decision(
        _state(activity_id=activity.id),
        phase=DayPhase.MORNING,
        active_activity=activity,
    )
    assert result.decision is ActivationDecision.CONTINUE_ACTIVITY
    assert result.requires_model is False


@pytest.mark.unit
def test_dead_and_unconscious_are_skip() -> None:
    dead = evaluate_activation_decision(_state(life_status="dead"), phase=DayPhase.DAWN)
    assert dead.decision is ActivationDecision.SKIP
    unconscious = evaluate_activation_decision(
        _state(life_status="unconscious"),
        phase=DayPhase.DAWN,
    )
    assert unconscious.decision is ActivationDecision.SKIP


@pytest.mark.unit
def test_travel_advances_with_seed_modifier_and_restart_preserves_progress() -> None:
    route = _route(distance="10", duration=5)
    activity = start_activity(
        activity_id=UUID(int=50),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=1),
        activity_type="travel",
        started_phase_index=3,
        route_id=route.id,
        origin_location_id=route.origin_location_id,
        destination_location_id=route.destination_location_id,
    )
    travel = start_travel_progress(activity=activity, route=route, absolute_phase_index=3)

    first = advance_travel(
        activity=activity,
        travel=travel,
        route=route,
        absolute_phase_index=4,
        world_random_seed=42,
    )
    replay = advance_travel(
        activity=activity,
        travel=travel,
        route=route,
        absolute_phase_index=4,
        world_random_seed=42,
    )
    assert first.travel is not None
    assert replay.travel is not None
    assert first.travel.distance_completed == replay.travel.distance_completed
    assert first.travel.phases_elapsed == 1
    expected_progress = (first.travel.distance_completed / route.distance_units).quantize(
        Decimal("0.0001")
    )
    assert first.activity.progress == expected_progress
    assert first.modifier != Decimal("0")
    assert Decimal("0.5") <= first.modifier <= Decimal("1.5")

    second = advance_travel(
        activity=first.activity,
        travel=first.travel,
        route=route,
        absolute_phase_index=5,
        world_random_seed=42,
    )
    assert second.travel is not None
    assert second.travel.phases_elapsed == 2
    assert second.travel.distance_completed > first.travel.distance_completed


@pytest.mark.unit
def test_travel_completes_on_arrival() -> None:
    route = _route(distance="2", duration=1)
    activity = start_activity(
        activity_id=UUID(int=51),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=1),
        activity_type="travel",
        started_phase_index=0,
        route_id=route.id,
        origin_location_id=route.origin_location_id,
        destination_location_id=route.destination_location_id,
    )
    travel = start_travel_progress(activity=activity, route=route, absolute_phase_index=0)
    # weather_factor pushes speed to the clamp ceiling so one tick covers the route.
    result = advance_activity(
        activity=activity,
        absolute_phase_index=1,
        travel=travel,
        route=route,
        world_random_seed=7,
        weather_factor=Decimal("2"),
    )
    assert result.arrived is True
    assert result.activity.status == ActivityStatus.COMPLETED.value
    assert result.travel is not None
    assert result.travel.status == TravelProgressStatus.ARRIVED.value
    assert result.travel.distance_completed == route.distance_units


@pytest.mark.unit
def test_intersecting_travel_encounter_detection() -> None:
    left = TravelerSnapshot(
        activity_id=UUID(int=1),
        owner_entity_id=UUID(int=11),
        route_id=UUID(int=10),
        origin_location_id=UUID(int=100),
        destination_location_id=UUID(int=200),
        progress=Decimal("0.40"),
    )
    right = TravelerSnapshot(
        activity_id=UUID(int=2),
        owner_entity_id=UUID(int=12),
        route_id=UUID(int=10),
        origin_location_id=UUID(int=100),
        destination_location_id=UUID(int=200),
        progress=Decimal("0.45"),
    )
    distant = TravelerSnapshot(
        activity_id=UUID(int=3),
        owner_entity_id=UUID(int=13),
        route_id=UUID(int=10),
        origin_location_id=UUID(int=100),
        destination_location_id=UUID(int=200),
        progress=Decimal("0.90"),
    )
    encounters = detect_intersecting_travel((left, right, distant))
    assert len(encounters) == 1
    assert {encounters[0].left_owner_id, encounters[0].right_owner_id} == {
        UUID(int=11),
        UUID(int=12),
    }

    reverse = TravelerSnapshot(
        activity_id=UUID(int=4),
        owner_entity_id=UUID(int=14),
        route_id=UUID(int=99),
        origin_location_id=UUID(int=200),
        destination_location_id=UUID(int=100),
        progress=Decimal("0.55"),
        is_bidirectional=True,
    )
    reverse_meetings = detect_intersecting_travel((left, reverse))
    assert len(reverse_meetings) == 1


@pytest.mark.unit
def test_route_invalidation_interrupts_safely() -> None:
    route = _route(status="active")
    activity = start_activity(
        activity_id=UUID(int=60),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=1),
        activity_type="travel",
        started_phase_index=0,
        route_id=route.id,
        origin_location_id=route.origin_location_id,
        destination_location_id=route.destination_location_id,
    )
    travel = start_travel_progress(activity=activity, route=route, absolute_phase_index=0)
    mid = advance_travel(
        activity=activity,
        travel=travel,
        route=route,
        absolute_phase_index=1,
        world_random_seed=1,
    )
    assert mid.travel is not None
    saved_distance = mid.travel.distance_completed

    inactive = route.model_copy(update={"status": "blocked"})
    invalidated = invalidate_for_inactive_route(
        activity=mid.activity,
        travel=mid.travel,
        route=inactive,
        absolute_phase_index=2,
    )
    assert invalidated.interrupted is True
    assert invalidated.activity.status == ActivityStatus.INVALIDATED.value
    assert invalidated.travel is not None
    assert invalidated.travel.status == TravelProgressStatus.INVALIDATED.value
    assert invalidated.travel.distance_completed == saved_distance
    assert invalidated.activity.progress == mid.activity.progress
    assert invalidated.activity.interruption_conditions["last_interrupt_reason"] == (
        "route_invalidated"
    )

    via_advance = advance_travel(
        activity=mid.activity,
        travel=mid.travel,
        route=inactive,
        absolute_phase_index=2,
        world_random_seed=1,
    )
    assert via_advance.interrupted is True
    assert via_advance.travel is not None
    assert via_advance.travel.distance_completed == saved_distance


@pytest.mark.unit
def test_interrupt_activity_preserves_progress() -> None:
    activity = start_activity(
        activity_id=UUID(int=70),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=1),
        activity_type="train",
        started_phase_index=0,
    )
    advanced = advance_activity(
        activity=activity,
        absolute_phase_index=1,
        progress_delta=Decimal("0.30"),
    )
    interrupted = interrupt_activity(advanced.activity, reason="scene_conflict")
    assert interrupted.interrupted is True
    assert interrupted.activity.status == ActivityStatus.INTERRUPTED.value
    assert interrupted.activity.progress == Decimal("0.3000")


@pytest.mark.unit
def test_estimate_phase_model_requests_skips_non_decision_actors() -> None:
    travel = start_activity(
        activity_id=UUID(int=80),
        world_id=UUID(int=1),
        owner_entity_id=UUID(int=4),
        activity_type="travel",
        started_phase_index=0,
        route_id=UUID(int=10),
    )
    activations = (
        evaluate_activation_decision(_state(character_id=1), phase=DayPhase.MORNING),
        evaluate_activation_decision(
            _state(character_id=2),
            phase=DayPhase.NIGHT,
            consciousness_status="asleep",
        ),
        evaluate_activation_decision(
            _state(life_status="dead", character_id=3),
            phase=DayPhase.DAWN,
        ),
        evaluate_activation_decision(
            _state(character_id=4, activity_id=travel.id),
            phase=DayPhase.NOON,
            active_activity=travel,
        ),
    )
    estimate = estimate_phase_model_requests(
        activations,
        director_call_planned=True,
        ambiguous_scene_count=1,
    )
    assert estimate.character_decision_requests == 1
    assert estimate.director_requests == 1
    assert estimate.resolver_requests == 1
    assert estimate.total_mandatory == 3


@pytest.mark.unit
def test_custom_sleep_schedule_wake_rules() -> None:
    schedule = SleepSchedule(
        sleep_phases=(DayPhase.EVENING, DayPhase.NIGHT),
        wake_phase=DayPhase.DAWN,
    )
    evening = evaluate_activation_decision(
        _state(),
        phase=DayPhase.EVENING,
        sleep_schedule=schedule,
    )
    assert evening.decision is ActivationDecision.SLEEP
    dawn = evaluate_activation_decision(
        _state(),
        phase=DayPhase.DAWN,
        sleep_schedule=schedule,
    )
    assert dawn.decision is ActivationDecision.FULL_DECISION


@pytest.mark.unit
def test_travel_requires_route() -> None:
    with pytest.raises(ActivityError, match="route_id"):
        start_activity(
            activity_id=UUID(int=90),
            world_id=UUID(int=1),
            owner_entity_id=UUID(int=1),
            activity_type="travel",
            started_phase_index=0,
        )
