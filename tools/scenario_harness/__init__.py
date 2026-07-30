"""Scenario harness for Stage 0 foundation gate (S0-QA-002)."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed import (
    import_caldris_stage0,
    import_caldris_stage1,
    import_caldris_stage2,
)
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.testing import Stage1FakeModelGateway, Stage2FakeModelGateway


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScenarioAssertion:
    path: str | None = None
    equals: Any = None
    invariant: str | None = None


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: str
    seed: str
    model_script: str | None = None
    random_script: str | None = None
    steps: tuple[ScenarioStep, ...] = ()
    assertions: tuple[ScenarioAssertion, ...] = ()


@dataclass
class ScenarioResult:
    scenario_id: str
    world_id: UUID | None = None
    event_timeline: list[str] = field(default_factory=list)
    task_trace: list[str] = field(default_factory=list)
    model_calls: list[dict[str, Any]] = field(default_factory=list)
    state_hashes: list[str] = field(default_factory=list)
    invariant_report: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    passed: bool = False


UowFactory = Callable[[], UnitOfWork]


def load_scenario(path: Path) -> ScenarioSpec:
    """Load a TOML scenario; Stage 0 supports TOML only."""

    if path.suffix not in {".toml", ".tml"}:
        msg = f"Stage 0 scenario harness supports TOML only: {path}"
        raise ValueError(msg)
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    steps = tuple(
        ScenarioStep(action=str(item["action"]), params=dict(item.get("params", {})))
        for item in raw.get("steps", [])
    )
    assertions = tuple(
        ScenarioAssertion(
            path=item.get("path"),
            equals=item.get("equals"),
            invariant=item.get("invariant"),
        )
        for item in raw.get("assertions", [])
    )
    return ScenarioSpec(
        scenario_id=str(raw["scenario_id"]),
        seed=str(raw.get("seed", "")),
        model_script=raw.get("model_script"),
        random_script=raw.get("random_script"),
        steps=steps,
        assertions=assertions,
    )


def run_scenario_skeleton(spec: ScenarioSpec) -> ScenarioResult:
    """Produce an empty structured result (kept for harness self-tests)."""

    return ScenarioResult(
        scenario_id=spec.scenario_id,
        invariant_report=[a.invariant for a in spec.assertions if a.invariant],
        passed=False,
    )


async def run_stage0_foundation(
    uow: UnitOfWork,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Execute the Caldris Stage 0 foundation scenario against a real UoW."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    runner = DeterministicPhaseRunner(uow)

    for step in spec.steps:
        action = step.action
        if action == "noop":
            result.task_trace.append("noop")
            continue
        if action == "seed_caldris":
            seeded = await import_caldris_stage0(uow, root=pack_root, fixture_name="stage0")
            await uow.commit()
            result.world_id = seeded.world_id
            result.task_trace.append(f"seed:{seeded.seed_id}:{seeded.already_imported}")
            result.event_timeline.append("WORLD_SEEDED")
            continue
        if action == "advance_phase":
            if result.world_id is None:
                result.failures.append("advance_phase before seed")
                result.passed = False
                return result
            advance = await runner.request_phase_advance(result.world_id)
            await uow.commit()
            result.task_trace.append(f"advance:{advance.absolute_phase_index}:{advance.phase_name}")
            result.event_timeline.extend(
                [f"phase:{advance.absolute_phase_index}:{eid}" for eid in advance.event_ids]
            )
            if advance.snapshot_id is not None:
                result.state_hashes.append(str(advance.snapshot_id))
            continue
        if action == "reconcile":
            if result.world_id is None:
                result.failures.append("reconcile before seed")
                result.passed = False
                return result
            report = await runner.reconcile(result.world_id)
            await uow.commit()
            result.task_trace.append(
                f"reconcile:completed={report.phase_completed}:tasks={report.tasks_created}"
            )
            continue
        result.failures.append(f"unknown action: {action}")
        result.passed = False
        return result

    await _evaluate_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def run_stage1_first_day(
    uow_factory: UowFactory,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Run the fake-model Stage 1 day with a fresh UoW at every step."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    for step in spec.steps:
        async with uow_factory() as uow:
            if step.action == "seed_caldris_stage1":
                seeded = await import_caldris_stage1(uow, root=pack_root)
                await uow.commit()
                result.world_id = seeded.world_id
                result.task_trace.append(f"seed:{seeded.seed_id}:stage1:{seeded.already_imported}")
                result.event_timeline.append("WORLD_SEEDED")
                continue
            if step.action == "advance_stage1_phase":
                if result.world_id is None:
                    result.failures.append("advance_stage1_phase before seed")
                    break
                gateway = Stage1FakeModelGateway()
                advance = await DeterministicPhaseRunner(
                    uow,
                    model_gateway=gateway,
                    stage1=True,
                ).request_phase_advance(result.world_id)
                await uow.commit()
                result.task_trace.append(
                    f"advance:{advance.absolute_phase_index}:{advance.phase_name}"
                )
                result.event_timeline.extend(
                    f"phase:{advance.absolute_phase_index}:{event_id}"
                    for event_id in advance.event_ids
                )
                result.model_calls.extend(gateway.calls)
                if advance.snapshot_id is not None:
                    result.state_hashes.append(str(advance.snapshot_id))
                continue
            result.failures.append(f"unknown Stage 1 action: {step.action}")
            break

    if result.world_id is not None:
        async with uow_factory() as uow:
            await _evaluate_stage1_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def run_stage2_seven_day(
    uow_factory: UowFactory,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Run the fake-model Stage 2 seven-day soak with per-day UoW boundaries."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    for step in spec.steps:
        if step.action == "seed_caldris_stage2":
            async with uow_factory() as uow:
                seeded = await import_caldris_stage2(uow, root=pack_root)
                await uow.commit()
                result.world_id = seeded.world_id
                result.task_trace.append(f"seed:{seeded.seed_id}:stage2:{seeded.already_imported}")
                result.event_timeline.append("WORLD_SEEDED")
            continue
        if step.action == "run_stage2_seven_day":
            if result.world_id is None:
                result.failures.append("run_stage2_seven_day before seed")
                break
            for day_index in range(7):
                async with uow_factory() as uow:
                    gateway = Stage2FakeModelGateway()
                    day = await DeterministicPhaseRunner(
                        uow,
                        model_gateway=gateway,
                        stage2=True,
                    ).run_day(result.world_id)
                    await uow.commit()
                    result.task_trace.append(
                        f"day:{day.day_index}:phases={len(day.phase_results)}"
                        f":day_run={day.day_run_id}:hard={day.hard_audit_violations}"
                    )
                    for advance in day.phase_results:
                        result.event_timeline.extend(
                            f"phase:{advance.absolute_phase_index}:{event_id}"
                            for event_id in advance.event_ids
                        )
                        if advance.snapshot_id is not None:
                            result.state_hashes.append(str(advance.snapshot_id))
                    result.model_calls.extend(gateway.calls)
                    if day.day_index != day_index:
                        result.failures.append(
                            f"expected day_index {day_index}, got {day.day_index}"
                        )
            continue
        result.failures.append(f"unknown Stage 2 action: {step.action}")
        break

    if result.world_id is not None:
        async with uow_factory() as uow:
            await _evaluate_stage2_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def _evaluate_stage2_invariants(
    uow: UnitOfWork,
    spec: ScenarioSpec,
    result: ScenarioResult,
) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after Stage 2 steps")
        return

    focus_ids = (
        seed_uuid("character/mira-talren"),
        seed_uuid("character/dain-arcen"),
        seed_uuid("character/iri-voss"),
        seed_uuid("character/torren-kest"),
    )
    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "seven_days_ten_phases":
            for index in range(70):
                phase = await uow.phases.find_by_world_and_index(world_id, index)
                if phase is None or PhaseRunState(phase.state) is not PhaseRunState.COMPLETED:
                    result.failures.append(f"phase {index} missing or incomplete")
                    break
            continue
        if invariant == "four_focus_characters":
            present = set(await uow.characters.list_character_ids_for_world(world_id))
            missing = [
                str(character_id) for character_id in focus_ids if character_id not in present
            ]
            if missing:
                result.failures.append(f"missing focus characters: {missing}")
            continue
        if invariant == "same_snapshot_per_phase_intents":
            # Sample waking phases across the week (skip sleep-only night/midnight).
            sample_indexes = [0, 2, 7, 10, 22, 37, 52, 67]
            for index in sample_indexes:
                phase = await uow.phases.find_by_world_and_index(world_id, index)
                if phase is None:
                    result.failures.append(f"phase {index} missing for snapshot check")
                    continue
                if phase.phase_name in {"night", "midnight"}:
                    continue
                snapshot = await uow.snapshots.get_for_phase(phase.id)
                proposals = await uow.action_proposals.list_for_phase(phase.id)
                if snapshot is None:
                    result.failures.append(f"phase {phase.id} missing snapshot")
                    continue
                if not proposals:
                    # Sleep/skip-only phases may have zero intents.
                    continue
                if {proposal.snapshot_id for proposal in proposals} != {snapshot.id}:
                    result.failures.append(f"phase {phase.id} intents use different snapshots")
            continue
        if invariant == "seven_day_runs":
            day_runs = await uow.day_runs.list_for_world(world_id)
            if len(day_runs) != 7:
                result.failures.append(f"expected 7 day_run rows, got {len(day_runs)}")
            elif any(row.status != "completed" for row in day_runs):
                result.failures.append("one or more day_run rows are not completed")
            elif {row.day_index for row in day_runs} != set(range(7)):
                result.failures.append("day_run day_index set is not 0..6")
            continue
        if invariant == "no_hard_audit_violations":
            day_runs = await uow.day_runs.list_for_world(world_id)
            for day_run in day_runs:
                audit = await uow.daily_audits.get_by_day_run(day_run.id)
                if audit is None:
                    result.failures.append(f"daily_audit missing for day_run {day_run.id}")
                elif audit.hard_violation_count != 0:
                    result.failures.append(
                        f"hard audit violations on day {day_run.day_index}: "
                        f"{audit.hard_violation_count}"
                    )
            continue
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=5_000)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate Stage 2 event idempotency keys")
            continue
        result.failures.append(f"unknown Stage 2 invariant: {invariant}")


async def _evaluate_stage1_invariants(
    uow: UnitOfWork,
    spec: ScenarioSpec,
    result: ScenarioResult,
) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after Stage 1 steps")
        return

    phases = [await uow.phases.find_by_world_and_index(world_id, index) for index in (0, 2, 7)]
    mira_id = seed_uuid("character/mira-talren")
    dain_id = seed_uuid("character/dain-arcen")
    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "three_phase_day":
            if any(phase is None for phase in phases):
                result.failures.append("one or more Stage 1 phases are missing")
            elif any(
                PhaseRunState(phase.state) is not PhaseRunState.COMPLETED
                for phase in phases
                if phase is not None
            ):
                result.failures.append("one or more Stage 1 phases are incomplete")
            continue
        if invariant == "two_intents_one_snapshot":
            for phase in phases:
                if phase is None:
                    continue
                snapshot = await uow.snapshots.get_for_phase(phase.id)
                proposals = await uow.action_proposals.list_for_phase(phase.id)
                if snapshot is None or len(proposals) != 2:
                    result.failures.append(f"phase {phase.id} missing snapshot or two intents")
                    continue
                if {proposal.snapshot_id for proposal in proposals} != {snapshot.id}:
                    result.failures.append(f"phase {phase.id} intents use different snapshots")
            continue
        if invariant == "isolated_perspective_records":
            for phase in phases:
                if phase is None:
                    continue
                scenes = await uow.scenes.list_for_phase(phase.id)
                if len(scenes) != 1:
                    result.failures.append(f"phase {phase.id} does not have one scene")
                    continue
                scope_hashes = {
                    participant.knowledge_scope_hash for participant in scenes[0].participants
                }
                if None in scope_hashes or len(scope_hashes) != 2:
                    result.failures.append(f"phase {phase.id} perspective scopes are not isolated")
            for character_id in (mira_id, dain_id):
                observations = await uow.observations.list_for_observer(character_id)
                memories = await uow.recent_memories.list_for_owner(
                    character_id,
                    world_id=world_id,
                )
                if not observations or not memories:
                    result.failures.append(
                        f"character {character_id} missing observations or recent memories"
                    )
            continue
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=200)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate Stage 1 event idempotency keys")
            continue
        if invariant == "bounded_fake_model_calls":
            if len(result.model_calls) != 10:
                result.failures.append(
                    f"expected 10 fake model calls, got {len(result.model_calls)}"
                )
            continue
        result.failures.append(f"unknown Stage 1 invariant: {invariant}")


async def _evaluate_invariants(uow: UnitOfWork, spec: ScenarioSpec, result: ScenarioResult) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after scenario steps")
        return

    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=200)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate event idempotency keys")
            continue
        if invariant == "phase_completed":
            phase = await uow.phases.find_by_world_and_index(world_id, 0)
            if phase is None or PhaseRunState(phase.state) is not PhaseRunState.COMPLETED:
                result.failures.append("phase 0 not completed")
            continue
        if invariant == "snapshot_sealed":
            phase = await uow.phases.find_by_world_and_index(world_id, 0)
            if phase is None:
                result.failures.append("phase 0 missing for snapshot check")
                continue
            snap = await uow.snapshots.get_for_phase(phase.id)
            if snap is None:
                result.failures.append("phase 0 snapshot missing")
            continue
        if invariant == "mira_memory_written":
            memories = await uow.recent_memories.list_for_owner(
                seed_uuid("character/mira-talren"),
                world_id=world_id,
                limit=20,
            )
            if not memories:
                result.failures.append("mira recent memory missing")
            continue
        if invariant == "world_tick_present":
            events = await uow.events.list_for_world(world_id, limit=200)
            if not any(event.event_type == "WORLD_TICK" for event in events):
                result.failures.append("WORLD_TICK missing")
            continue
        result.failures.append(f"unknown invariant: {invariant}")


async def run_stage3_thirty_day(
    uow_factory: UowFactory,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Run the fake-model Stage 3 thirty-day soak with monthly barrier."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    for step in spec.steps:
        if step.action == "seed_caldris_stage2":
            async with uow_factory() as uow:
                seeded = await import_caldris_stage2(uow, root=pack_root)
                await uow.commit()
                result.world_id = seeded.world_id
                result.task_trace.append(f"seed:{seeded.seed_id}:stage2:{seeded.already_imported}")
                result.event_timeline.append("WORLD_SEEDED")
            continue
        if step.action == "run_stage3_thirty_day":
            if result.world_id is None:
                result.failures.append("run_stage3_thirty_day before seed")
                break
            for day_index in range(30):
                async with uow_factory() as uow:
                    gateway = Stage2FakeModelGateway()
                    day = await DeterministicPhaseRunner(
                        uow,
                        model_gateway=gateway,
                        stage2=True,
                    ).run_day(result.world_id)
                    await uow.commit()
                    result.task_trace.append(
                        f"day:{day.day_index}:phases={len(day.phase_results)}"
                        f":day_run={day.day_run_id}:hard={day.hard_audit_violations}"
                    )
                    for advance in day.phase_results:
                        result.event_timeline.extend(
                            f"phase:{advance.absolute_phase_index}:{event_id}"
                            for event_id in advance.event_ids
                        )
                        if advance.snapshot_id is not None:
                            result.state_hashes.append(str(advance.snapshot_id))
                    result.model_calls.extend(gateway.calls)
                    if day.day_index != day_index:
                        result.failures.append(
                            f"expected day_index {day_index}, got {day.day_index}"
                        )
            async with uow_factory() as uow:
                month = await DeterministicPhaseRunner(
                    uow,
                    model_gateway=Stage2FakeModelGateway(),
                    stage2=True,
                ).finalize_month(result.world_id, month_index=1)
                await uow.commit()
                result.task_trace.append(
                    f"month:{month.month_index}:run={month.month_run_id}"
                    f":already={month.already_finalized}"
                )
            continue
        result.failures.append(f"unknown Stage 3 action: {step.action}")
        break

    if result.world_id is not None:
        async with uow_factory() as uow:
            await _evaluate_stage3_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def _evaluate_stage3_invariants(
    uow: UnitOfWork,
    spec: ScenarioSpec,
    result: ScenarioResult,
) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after Stage 3 steps")
        return

    focus_ids = (
        seed_uuid("character/mira-talren"),
        seed_uuid("character/dain-arcen"),
        seed_uuid("character/iri-voss"),
        seed_uuid("character/torren-kest"),
    )
    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "thirty_days_ten_phases":
            for index in range(300):
                phase = await uow.phases.find_by_world_and_index(world_id, index)
                if phase is None or PhaseRunState(phase.state) is not PhaseRunState.COMPLETED:
                    result.failures.append(f"phase {index} missing or incomplete")
                    break
            continue
        if invariant == "four_focus_characters":
            present = set(await uow.characters.list_character_ids_for_world(world_id))
            missing = [
                str(character_id) for character_id in focus_ids if character_id not in present
            ]
            if missing:
                result.failures.append(f"missing focus characters: {missing}")
            continue
        if invariant == "thirty_day_runs":
            day_runs = await uow.day_runs.list_for_world(world_id)
            if len(day_runs) != 30:
                result.failures.append(f"expected 30 day_run rows, got {len(day_runs)}")
            elif any(row.status != "completed" for row in day_runs):
                result.failures.append("one or more day_run rows are not completed")
            continue
        if invariant == "month_run_completed":
            month = await uow.month_runs.get_by_world_month(world_id, 1)
            if month is None or month.status != "completed":
                result.failures.append("month_run 1 missing or incomplete")
            continue
        if invariant == "no_hard_audit_violations":
            day_runs = await uow.day_runs.list_for_world(world_id)
            for day_run in day_runs:
                audit = await uow.daily_audits.get_by_day_run(day_run.id)
                if audit is None:
                    result.failures.append(f"daily_audit missing for day_run {day_run.id}")
                elif audit.hard_violation_count != 0:
                    result.failures.append(
                        f"hard audit violations on day {day_run.day_index}: "
                        f"{audit.hard_violation_count}"
                    )
            continue
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=20_000)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate Stage 3 event idempotency keys")
            continue
        result.failures.append(f"unknown Stage 3 invariant: {invariant}")
