"""Shared domain StrEnums (handbook ``05`` §7)."""

from __future__ import annotations

from enum import StrEnum


class DayPhase(StrEnum):
    DAWN = "dawn"
    SUNRISE = "sunrise"
    MORNING = "morning"
    NOON = "noon"
    AFTERNOON = "afternoon"
    SUNSET = "sunset"
    DUSK = "dusk"
    EVENING = "evening"
    NIGHT = "night"
    MIDNIGHT = "midnight"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSE_REQUESTED = "pause_requested"
    PAUSED = "paused"
    RETRYING = "retrying"
    FAILED = "failed"
    COMPLETED = "completed"


class PhaseStage(StrEnum):
    ACCEPT_COMMANDS = "accept_commands"
    ADVANCE_CLOCK = "advance_clock"
    APPLY_WORLD_TICK = "apply_world_tick"
    DIRECTOR_REVIEW = "director_review"
    COMMIT_WORLD_EVENT = "commit_world_event"
    BUILD_SNAPSHOT = "build_snapshot"
    GENERATE_INTENTS = "generate_intents"
    ASSEMBLE_SCENES = "assemble_scenes"
    RESOLVE_SCENES = "resolve_scenes"
    WRITE_MEMORIES = "write_memories"
    ENQUEUE_IMAGES = "enqueue_images"
    FINALIZE = "finalize"


class SceneStage(StrEnum):
    DRAFTED = "drafted"
    VALIDATE_ACTIONS = "validate_actions"
    ORDER_INITIATIVE = "order_initiative"
    COLLECT_REACTIONS = "collect_reactions"
    RESOLVE = "resolve"
    VALIDATE_EFFECTS = "validate_effects"
    COMMIT = "commit"
    WRITE_OBSERVATIONS = "write_observations"
    ENQUEUE_IMAGES = "enqueue_images"
    COMPLETE = "complete"
    INVALIDATED = "invalidated"


class UserRole(StrEnum):
    WATCHER = "watcher"
    DIRECTOR = "director"
    DEITY = "deity"
    PLAYER = "player"


class SimulationMode(StrEnum):
    AUTO = "auto"
    MANUAL = "manual"


class EntityKind(StrEnum):
    CHARACTER = "character"
    NPC = "npc"
    LOCATION = "location"
    ITEM = "item"
    FACTION = "faction"
    CREATURE = "creature"
    ACTIVITY = "activity"
    ARC = "arc"


class ActionFamily(StrEnum):
    WAIT = "wait"
    CONTINUE_ACTIVITY = "continue_activity"
    MOVE = "move"
    OBSERVE = "observe"
    COMMUNICATE = "communicate"
    SOCIALIZE = "socialize"
    PERSUADE = "persuade"
    DECEIVE = "deceive"
    INVESTIGATE = "investigate"
    ATTACK = "attack"
    DEFEND = "defend"
    CAST_MAGIC = "cast_magic"
    USE_ITEM = "use_item"
    TRANSFER = "transfer"
    CREATE = "create"
    CRAFT = "craft"
    TRAIN = "train"
    WORK = "work"
    REST = "rest"
    CARE = "care"
    PERFORM = "perform"
    RITUAL = "ritual"
    INTERACT_ENVIRONMENT = "interact_environment"
    OTHER = "other"


class Visibility(StrEnum):
    PUBLIC = "public"
    OBSERVABLE = "observable"
    COVERT = "covert"
    PRIVATE = "private"


class ResolutionLevel(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INTERRUPTED = "interrupted"
    INVALIDATED = "invalidated"


class ResourceKind(StrEnum):
    STAMINA = "stamina"
    MANA = "mana"
    MONEY = "money"


class RelationshipDimension(StrEnum):
    FAMILIARITY = "familiarity"
    TRUST = "trust"
    AFFECTION = "affection"
    ATTRACTION = "attraction"
    RESPECT = "respect"
    FEAR = "fear"
    RESENTMENT = "resentment"
    DEPENDENCY = "dependency"
    LOYALTY = "loyalty"


class ObservationChannel(StrEnum):
    SIGHT = "sight"
    HEARING = "hearing"
    TOUCH = "touch"
    SMELL = "smell"
    MAGIC = "magic"
    COMMUNICATION = "communication"
    INFERENCE = "inference"


class MemoryKind(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    RELATIONAL = "relational"
    EMOTIONAL = "emotional"
    AUTOBIOGRAPHICAL = "autobiographical"
    PROCEDURAL = "procedural"
    COMMITMENT = "commitment"
    PLAN = "plan"
    UNRESOLVED_QUESTION = "unresolved_question"
    SECRET = "secret"  # noqa: S105 — MemoryKind enum value, not a credential
    CLAIM = "claim"


class SourceKind(StrEnum):
    ENGINE = "engine"
    MODEL = "model"
    USER = "user"
    MIGRATION = "migration"


class TaskState(StrEnum):
    """Operational task lifecycle states (Stage 0 surface for S0-ORCH-001)."""

    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"
