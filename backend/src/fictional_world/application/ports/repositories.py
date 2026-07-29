"""Repository and unit-of-work ports (handbook ``19`` §12)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.continuity.persistence import (
    ActivityPersistenceRecord,
    CommitmentPersistenceRecord,
    DayRunPersistenceRecord,
    DiaryEntryPersistenceRecord,
    GoalPersistenceRecord,
    HookPersistenceRecord,
    NarrativeMetricPersistenceRecord,
    NpcLifecyclePersistenceRecord,
    NpcProfilePersistenceRecord,
    PlanPersistenceRecord,
    PlanStepPersistenceRecord,
    RelationshipEdgePersistenceRecord,
    RoutePersistenceRecord,
    SummaryPersistenceRecord,
)
from fictional_world.domain.events.persistence import (
    EventEffectRecord,
    OutboxMessageRecord,
    WorldEventRecord,
)
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    ClaimPersistenceRecord,
    ObservationPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.phases.records import (
    PhaseRunRecord,
    PhaseSnapshotRecord,
)
from fictional_world.domain.scenes.persistence import (
    ActionProposalRecord,
    NarrationRecord,
    PlayerControlSessionRecord,
    ReactionProposalRecord,
    SceneRecord,
    SceneResolutionRecord,
    SceneRunRecord,
    StreamEventRecord,
)
from fictional_world.domain.seed.records import (
    CharacterCardVersionRecord,
    LocationRecord,
    WorldConfigRecord,
)
from fictional_world.domain.tasks.budget import RequestBudgetRecord
from fictional_world.domain.tasks.task_run import TaskRun
from fictional_world.domain.tasks.user_command import UserCommandRecord
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)


class WorldRepository(Protocol):
    async def get(self, world_id: UUID) -> WorldRecord | None: ...

    async def get_by_slug(self, slug: str) -> WorldRecord | None: ...

    async def insert(self, world: WorldRecord) -> WorldRecord: ...

    async def lock_for_event_sequence(self, world_id: UUID) -> WorldRecord: ...

    async def advance_event_sequence(
        self,
        world_id: UUID,
        *,
        next_sequence: int,
        expected_version: int,
    ) -> WorldRecord: ...

    async def get_clock(self, world_id: UUID) -> WorldClockRecord | None: ...

    async def upsert_clock(
        self, clock: WorldClockRecord, *, expected_version: int | None
    ) -> WorldClockRecord: ...

    async def update_status(
        self,
        world_id: UUID,
        *,
        status: str,
        expected_version: int,
    ) -> WorldRecord: ...

    async def insert_config(self, config: WorldConfigRecord) -> WorldConfigRecord: ...

    async def set_config_created_event(
        self, config_id: UUID, *, created_event_id: UUID
    ) -> WorldConfigRecord: ...


class CharacterRepository(Protocol):
    async def insert_entity(self, entity: EntityRecord) -> EntityRecord: ...

    async def insert_character(self, character: CharacterRecord) -> CharacterRecord: ...

    async def get_state(self, character_id: UUID) -> CharacterStateRecord | None: ...

    async def get_state_for_update(self, character_id: UUID) -> CharacterStateRecord: ...

    async def insert_state(self, state: CharacterStateRecord) -> CharacterStateRecord: ...

    async def save_state(
        self,
        state: CharacterStateRecord,
        *,
        expected_version: int,
    ) -> CharacterStateRecord: ...

    async def insert_location(self, location: LocationRecord) -> LocationRecord: ...

    async def get_location(self, entity_id: UUID) -> LocationRecord | None: ...

    async def insert_card(self, card: CharacterCardVersionRecord) -> CharacterCardVersionRecord: ...

    async def get_card(self, card_id: UUID) -> CharacterCardVersionRecord | None: ...

    async def set_character_card(
        self, character_id: UUID, *, card_version_id: UUID
    ) -> CharacterRecord: ...

    async def set_entity_created_event(
        self, entity_id: UUID, *, created_event_id: UUID
    ) -> EntityRecord: ...

    async def list_character_ids_for_world(self, world_id: UUID) -> Sequence[UUID]: ...


class PhaseRepository(Protocol):
    async def get(self, phase_run_id: UUID) -> PhaseRunRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> PhaseRunRecord | None: ...

    async def find_by_world_and_index(
        self, world_id: UUID, absolute_phase_index: int
    ) -> PhaseRunRecord | None: ...

    async def find_active_for_world(self, world_id: UUID) -> PhaseRunRecord | None: ...

    async def insert(self, phase: PhaseRunRecord) -> PhaseRunRecord: ...

    async def save(
        self,
        phase: PhaseRunRecord,
        *,
        expected_version: int,
    ) -> PhaseRunRecord: ...


class EventRepository(Protocol):
    async def get(self, event_id: UUID) -> WorldEventRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> WorldEventRecord | None: ...

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
    ) -> Sequence[WorldEventRecord]: ...

    async def insert(self, event: WorldEventRecord) -> WorldEventRecord: ...

    async def insert_effects(
        self, effects: Sequence[EventEffectRecord]
    ) -> Sequence[EventEffectRecord]: ...


class ObservationRepository(Protocol):
    async def insert_many(
        self, observations: Sequence[ObservationPersistenceRecord]
    ) -> Sequence[ObservationPersistenceRecord]: ...

    async def list_for_observer(
        self,
        observer_id: UUID,
        *,
        limit: int = 50,
    ) -> Sequence[ObservationPersistenceRecord]: ...


class RecentMemoryRepository(Protocol):
    async def insert(self, memory: RecentMemoryRecord) -> RecentMemoryRecord: ...

    async def list_for_owner(
        self,
        owner_character_id: UUID,
        *,
        world_id: UUID,
        limit: int = 50,
    ) -> Sequence[RecentMemoryRecord]: ...


class AggregateVersionRepository(Protocol):
    async def get(
        self,
        world_id: UUID,
        aggregate_type: str,
        aggregate_id: UUID,
    ) -> AggregateVersionRecord | None: ...

    async def upsert(
        self,
        record: AggregateVersionRecord,
        *,
        expected_version: int | None,
    ) -> AggregateVersionRecord: ...

    async def verify(
        self,
        world_id: UUID,
        expected: Mapping[str, int],
    ) -> None:
        """``expected`` maps ``aggregate_type:aggregate_id`` -> version."""
        ...


class OutboxRepository(Protocol):
    async def insert(self, message: OutboxMessageRecord) -> OutboxMessageRecord: ...

    async def find_by_idempotency_key(self, key: str) -> OutboxMessageRecord | None: ...

    async def get(self, message_id: UUID) -> OutboxMessageRecord | None: ...

    async def insert_many(
        self, messages: Sequence[OutboxMessageRecord]
    ) -> Sequence[OutboxMessageRecord]: ...

    async def claim_available(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        limit: int = 1,
    ) -> Sequence[OutboxMessageRecord]: ...

    async def complete(
        self,
        message_id: UUID,
        *,
        worker_id: str,
        now: datetime,
    ) -> OutboxMessageRecord: ...


class TaskRepository(Protocol):
    async def get(self, task_id: UUID) -> TaskRun | None: ...

    async def find_by_idempotency_key(self, key: str) -> TaskRun | None: ...

    async def insert(self, task: TaskRun) -> TaskRun: ...

    async def add_dependency(self, task_id: UUID, depends_on_task_id: UUID) -> None: ...

    async def list_dependencies(self, task_id: UUID) -> Sequence[UUID]: ...

    async def claim_available(
        self,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
        limit: int = 1,
    ) -> Sequence[TaskRun]: ...

    async def heartbeat(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        lease_duration: timedelta,
        now: datetime,
    ) -> TaskRun: ...

    async def mark_running(self, task_id: UUID, *, worker_id: str, now: datetime) -> TaskRun: ...

    async def complete_success(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        result_reference: Mapping[str, object] | None = None,
    ) -> TaskRun: ...

    async def fail_or_retry(
        self,
        task_id: UUID,
        *,
        worker_id: str,
        now: datetime,
        error_code: str,
        error_detail: Mapping[str, object] | None,
        retry_delay: timedelta,
    ) -> TaskRun: ...

    async def cancel(self, task_id: UUID, *, now: datetime) -> TaskRun: ...


class BudgetRepository(Protocol):
    async def get(self, reservation_id: UUID) -> RequestBudgetRecord | None: ...

    async def find_by_reservation_key(self, key: str) -> RequestBudgetRecord | None: ...

    async def reserve(self, record: RequestBudgetRecord) -> RequestBudgetRecord: ...

    async def consume(self, reservation_id: UUID, *, now: datetime) -> RequestBudgetRecord: ...

    async def release(self, reservation_id: UUID) -> RequestBudgetRecord: ...

    async def expire_due(
        self, *, now: datetime, limit: int = 100
    ) -> Sequence[RequestBudgetRecord]: ...


class PhaseSnapshotRepository(Protocol):
    async def get(self, snapshot_id: UUID) -> PhaseSnapshotRecord | None: ...

    async def get_for_phase(self, phase_run_id: UUID) -> PhaseSnapshotRecord | None: ...

    async def insert(self, snapshot: PhaseSnapshotRecord) -> PhaseSnapshotRecord: ...


class ActionProposalRepository(Protocol):
    async def get(self, proposal_id: UUID) -> ActionProposalRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> ActionProposalRecord | None: ...

    async def list_for_phase(self, phase_run_id: UUID) -> Sequence[ActionProposalRecord]: ...

    async def insert(self, proposal: ActionProposalRecord) -> ActionProposalRecord: ...


class SceneRepository(Protocol):
    async def get(self, scene_id: UUID) -> SceneRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> SceneRecord | None: ...

    async def list_for_phase(self, phase_run_id: UUID) -> Sequence[SceneRecord]: ...

    async def insert(self, scene: SceneRecord) -> SceneRecord: ...

    async def save(self, scene: SceneRecord, *, expected_version: int) -> SceneRecord: ...


class ReactionProposalRepository(Protocol):
    async def get(self, reaction_id: UUID) -> ReactionProposalRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> ReactionProposalRecord | None: ...

    async def list_for_scene(self, scene_id: UUID) -> Sequence[ReactionProposalRecord]: ...

    async def insert(self, reaction: ReactionProposalRecord) -> ReactionProposalRecord: ...


class SceneResolutionRepository(Protocol):
    async def get(self, resolution_id: UUID) -> SceneResolutionRecord | None: ...

    async def get_for_scene(self, scene_id: UUID) -> SceneResolutionRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> SceneResolutionRecord | None: ...

    async def insert(self, resolution: SceneResolutionRecord) -> SceneResolutionRecord: ...


class SceneRunRepository(Protocol):
    async def get(self, run_id: UUID) -> SceneRunRecord | None: ...

    async def get_for_scene(self, scene_id: UUID) -> SceneRunRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> SceneRunRecord | None: ...

    async def insert(self, run: SceneRunRecord) -> SceneRunRecord: ...


class NarrationRepository(Protocol):
    async def get(self, narration_id: UUID) -> NarrationRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> NarrationRecord | None: ...

    async def list_for_scene(self, scene_id: UUID) -> Sequence[NarrationRecord]: ...

    async def insert(self, narration: NarrationRecord) -> NarrationRecord: ...


class StreamEventRepository(Protocol):
    async def get(self, event_id: UUID) -> StreamEventRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> StreamEventRecord | None: ...

    async def list_after(
        self,
        world_id: UUID,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
    ) -> Sequence[StreamEventRecord]: ...

    async def next_sequence(self, world_id: UUID) -> int: ...

    async def insert(self, event: StreamEventRecord) -> StreamEventRecord: ...


class PlayerControlRepository(Protocol):
    async def get(self, session_id: UUID) -> PlayerControlSessionRecord | None: ...

    async def find_active_for_character(
        self, character_id: UUID
    ) -> PlayerControlSessionRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> PlayerControlSessionRecord | None: ...

    async def insert(self, session: PlayerControlSessionRecord) -> PlayerControlSessionRecord: ...

    async def save(
        self, session: PlayerControlSessionRecord, *, expected_version: int
    ) -> PlayerControlSessionRecord: ...


class UserCommandRepository(Protocol):
    async def get(self, command_id: UUID) -> UserCommandRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> UserCommandRecord | None: ...

    async def list_pending_for_world(
        self,
        world_id: UUID,
        *,
        limit: int = 100,
    ) -> Sequence[UserCommandRecord]: ...

    async def insert(self, command: UserCommandRecord) -> UserCommandRecord: ...


class GoalRepository(Protocol):
    async def get(self, goal_id: UUID) -> GoalPersistenceRecord | None: ...

    async def insert(self, goal: GoalPersistenceRecord) -> GoalPersistenceRecord: ...

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID
    ) -> Sequence[GoalPersistenceRecord]: ...


class PlanRepository(Protocol):
    async def get(self, plan_id: UUID) -> PlanPersistenceRecord | None: ...

    async def insert(self, plan: PlanPersistenceRecord) -> PlanPersistenceRecord: ...

    async def list_for_goal(self, goal_id: UUID) -> Sequence[PlanPersistenceRecord]: ...

    async def insert_step(self, step: PlanStepPersistenceRecord) -> PlanStepPersistenceRecord: ...


class CommitmentRepository(Protocol):
    async def get(self, commitment_id: UUID) -> CommitmentPersistenceRecord | None: ...

    async def insert(
        self, commitment: CommitmentPersistenceRecord
    ) -> CommitmentPersistenceRecord: ...

    async def list_for_debtor(
        self, debtor_character_id: UUID, *, world_id: UUID
    ) -> Sequence[CommitmentPersistenceRecord]: ...


class RelationshipEdgeRepository(Protocol):
    async def get(
        self, source_character_id: UUID, target_character_id: UUID
    ) -> RelationshipEdgePersistenceRecord | None: ...

    async def insert(
        self, edge: RelationshipEdgePersistenceRecord
    ) -> RelationshipEdgePersistenceRecord: ...

    async def list_for_source(
        self, source_character_id: UUID, *, world_id: UUID
    ) -> Sequence[RelationshipEdgePersistenceRecord]: ...


class ClaimRepository(Protocol):
    async def get(self, claim_id: UUID) -> ClaimPersistenceRecord | None: ...

    async def insert(self, claim: ClaimPersistenceRecord) -> ClaimPersistenceRecord: ...

    async def list_for_speaker(
        self, speaker_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[ClaimPersistenceRecord]: ...


class BeliefRepository(Protocol):
    async def get(self, belief_id: UUID) -> BeliefPersistenceRecord | None: ...

    async def insert(self, belief: BeliefPersistenceRecord) -> BeliefPersistenceRecord: ...

    async def list_for_character(
        self, character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[BeliefPersistenceRecord]: ...


class SecretAccessRepository(Protocol):
    async def get(self, secret_access_id: UUID) -> SecretAccessPersistenceRecord | None: ...

    async def insert(
        self, access: SecretAccessPersistenceRecord
    ) -> SecretAccessPersistenceRecord: ...

    async def list_for_holder(
        self, holder_character_id: UUID, *, world_id: UUID
    ) -> Sequence[SecretAccessPersistenceRecord]: ...


class ActivityRepository(Protocol):
    async def get(self, activity_id: UUID) -> ActivityPersistenceRecord | None: ...

    async def insert(self, activity: ActivityPersistenceRecord) -> ActivityPersistenceRecord: ...

    async def list_for_owner(
        self, owner_entity_id: UUID, *, world_id: UUID
    ) -> Sequence[ActivityPersistenceRecord]: ...


class RouteRepository(Protocol):
    async def get(self, route_id: UUID) -> RoutePersistenceRecord | None: ...

    async def insert(self, route: RoutePersistenceRecord) -> RoutePersistenceRecord: ...

    async def list_for_world(self, world_id: UUID) -> Sequence[RoutePersistenceRecord]: ...


class HookRepository(Protocol):
    async def get(self, hook_id: UUID) -> HookPersistenceRecord | None: ...

    async def get_by_key(self, world_id: UUID, hook_key: str) -> HookPersistenceRecord | None: ...

    async def insert(self, hook: HookPersistenceRecord) -> HookPersistenceRecord: ...

    async def update(self, hook: HookPersistenceRecord) -> HookPersistenceRecord: ...

    async def list_for_world(
        self, world_id: UUID, *, status: str | None = None
    ) -> Sequence[HookPersistenceRecord]: ...


class NarrativeMetricRepository(Protocol):
    async def insert(
        self, metric: NarrativeMetricPersistenceRecord
    ) -> NarrativeMetricPersistenceRecord: ...

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        metric_key: str | None = None,
        limit: int = 50,
    ) -> Sequence[NarrativeMetricPersistenceRecord]: ...


class NpcRepository(Protocol):
    async def get_profile(self, character_id: UUID) -> NpcProfilePersistenceRecord | None: ...

    async def insert_profile(
        self, profile: NpcProfilePersistenceRecord
    ) -> NpcProfilePersistenceRecord: ...

    async def get_lifecycle(self, character_id: UUID) -> NpcLifecyclePersistenceRecord | None: ...

    async def insert_lifecycle(
        self, lifecycle: NpcLifecyclePersistenceRecord
    ) -> NpcLifecyclePersistenceRecord: ...


class SummaryRepository(Protocol):
    async def get(self, summary_id: UUID) -> SummaryPersistenceRecord | None: ...

    async def insert(self, summary: SummaryPersistenceRecord) -> SummaryPersistenceRecord: ...

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[SummaryPersistenceRecord]: ...


class DiaryEntryRepository(Protocol):
    async def get(self, entry_id: UUID) -> DiaryEntryPersistenceRecord | None: ...

    async def insert(self, entry: DiaryEntryPersistenceRecord) -> DiaryEntryPersistenceRecord: ...

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[DiaryEntryPersistenceRecord]: ...


class DayRunRepository(Protocol):
    async def get(self, day_run_id: UUID) -> DayRunPersistenceRecord | None: ...

    async def find_by_idempotency_key(self, key: str) -> DayRunPersistenceRecord | None: ...

    async def insert(self, day_run: DayRunPersistenceRecord) -> DayRunPersistenceRecord: ...

    async def list_for_world(self, world_id: UUID) -> Sequence[DayRunPersistenceRecord]: ...


class UnitOfWork(Protocol):
    worlds: WorldRepository
    characters: CharacterRepository
    phases: PhaseRepository
    snapshots: PhaseSnapshotRepository
    events: EventRepository
    observations: ObservationRepository
    recent_memories: RecentMemoryRepository
    aggregate_versions: AggregateVersionRepository
    outbox: OutboxRepository
    tasks: TaskRepository
    budgets: BudgetRepository
    action_proposals: ActionProposalRepository
    scenes: SceneRepository
    reactions: ReactionProposalRepository
    scene_resolutions: SceneResolutionRepository
    scene_runs: SceneRunRepository
    narrations: NarrationRepository
    stream_events: StreamEventRepository
    player_controls: PlayerControlRepository
    user_commands: UserCommandRepository
    goals: GoalRepository
    plans: PlanRepository
    commitments: CommitmentRepository
    relationship_edges: RelationshipEdgeRepository
    claims: ClaimRepository
    beliefs: BeliefRepository
    secret_access: SecretAccessRepository
    activities: ActivityRepository
    routes: RouteRepository
    hooks: HookRepository
    narrative_metrics: NarrativeMetricRepository
    npcs: NpcRepository
    summaries: SummaryRepository
    diary_entries: DiaryEntryRepository
    day_runs: DayRunRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
