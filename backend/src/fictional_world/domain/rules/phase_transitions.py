"""Phase and scene lifecycle transition rules."""

from __future__ import annotations

from fictional_world.domain.common.enums import PhaseStage, RunStatus, SceneStage
from fictional_world.domain.common.errors import InvalidStateTransition

PHASE_STAGE_ORDER: tuple[PhaseStage, ...] = (
    PhaseStage.ACCEPT_COMMANDS,
    PhaseStage.ADVANCE_CLOCK,
    PhaseStage.APPLY_WORLD_TICK,
    PhaseStage.DIRECTOR_REVIEW,
    PhaseStage.COMMIT_WORLD_EVENT,
    PhaseStage.BUILD_SNAPSHOT,
    PhaseStage.GENERATE_INTENTS,
    PhaseStage.ASSEMBLE_SCENES,
    PhaseStage.RESOLVE_SCENES,
    PhaseStage.WRITE_MEMORIES,
    PhaseStage.ENQUEUE_IMAGES,
    PhaseStage.FINALIZE,
)

SCENE_STAGE_ORDER: tuple[SceneStage, ...] = (
    SceneStage.DRAFTED,
    SceneStage.VALIDATE_ACTIONS,
    SceneStage.ORDER_INITIATIVE,
    SceneStage.COLLECT_REACTIONS,
    SceneStage.RESOLVE,
    SceneStage.VALIDATE_EFFECTS,
    SceneStage.COMMIT,
    SceneStage.WRITE_OBSERVATIONS,
    SceneStage.ENQUEUE_IMAGES,
    SceneStage.COMPLETE,
)

_TERMINAL_RUN = frozenset({RunStatus.COMPLETED, RunStatus.FAILED})

_ALLOWED_RUN: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.PENDING: frozenset({RunStatus.RUNNING, RunStatus.FAILED}),
    RunStatus.RUNNING: frozenset(
        {
            RunStatus.WAITING,
            RunStatus.PAUSE_REQUESTED,
            RunStatus.COMPLETED,
            RunStatus.FAILED,
            RunStatus.RETRYING,
        }
    ),
    RunStatus.WAITING: frozenset({RunStatus.RUNNING, RunStatus.FAILED, RunStatus.PAUSE_REQUESTED}),
    RunStatus.PAUSE_REQUESTED: frozenset({RunStatus.PAUSED, RunStatus.RUNNING, RunStatus.FAILED}),
    RunStatus.PAUSED: frozenset({RunStatus.RUNNING, RunStatus.FAILED}),
    RunStatus.RETRYING: frozenset({RunStatus.RUNNING, RunStatus.FAILED, RunStatus.COMPLETED}),
}


def assert_phase_stage_advance(*, current: PhaseStage, nxt: PhaseStage) -> None:
    if current is PhaseStage.FINALIZE:
        raise InvalidStateTransition(entity="phase_stage", from_state=current, to_state=nxt)
    try:
        cur_i = PHASE_STAGE_ORDER.index(current)
        nxt_i = PHASE_STAGE_ORDER.index(nxt)
    except ValueError as exc:
        raise InvalidStateTransition(
            entity="phase_stage", from_state=current, to_state=nxt
        ) from exc
    if nxt_i != cur_i + 1:
        raise InvalidStateTransition(entity="phase_stage", from_state=current, to_state=nxt)


def assert_scene_stage_advance(*, current: SceneStage, nxt: SceneStage) -> None:
    if current in {SceneStage.COMPLETE, SceneStage.INVALIDATED}:
        raise InvalidStateTransition(entity="scene_stage", from_state=current, to_state=nxt)
    if nxt is SceneStage.INVALIDATED:
        return
    try:
        cur_i = SCENE_STAGE_ORDER.index(current)
        nxt_i = SCENE_STAGE_ORDER.index(nxt)
    except ValueError as exc:
        raise InvalidStateTransition(
            entity="scene_stage", from_state=current, to_state=nxt
        ) from exc
    if nxt_i != cur_i + 1:
        raise InvalidStateTransition(entity="scene_stage", from_state=current, to_state=nxt)


def assert_run_status_transition(*, current: RunStatus, nxt: RunStatus) -> None:
    if current in _TERMINAL_RUN:
        raise InvalidStateTransition(entity="run_status", from_state=current, to_state=nxt)
    if nxt not in _ALLOWED_RUN.get(current, frozenset()):
        raise InvalidStateTransition(entity="run_status", from_state=current, to_state=nxt)
