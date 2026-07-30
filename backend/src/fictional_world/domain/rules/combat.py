"""Combat exchange resolution without HP (S3-RULES-003 / handbook ``10`` §10)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN, clamp_world_scale
from fictional_world.domain.rules.seeded import SeededRng


class CombatOutcomeClass(StrEnum):
    CLEAN_SUCCESS = "clean_success"
    SUCCESS_WITH_COST = "success_with_cost"
    PARTIAL_CONTACT = "partial_contact"
    STALEMATE = "stalemate"
    FAILED_ATTEMPT = "failed_attempt"
    COUNTERED = "countered"
    INTERRUPTED = "interrupted"
    CATASTROPHIC_FAILURE = "catastrophic_failure"


class CombatantSnapshot(StrictContract):
    """Sealed combatant inputs for one exchange (no HP)."""

    character_id: UUID
    capability: float = Field(ge=STAT_MIN, le=STAT_MAX)
    skill: float = Field(ge=STAT_MIN, le=STAT_MAX)
    preparation: float = Field(default=0.0, ge=0.0, le=1.0)
    terrain_advantage: float = Field(default=0.0, ge=-1.0, le=1.0)
    teamwork: float = Field(default=0.0, ge=0.0, le=1.0)
    morale: float = Field(default=0.5, ge=0.0, le=1.0)
    injury_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    surprise: float = Field(default=0.0, ge=0.0, le=1.0)
    stamina_ratio: float = Field(default=1.0, ge=0.0, le=1.0)


class CombatExchangeInput(StrictContract):
    attacker: CombatantSnapshot
    defender: CombatantSnapshot
    seed: int
    proposed_outcome: CombatOutcomeClass | None = None
    attacker_retroactive_prep: bool = False


class InjuryBand(StrictContract):
    severity_min: float = Field(ge=STAT_MIN, le=STAT_MAX)
    severity_max: float = Field(ge=STAT_MIN, le=STAT_MAX)
    bleeding_max: float = Field(ge=STAT_MIN, le=STAT_MAX)
    body_regions: tuple[str, ...] = ("torso",)


class CombatExchangeResult(StrictContract):
    outcome: CombatOutcomeClass
    attacker_score: float
    defender_score: float
    margin: float
    allowed_outcomes: tuple[CombatOutcomeClass, ...]
    injury_band: InjuryBand | None = None
    rejected: bool = False
    rejection_reason: str | None = None
    roll: float = Field(ge=0.0, le=1.0)
    justification: str = Field(min_length=1, max_length=1_000)


_OUTCOME_RANK: dict[CombatOutcomeClass, int] = {
    CombatOutcomeClass.CATASTROPHIC_FAILURE: -3,
    CombatOutcomeClass.FAILED_ATTEMPT: -2,
    CombatOutcomeClass.COUNTERED: -1,
    CombatOutcomeClass.INTERRUPTED: -1,
    CombatOutcomeClass.STALEMATE: 0,
    CombatOutcomeClass.PARTIAL_CONTACT: 1,
    CombatOutcomeClass.SUCCESS_WITH_COST: 2,
    CombatOutcomeClass.CLEAN_SUCCESS: 3,
}


def combatant_score(combatant: CombatantSnapshot, *, seed: int, salt: str) -> float:
    """Aggregate capability with preparation/terrain/teamwork/morale/injury modifiers."""

    rng = SeededRng(seed=seed, salt=salt)
    base = (
        0.45 * combatant.capability
        + 0.30 * combatant.skill
        + 0.10 * combatant.preparation * STAT_MAX
        + 0.05 * combatant.teamwork * STAT_MAX
        + 0.05 * combatant.morale * STAT_MAX
        + 0.05 * combatant.stamina_ratio * STAT_MAX
    )
    base += combatant.terrain_advantage * 8.0
    base += combatant.surprise * 10.0
    base -= combatant.injury_penalty * 20.0
    noise = (rng.unit() - 0.5) * 6.0
    return clamp_world_scale(base + noise)


def feasible_outcome_envelope(
    *,
    margin: float,
    attacker: CombatantSnapshot,
    defender: CombatantSnapshot,
) -> tuple[CombatOutcomeClass, ...]:
    """Return outcome classes allowed by capability margin (no impossible upsets)."""

    # Large disadvantage without prep/surprise cannot claim clean success.
    if margin < -25.0 and attacker.preparation < 0.4 and attacker.surprise < 0.3:
        return (
            CombatOutcomeClass.FAILED_ATTEMPT,
            CombatOutcomeClass.COUNTERED,
            CombatOutcomeClass.CATASTROPHIC_FAILURE,
            CombatOutcomeClass.STALEMATE,
            CombatOutcomeClass.INTERRUPTED,
        )
    if margin < -10.0:
        allowed = [
            CombatOutcomeClass.FAILED_ATTEMPT,
            CombatOutcomeClass.STALEMATE,
            CombatOutcomeClass.PARTIAL_CONTACT,
            CombatOutcomeClass.COUNTERED,
            CombatOutcomeClass.INTERRUPTED,
        ]
        # Weaker but prepared / surprise may still achieve costly success.
        if attacker.preparation >= 0.6 or attacker.surprise >= 0.5:
            allowed.append(CombatOutcomeClass.SUCCESS_WITH_COST)
            if margin > -18.0 and attacker.preparation >= 0.75:
                allowed.append(CombatOutcomeClass.CLEAN_SUCCESS)
        return tuple(dict.fromkeys(allowed))
    if margin < 5.0:
        return (
            CombatOutcomeClass.STALEMATE,
            CombatOutcomeClass.PARTIAL_CONTACT,
            CombatOutcomeClass.SUCCESS_WITH_COST,
            CombatOutcomeClass.FAILED_ATTEMPT,
            CombatOutcomeClass.COUNTERED,
        )
    if margin < 20.0:
        return (
            CombatOutcomeClass.PARTIAL_CONTACT,
            CombatOutcomeClass.SUCCESS_WITH_COST,
            CombatOutcomeClass.CLEAN_SUCCESS,
            CombatOutcomeClass.STALEMATE,
        )
    # Dominant attacker; defender high prep can still force cost/stalemate.
    allowed = [
        CombatOutcomeClass.CLEAN_SUCCESS,
        CombatOutcomeClass.SUCCESS_WITH_COST,
        CombatOutcomeClass.PARTIAL_CONTACT,
    ]
    if defender.preparation >= 0.7 or defender.terrain_advantage > 0.4:
        allowed.extend((CombatOutcomeClass.STALEMATE, CombatOutcomeClass.FAILED_ATTEMPT))
    return tuple(dict.fromkeys(allowed))


def resolve_combat_exchange(exchange: CombatExchangeInput) -> CombatExchangeResult:
    """Resolve one combat exchange inside a feasible outcome envelope.

    Rejects impossible proposed outcomes. Reactor cannot claim retroactive preparation.
    """

    if exchange.attacker_retroactive_prep:
        raise InvalidAction("reactor cannot retroactively apply preparation")

    atk = combatant_score(exchange.attacker, seed=exchange.seed, salt="attacker")
    dfn = combatant_score(exchange.defender, seed=exchange.seed, salt="defender")
    margin = atk - dfn
    allowed = feasible_outcome_envelope(
        margin=margin,
        attacker=exchange.attacker,
        defender=exchange.defender,
    )
    rng = SeededRng(seed=exchange.seed, salt="outcome")
    roll = rng.unit()

    if exchange.proposed_outcome is not None:
        if exchange.proposed_outcome not in allowed:
            return CombatExchangeResult(
                outcome=exchange.proposed_outcome,
                attacker_score=atk,
                defender_score=dfn,
                margin=margin,
                allowed_outcomes=allowed,
                rejected=True,
                rejection_reason="outcome_outside_feasible_envelope",
                roll=roll,
                justification=(
                    f"proposed {exchange.proposed_outcome.value} not in "
                    f"{[o.value for o in allowed]}"
                ),
            )
        outcome = exchange.proposed_outcome
    else:
        outcome = _pick_outcome(allowed, margin=margin, roll=roll)

    injury_band = _injury_band_for(outcome, margin=margin)
    return CombatExchangeResult(
        outcome=outcome,
        attacker_score=atk,
        defender_score=dfn,
        margin=margin,
        allowed_outcomes=allowed,
        injury_band=injury_band,
        roll=roll,
        justification=(
            f"margin={margin:.2f}; attacker_prep={exchange.attacker.preparation:.2f}; "
            f"selected={outcome.value}"
        ),
    )


def _pick_outcome(
    allowed: tuple[CombatOutcomeClass, ...],
    *,
    margin: float,
    roll: float,
) -> CombatOutcomeClass:
    if not allowed:
        return CombatOutcomeClass.STALEMATE
    # Bias toward higher-rank outcomes when margin is positive.
    ranked = sorted(allowed, key=lambda o: _OUTCOME_RANK[o])
    if margin >= 15.0:
        idx = min(len(ranked) - 1, int(roll * len(ranked) + 0.5))
    elif margin <= -15.0:
        idx = max(0, int(roll * len(ranked) * 0.5))
    else:
        idx = min(len(ranked) - 1, int(roll * len(ranked)))
    return ranked[idx]


def _injury_band_for(outcome: CombatOutcomeClass, *, margin: float) -> InjuryBand | None:
    if outcome in {
        CombatOutcomeClass.FAILED_ATTEMPT,
        CombatOutcomeClass.STALEMATE,
        CombatOutcomeClass.INTERRUPTED,
    }:
        return None
    if outcome is CombatOutcomeClass.PARTIAL_CONTACT:
        return InjuryBand(severity_min=1.0, severity_max=20.0, bleeding_max=10.0)
    if outcome is CombatOutcomeClass.SUCCESS_WITH_COST:
        return InjuryBand(severity_min=10.0, severity_max=40.0, bleeding_max=25.0)
    if outcome is CombatOutcomeClass.CLEAN_SUCCESS:
        high = clamp_world_scale(35.0 + max(0.0, margin))
        return InjuryBand(
            severity_min=20.0,
            severity_max=min(STAT_MAX, high),
            bleeding_max=40.0,
        )
    if outcome is CombatOutcomeClass.COUNTERED:
        return InjuryBand(
            severity_min=5.0,
            severity_max=35.0,
            bleeding_max=20.0,
            body_regions=("torso", "left_arm", "right_arm"),
        )
    if outcome is CombatOutcomeClass.CATASTROPHIC_FAILURE:
        return InjuryBand(severity_min=40.0, severity_max=80.0, bleeding_max=60.0)
    return None
