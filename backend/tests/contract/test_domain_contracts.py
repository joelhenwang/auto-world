"""Contract tests for Stage 0 domain schemas (S0-DOM-001)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import TypeAdapter, ValidationError

from fictional_world.domain import (
    ActionFamily,
    DayPhase,
    FictionalTime,
    MemoryKind,
    MemoryRecord,
    MoveEntityEffect,
    ObservationChannel,
    ObservationRecord,
    PhaseRun,
    PhaseStage,
    RunStatus,
    SceneRun,
    SceneStage,
    SourceKind,
    TaskRun,
    TaskState,
    Visibility,
    WaitEffect,
)
from fictional_world.domain.effects.commands import EFFECT_COMMAND_TYPES, EffectCommand
from fictional_world.domain.events import Provenance


@pytest.mark.contract
def test_fictional_time_ranges() -> None:
    ok = FictionalTime(
        generation_index=1,
        world_day_index=1,
        phase=DayPhase.DAWN,
        absolute_phase_index=0,
    )
    assert ok.phase is DayPhase.DAWN
    with pytest.raises(ValidationError):
        FictionalTime(
            generation_index=0,
            world_day_index=1,
            phase=DayPhase.DAWN,
            absolute_phase_index=0,
        )
    with pytest.raises(ValidationError):
        FictionalTime(
            generation_index=1,
            world_day_index=1,
            phase=DayPhase.DAWN,
            absolute_phase_index=0,
            extra_field="nope",  # type: ignore[call-arg]
        )


@pytest.mark.contract
def test_phase_and_scene_run_forbid_extras() -> None:
    phase = PhaseRun(
        phase_id=uuid4(),
        world_id=uuid4(),
        fictional_time=FictionalTime(
            generation_index=1,
            world_day_index=1,
            phase=DayPhase.MORNING,
            absolute_phase_index=2,
        ),
        status=RunStatus.PENDING,
        stage=PhaseStage.ACCEPT_COMMANDS,
        version=0,
    )
    assert phase.attempt_count == 0
    scene = SceneRun(
        scene_id=uuid4(),
        phase_id=phase.phase_id,
        status=RunStatus.RUNNING,
        stage=SceneStage.DRAFTED,
        participant_ids=(uuid4(),),
        action_proposal_ids=(uuid4(),),
        beat_budget=3,
        version=0,
    )
    assert scene.beat_budget == 3
    with pytest.raises(ValidationError):
        SceneRun(
            scene_id=uuid4(),
            phase_id=phase.phase_id,
            status=RunStatus.RUNNING,
            stage=SceneStage.DRAFTED,
            participant_ids=(),
            action_proposal_ids=(uuid4(),),
            beat_budget=3,
            version=0,
        )


@pytest.mark.contract
def test_effect_union_stage0_and_handbook_kinds() -> None:
    adapter = TypeAdapter(EffectCommand)
    wait = adapter.validate_python(
        {
            "kind": "wait",
            "effect_key": "wait-1",
            "justification": "idle",
            "entity_id": str(uuid4()),
            "phases": 1,
        }
    )
    assert isinstance(wait, WaitEffect)
    move = adapter.validate_python(
        {
            "kind": "move_entity",
            "effect_key": "move-1",
            "justification": "travel",
            "entity_id": str(uuid4()),
            "from_location_id": str(uuid4()),
            "to_location_id": str(uuid4()),
        }
    )
    assert isinstance(move, MoveEntityEffect)
    assert len(EFFECT_COMMAND_TYPES) >= 16


@pytest.mark.contract
def test_observation_and_memory_ranges() -> None:
    now = datetime.now(tz=UTC)
    obs = ObservationRecord(
        observation_id=uuid4(),
        observer_id=uuid4(),
        event_id=uuid4(),
        phase_id=uuid4(),
        channels=(ObservationChannel.SIGHT,),
        perceived_summary="A door opens.",
        uncertainty=0.2,
        created_at=now,
    )
    assert obs.channels == (ObservationChannel.SIGHT,)
    with pytest.raises(ValidationError):
        ObservationRecord(
            observation_id=uuid4(),
            observer_id=uuid4(),
            event_id=uuid4(),
            phase_id=uuid4(),
            channels=(ObservationChannel.SIGHT,),
            perceived_summary="x",
            uncertainty=1.5,
            created_at=now,
        )
    mem = MemoryRecord(
        memory_id=uuid4(),
        owner_character_id=uuid4(),
        kind=MemoryKind.EPISODIC,
        text="Saw the door open.",
        salience=0.5,
        confidence=0.8,
        visibility=Visibility.PRIVATE,
        created_absolute_phase_index=2,
        created_at=now,
    )
    assert mem.kind is MemoryKind.EPISODIC


@pytest.mark.contract
def test_task_run_and_provenance() -> None:
    now = datetime.now(tz=UTC)
    task = TaskRun(
        id=uuid4(),
        task_type="phase.advance",
        state=TaskState.PENDING,
        priority=10,
        payload={"n": 1},
        idempotency_key="phase-advance-1",
        available_at=now,
        created_at=now,
    )
    assert task.state is TaskState.PENDING
    prov = Provenance(
        source_kind=SourceKind.ENGINE,
        source_id=uuid4(),
        created_at=now,
    )
    assert prov.schema_version == "1.0"


@pytest.mark.contract
def test_json_schemas_generate() -> None:
    import runpy
    from pathlib import Path

    script = Path(__file__).resolve().parents[3] / "scripts" / "generate_json_schemas.py"
    result = runpy.run_path(str(script), run_name="__not_main__")
    assert result["main"]() == 0
    out_dir = result["OUT_DIR"]
    assert (out_dir / "manifest.json").is_file()
    for model in result["MODELS"]:
        name = model.__name__
        assert (out_dir / f"{name}.json").is_file()


@pytest.mark.contract
def test_action_family_enum_includes_stage0() -> None:
    assert ActionFamily.WAIT.value == "wait"
    assert ActionFamily.OBSERVE.value == "observe"
    assert ActionFamily.REST.value == "rest"
    assert ActionFamily.MOVE.value == "move"
