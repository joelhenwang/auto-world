"""Domain rules package (S0-SIM-001)."""

from fictional_world.domain.rules.effects import (
    EffectValidationContext,
    project_effect,
    validate_effect,
    validate_effects,
)
from fictional_world.domain.rules.invariants import INVARIANT_REGISTRY, get_invariant
from fictional_world.domain.rules.phase_transitions import (
    PHASE_STAGE_ORDER,
    SCENE_STAGE_ORDER,
    assert_phase_stage_advance,
    assert_run_status_transition,
    assert_scene_stage_advance,
)

__all__ = [
    "INVARIANT_REGISTRY",
    "PHASE_STAGE_ORDER",
    "SCENE_STAGE_ORDER",
    "EffectValidationContext",
    "assert_phase_stage_advance",
    "assert_run_status_transition",
    "assert_scene_stage_advance",
    "get_invariant",
    "project_effect",
    "validate_effect",
    "validate_effects",
]
