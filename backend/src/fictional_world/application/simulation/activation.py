"""Deterministic character activation rules (Stage 1 + Stage 2)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import DayPhase
from fictional_world.domain.continuity.persistence import ActivityPersistenceRecord
from fictional_world.domain.continuity.statuses import ActivityStatus
from fictional_world.domain.time.calendar import PHASE_ORDER

# Non-decision multi-phase activities that continue without a model call.
CONTINUATION_ACTIVITY_TYPES: frozenset[str] = frozenset(
    {
        "travel",
        "train",
        "work",
        "craft",
        "rest",
        "study",
    }
)

DEFAULT_SLEEP_PHASES: frozenset[DayPhase] = frozenset({DayPhase.NIGHT, DayPhase.MIDNIGHT})
DEFAULT_WAKE_PHASE: DayPhase = DayPhase.DAWN


class EligibilityStatus(StrEnum):
    """Whether a character receives a primary decision request (Stage 1)."""

    ELIGIBLE = "eligible"
    SKIPPED_DEAD = "skipped_dead"
    SKIPPED_UNCONSCIOUS = "skipped_unconscious"


class ActivationDecision(StrEnum):
    """Stage 2 activation outcome for one character in one phase."""

    FULL_DECISION = "full_decision"
    SLEEP = "sleep"
    CONTINUE_ACTIVITY = "continue_activity"
    SKIP = "skip"


class SleepSchedule(StrictContract):
    """Per-character or world-default sleep window on the detailed calendar."""

    sleep_phases: tuple[DayPhase, ...] = Field(
        default=(DayPhase.NIGHT, DayPhase.MIDNIGHT),
        min_length=1,
    )
    wake_phase: DayPhase = DayPhase.DAWN

    def includes(self, phase: DayPhase | str) -> bool:
        name = phase if isinstance(phase, DayPhase) else DayPhase(str(phase).strip().casefold())
        return name in self.sleep_phases


class ActivationResult(StrictContract):
    decision: ActivationDecision
    reason: str = Field(min_length=1, max_length=500)
    requires_model: bool


def default_sleep_schedule() -> SleepSchedule:
    return SleepSchedule(
        sleep_phases=tuple(phase for phase in PHASE_ORDER if phase in DEFAULT_SLEEP_PHASES),
        wake_phase=DEFAULT_WAKE_PHASE,
    )


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


def evaluate_activation_decision(
    character_state: CharacterStateRecord,
    *,
    phase: DayPhase | str,
    active_activity: ActivityPersistenceRecord | None = None,
    sleep_schedule: SleepSchedule | None = None,
    interruption_candidate: bool = False,
    decision_point: bool = False,
    consciousness_status: str | None = None,
) -> ActivationResult:
    """Decide SLEEP / CONTINUE_ACTIVITY / FULL_DECISION / SKIP for Stage 2.

    Priority (handbook ``07`` §8 / ``05`` §8.3):

    1. dead or permanently incapable → SKIP
    2. unconscious with no recovery choice → SKIP
    3. asleep / scheduled sleep without interruption → SLEEP
    4. continuing non-decision activity → CONTINUE_ACTIVITY
    5. otherwise → FULL_DECISION
    """

    life_status = character_state.life_status.strip().casefold()
    if life_status == "dead":
        return ActivationResult(
            decision=ActivationDecision.SKIP,
            reason="character is dead",
            requires_model=False,
        )
    if life_status == "unconscious":
        return ActivationResult(
            decision=ActivationDecision.SKIP,
            reason="character is unconscious",
            requires_model=False,
        )

    phase_value = phase if isinstance(phase, DayPhase) else DayPhase(str(phase).strip().casefold())
    schedule = sleep_schedule if sleep_schedule is not None else default_sleep_schedule()
    consciousness = (
        consciousness_status.strip().casefold() if consciousness_status is not None else life_status
    )
    asleep = consciousness in {"asleep", "drowsy"} or (
        active_activity is not None
        and active_activity.status == ActivityStatus.ACTIVE.value
        and active_activity.activity_type.strip().casefold() == "sleep"
    )
    scheduled_sleep = schedule.includes(phase_value) and not _is_wake_phase(
        phase_value, schedule.wake_phase
    )

    if (asleep or scheduled_sleep) and not interruption_candidate:
        return ActivationResult(
            decision=ActivationDecision.SLEEP,
            reason=(
                "asleep with no interruption candidate"
                if asleep
                else f"scheduled sleep during {phase_value.value}"
            ),
            requires_model=False,
        )

    if (
        active_activity is not None
        and active_activity.status == ActivityStatus.ACTIVE.value
        and not decision_point
        and not interruption_candidate
    ):
        activity_type = active_activity.activity_type.strip().casefold()
        if activity_type == "sleep":
            return ActivationResult(
                decision=ActivationDecision.SLEEP,
                reason="continuing sleep activity",
                requires_model=False,
            )
        if activity_type in CONTINUATION_ACTIVITY_TYPES:
            return ActivationResult(
                decision=ActivationDecision.CONTINUE_ACTIVITY,
                reason=f"continuing {activity_type} without decision point",
                requires_model=False,
            )

    if interruption_candidate and (asleep or scheduled_sleep):
        return ActivationResult(
            decision=ActivationDecision.FULL_DECISION,
            reason="wake interruption requires a decision",
            requires_model=True,
        )

    return ActivationResult(
        decision=ActivationDecision.FULL_DECISION,
        reason="character can choose a primary action",
        requires_model=True,
    )


def _is_wake_phase(phase: DayPhase, wake_phase: DayPhase) -> bool:
    return phase is wake_phase


__all__ = [
    "CONTINUATION_ACTIVITY_TYPES",
    "DEFAULT_SLEEP_PHASES",
    "DEFAULT_WAKE_PHASE",
    "ActivationDecision",
    "ActivationResult",
    "EligibilityStatus",
    "SleepSchedule",
    "default_sleep_schedule",
    "evaluate_activation",
    "evaluate_activation_decision",
]
