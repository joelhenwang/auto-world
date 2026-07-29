"""Persistent Activity state machine and route travel progress (S2-SIM-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.continuity.persistence import (
    ActivityPersistenceRecord,
    RoutePersistenceRecord,
    TravelProgressPersistenceRecord,
)
from fictional_world.domain.continuity.statuses import ActivityStatus, TravelProgressStatus

# Progress fraction considered "same location" for encounter detection.
DEFAULT_ENCOUNTER_PROXIMITY = Decimal("0.15")


class ActivityError(DomainError):
    """Raised when an activity transition is illegal."""


class ActivityTickResult(StrictContract):
    activity: ActivityPersistenceRecord
    travel: TravelProgressPersistenceRecord | None = None
    arrived: bool = False
    interrupted: bool = False
    distance_delta: Decimal = Field(default=Decimal("0"))
    modifier: Decimal = Field(default=Decimal("1"))


class TravelEncounter(StrictContract):
    """Two travelers whose route progress overlaps closely enough to meet."""

    left_activity_id: UUID
    right_activity_id: UUID
    left_owner_id: UUID
    right_owner_id: UUID
    route_id: UUID
    proximity: Decimal


class TravelerSnapshot(StrictContract):
    """Minimal travel state for intersection checks (no omniscient extras)."""

    activity_id: UUID
    owner_entity_id: UUID
    route_id: UUID
    origin_location_id: UUID
    destination_location_id: UUID
    progress: Decimal = Field(ge=0, le=1)
    is_bidirectional: bool = True


def start_activity(
    *,
    activity_id: UUID,
    world_id: UUID,
    owner_entity_id: UUID,
    activity_type: str,
    started_phase_index: int,
    origin_location_id: UUID | None = None,
    destination_location_id: UUID | None = None,
    route_id: UUID | None = None,
    expected_end_phase_index: int | None = None,
    interruption_conditions: dict[str, object] | None = None,
    activity_payload: dict[str, object] | None = None,
) -> ActivityPersistenceRecord:
    """Create an active activity; travel activities require a route_id."""

    normalized_type = activity_type.strip().casefold()
    if normalized_type == "travel" and route_id is None:
        raise ActivityError("travel activity requires route_id")
    return ActivityPersistenceRecord(
        id=activity_id,
        world_id=world_id,
        owner_entity_id=owner_entity_id,
        activity_type=normalized_type,
        status=ActivityStatus.ACTIVE.value,
        origin_location_id=origin_location_id,
        destination_location_id=destination_location_id,
        route_id=route_id,
        started_phase_index=started_phase_index,
        expected_end_phase_index=expected_end_phase_index,
        progress=Decimal("0"),
        interruption_conditions=dict(interruption_conditions or {}),
        activity_payload=dict(activity_payload or {}),
        version=0,
    )


def start_travel_progress(
    *,
    activity: ActivityPersistenceRecord,
    route: RoutePersistenceRecord,
    absolute_phase_index: int,
) -> TravelProgressPersistenceRecord:
    """Initialize travel_progress for a newly started travel activity."""

    if activity.activity_type != "travel":
        raise ActivityError("travel progress requires activity_type=travel")
    if activity.route_id != route.id:
        raise ActivityError("activity route_id does not match route")
    if route.status.strip().casefold() != "active":
        raise ActivityError("cannot start travel on inactive route")
    return TravelProgressPersistenceRecord(
        activity_id=activity.id,
        route_id=route.id,
        distance_completed=Decimal("0"),
        phases_elapsed=0,
        current_segment_index=0,
        last_tick_phase_index=absolute_phase_index,
        status=TravelProgressStatus.IN_PROGRESS.value,
        version=0,
    )


def travel_modifier(
    *,
    world_random_seed: int,
    absolute_phase_index: int,
    route: RoutePersistenceRecord,
    weather_factor: Decimal = Decimal("1"),
) -> Decimal:
    """Deterministic travel speed modifier from world seed, phase, and route.

    Range is approximately ``[0.85, 1.15]`` before weather. Weather multiplies
    the result and is clamped to ``[0.5, 1.5]``.
    """

    material = (
        f"{world_random_seed}:{absolute_phase_index}:{route.id}:"
        f"{route.danger_level}:{','.join(route.terrain_tags)}"
    )
    digest = 0
    for index, char in enumerate(material.encode("utf-8")):
        digest = (digest * 131 + char + index * 17) & 0xFFFFFFFF
    # Map to [0, 1] then to [0.85, 1.15].
    unit = Decimal(digest % 10_000) / Decimal(10_000)
    base = Decimal("0.85") + unit * Decimal("0.30")
    seasonal = _seasonal_modifier(route)
    combined = base * seasonal * weather_factor
    if combined < Decimal("0.5"):
        return Decimal("0.5")
    if combined > Decimal("1.5"):
        return Decimal("1.5")
    return combined.quantize(Decimal("0.0001"))


def advance_travel(
    *,
    activity: ActivityPersistenceRecord,
    travel: TravelProgressPersistenceRecord,
    route: RoutePersistenceRecord,
    absolute_phase_index: int,
    world_random_seed: int,
    weather_factor: Decimal = Decimal("1"),
) -> ActivityTickResult:
    """Advance one phase of route travel; complete on arrival.

    Restart-safe: identical inputs yield identical outputs. Does not invent
    catch-up ticks for offline time — callers must invoke once per phase.
    """

    if activity.status != ActivityStatus.ACTIVE.value:
        raise ActivityError(f"cannot advance activity in status {activity.status}")
    if travel.status != TravelProgressStatus.IN_PROGRESS.value:
        raise ActivityError(f"cannot advance travel in status {travel.status}")
    if route.status.strip().casefold() != "active":
        return invalidate_for_inactive_route(
            activity=activity,
            travel=travel,
            route=route,
            absolute_phase_index=absolute_phase_index,
        )

    modifier = travel_modifier(
        world_random_seed=world_random_seed,
        absolute_phase_index=absolute_phase_index,
        route=route,
        weather_factor=weather_factor,
    )
    base_step = route.distance_units / Decimal(route.base_duration_phases)
    distance_delta = (base_step * modifier).quantize(Decimal("0.0001"))
    new_distance = travel.distance_completed + distance_delta
    arrived = new_distance >= route.distance_units
    if arrived:
        new_distance = route.distance_units
    progress = (
        Decimal("1")
        if route.distance_units == 0
        else (new_distance / route.distance_units).quantize(Decimal("0.0001"))
    )
    if progress > Decimal("1"):
        progress = Decimal("1")

    new_travel = travel.model_copy(
        update={
            "distance_completed": new_distance,
            "phases_elapsed": travel.phases_elapsed + 1,
            "current_segment_index": travel.current_segment_index,
            "last_tick_phase_index": absolute_phase_index,
            "status": (
                TravelProgressStatus.ARRIVED.value
                if arrived
                else TravelProgressStatus.IN_PROGRESS.value
            ),
            "version": travel.version + 1,
        }
    )
    if arrived:
        new_activity = complete_activity(activity, progress=Decimal("1"))
    else:
        new_activity = activity.model_copy(
            update={
                "progress": progress,
                "version": activity.version + 1,
            }
        )
    return ActivityTickResult(
        activity=new_activity,
        travel=new_travel,
        arrived=arrived,
        interrupted=False,
        distance_delta=distance_delta,
        modifier=modifier,
    )


def advance_activity(
    *,
    activity: ActivityPersistenceRecord,
    absolute_phase_index: int,
    progress_delta: Decimal | None = None,
    travel: TravelProgressPersistenceRecord | None = None,
    route: RoutePersistenceRecord | None = None,
    world_random_seed: int = 0,
    weather_factor: Decimal = Decimal("1"),
) -> ActivityTickResult:
    """Advance a non-travel or travel activity by one phase."""

    if activity.status != ActivityStatus.ACTIVE.value:
        raise ActivityError(f"cannot advance activity in status {activity.status}")

    if activity.activity_type == "travel":
        if travel is None or route is None:
            raise ActivityError("travel advance requires travel progress and route")
        return advance_travel(
            activity=activity,
            travel=travel,
            route=route,
            absolute_phase_index=absolute_phase_index,
            world_random_seed=world_random_seed,
            weather_factor=weather_factor,
        )

    delta = progress_delta if progress_delta is not None else Decimal("0.25")
    if delta <= 0:
        raise ActivityError("progress_delta must be positive")
    new_progress = activity.progress + delta
    completed = new_progress >= Decimal("1")
    if completed:
        return ActivityTickResult(
            activity=complete_activity(activity, progress=Decimal("1")),
            travel=None,
            arrived=True,
            interrupted=False,
            distance_delta=Decimal("0"),
            modifier=Decimal("1"),
        )
    return ActivityTickResult(
        activity=activity.model_copy(
            update={
                "progress": new_progress.quantize(Decimal("0.0001")),
                "version": activity.version + 1,
            }
        ),
        travel=None,
        arrived=False,
        interrupted=False,
        distance_delta=Decimal("0"),
        modifier=Decimal("1"),
    )


def interrupt_activity(
    activity: ActivityPersistenceRecord,
    *,
    reason: str,
    travel: TravelProgressPersistenceRecord | None = None,
) -> ActivityTickResult:
    """Interrupt an active activity without inventing progress."""

    if activity.status != ActivityStatus.ACTIVE.value:
        raise ActivityError(f"cannot interrupt activity in status {activity.status}")
    conditions = dict(activity.interruption_conditions)
    conditions["last_interrupt_reason"] = reason
    new_activity = activity.model_copy(
        update={
            "status": ActivityStatus.INTERRUPTED.value,
            "interruption_conditions": conditions,
            "version": activity.version + 1,
        }
    )
    new_travel = None
    if travel is not None and travel.status == TravelProgressStatus.IN_PROGRESS.value:
        new_travel = travel.model_copy(
            update={
                "status": TravelProgressStatus.INTERRUPTED.value,
                "version": travel.version + 1,
            }
        )
    return ActivityTickResult(
        activity=new_activity,
        travel=new_travel,
        arrived=False,
        interrupted=True,
        distance_delta=Decimal("0"),
        modifier=Decimal("1"),
    )


def complete_activity(
    activity: ActivityPersistenceRecord,
    *,
    progress: Decimal = Decimal("1"),
) -> ActivityPersistenceRecord:
    if activity.status not in {
        ActivityStatus.ACTIVE.value,
        ActivityStatus.INTERRUPTED.value,
    }:
        raise ActivityError(f"cannot complete activity in status {activity.status}")
    return activity.model_copy(
        update={
            "status": ActivityStatus.COMPLETED.value,
            "progress": progress,
            "version": activity.version + 1,
        }
    )


def invalidate_for_inactive_route(
    *,
    activity: ActivityPersistenceRecord,
    travel: TravelProgressPersistenceRecord,
    route: RoutePersistenceRecord,
    absolute_phase_index: int,
) -> ActivityTickResult:
    """Route invalidation interrupts travel safely without fabricating arrival."""

    _ = absolute_phase_index
    if route.status.strip().casefold() == "active":
        raise ActivityError("route is still active; nothing to invalidate")
    conditions = dict(activity.interruption_conditions)
    conditions["last_interrupt_reason"] = "route_invalidated"
    conditions["invalidated_route_id"] = str(route.id)
    conditions["invalidated_route_status"] = route.status
    new_activity = activity.model_copy(
        update={
            "status": ActivityStatus.INVALIDATED.value,
            "interruption_conditions": conditions,
            "version": activity.version + 1,
        }
    )
    new_travel = travel.model_copy(
        update={
            "status": TravelProgressStatus.INVALIDATED.value,
            "version": travel.version + 1,
        }
    )
    return ActivityTickResult(
        activity=new_activity,
        travel=new_travel,
        arrived=False,
        interrupted=True,
        distance_delta=Decimal("0"),
        modifier=Decimal("1"),
    )


def detect_intersecting_travel(
    travelers: tuple[TravelerSnapshot, ...] | list[TravelerSnapshot],
    *,
    proximity_threshold: Decimal = DEFAULT_ENCOUNTER_PROXIMITY,
) -> tuple[TravelEncounter, ...]:
    """Detect pairwise meetings on the same (or reverse) route segment."""

    ordered = sorted(travelers, key=lambda item: (item.route_id.int, item.owner_entity_id.int))
    encounters: list[TravelEncounter] = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if left.owner_entity_id == right.owner_entity_id:
                continue
            if not _same_undirected_route(left, right):
                continue
            left_pos = _normalized_progress(left)
            right_pos = _normalized_progress(right)
            proximity = abs(left_pos - right_pos)
            if proximity <= proximity_threshold:
                encounters.append(
                    TravelEncounter(
                        left_activity_id=left.activity_id,
                        right_activity_id=right.activity_id,
                        left_owner_id=left.owner_entity_id,
                        right_owner_id=right.owner_entity_id,
                        route_id=left.route_id,
                        proximity=proximity.quantize(Decimal("0.0001")),
                    )
                )
    return tuple(encounters)


def _same_undirected_route(left: TravelerSnapshot, right: TravelerSnapshot) -> bool:
    if left.route_id == right.route_id:
        return True
    left_ends = {left.origin_location_id, left.destination_location_id}
    right_ends = {right.origin_location_id, right.destination_location_id}
    if left_ends != right_ends:
        return False
    return left.is_bidirectional and right.is_bidirectional


def _normalized_progress(traveler: TravelerSnapshot) -> Decimal:
    """Map progress onto a shared origin→destination axis using location UUID order."""

    if traveler.origin_location_id.int <= traveler.destination_location_id.int:
        return traveler.progress
    return Decimal("1") - traveler.progress


def _seasonal_modifier(route: RoutePersistenceRecord) -> Decimal:
    raw = route.seasonal_modifiers.get("speed")
    if raw is None:
        return Decimal("1")
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str, Decimal)):
        return Decimal("1")
    try:
        value = Decimal(str(raw))
    except ArithmeticError:
        return Decimal("1")
    if value <= 0:
        return Decimal("1")
    return value


__all__ = [
    "DEFAULT_ENCOUNTER_PROXIMITY",
    "ActivityError",
    "ActivityTickResult",
    "TravelEncounter",
    "TravelerSnapshot",
    "advance_activity",
    "advance_travel",
    "complete_activity",
    "detect_intersecting_travel",
    "interrupt_activity",
    "invalidate_for_inactive_route",
    "start_activity",
    "start_travel_progress",
    "travel_modifier",
]
