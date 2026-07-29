"""Continuity domain package (Stage 2 persistence + pure services)."""

from fictional_world.domain.continuity.commitments import create_commitment, update_status
from fictional_world.domain.continuity.config import (
    DIMINISHING_RETURNS_RATE,
    NORMAL_SCENE_MAX_ABS_DELTA,
)
from fictional_world.domain.continuity.evidence import RelationshipEvidenceInput
from fictional_world.domain.continuity.goals import (
    abandon,
    activate,
    complete,
    create_goal,
    set_priority,
)
from fictional_world.domain.continuity.persistence import (
    ActivityPersistenceRecord,
    CommitmentPersistenceRecord,
    DailyAuditPersistenceRecord,
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
    SummarySourcePersistenceRecord,
)
from fictional_world.domain.continuity.plans import (
    create_primary_plan,
    demote_conflicting_primary_plans,
    invalidate_plan_for_failed_prerequisites,
    revise_plan,
    update_plan_step_status,
)
from fictional_world.domain.continuity.relationships import apply_relationship_evidence
from fictional_world.domain.continuity.relevance import (
    commitments_for_reminder,
    goal_relevance_score,
    rank_goals_for_context,
)
from fictional_world.domain.continuity.statuses import (
    CommitmentStatus,
    GoalStatus,
    PlanStatus,
    PlanStepStatus,
)

__all__ = [
    "DIMINISHING_RETURNS_RATE",
    "NORMAL_SCENE_MAX_ABS_DELTA",
    "ActivityPersistenceRecord",
    "CommitmentPersistenceRecord",
    "CommitmentStatus",
    "DailyAuditPersistenceRecord",
    "DayRunPersistenceRecord",
    "DiaryEntryPersistenceRecord",
    "GoalPersistenceRecord",
    "GoalStatus",
    "HookPersistenceRecord",
    "NarrativeMetricPersistenceRecord",
    "NpcLifecyclePersistenceRecord",
    "NpcProfilePersistenceRecord",
    "PlanPersistenceRecord",
    "PlanStatus",
    "PlanStepPersistenceRecord",
    "PlanStepStatus",
    "RelationshipEdgePersistenceRecord",
    "RelationshipEvidenceInput",
    "RoutePersistenceRecord",
    "SummaryPersistenceRecord",
    "SummarySourcePersistenceRecord",
    "abandon",
    "activate",
    "apply_relationship_evidence",
    "commitments_for_reminder",
    "complete",
    "create_commitment",
    "create_goal",
    "create_primary_plan",
    "demote_conflicting_primary_plans",
    "goal_relevance_score",
    "invalidate_plan_for_failed_prerequisites",
    "rank_goals_for_context",
    "revise_plan",
    "set_priority",
    "update_plan_step_status",
    "update_status",
]
