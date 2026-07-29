"""NPC registry and actor v1 (S2-WORLD-002).

Director proposes NPC stubs; this package deduplicates by fingerprint, enforces
active budgets in pure checks, builds compact cards and perspective-limited
knowledge packages, and manages TTL / archive without focus-slot promotion.

Canonical character entity creation and ``REGISTER_NPC`` effect commit remain
on the resolver path — this module returns validated registry records only.
"""

from fictional_world.application.npc.budgets import check_new_npc_budgets
from fictional_world.application.npc.cards import build_compact_card, compact_card_as_json
from fictional_world.application.npc.config import NpcBudgetConfig, NpcTtlConfig
from fictional_world.application.npc.fingerprint import (
    compute_similarity_fingerprint,
    normalize_token,
    normalize_token_set,
)
from fictional_world.application.npc.knowledge import (
    build_npc_knowledge_package,
    package_contains_forbidden_text,
)
from fictional_world.application.npc.registry import (
    archive_npc,
    extend_ttl_on_meaningful_scene,
    find_duplicate,
    may_receive_ordinary_actor_task,
    proposal_from_director_stub,
    propose_or_register_npc,
    recall_archived_npc,
    to_lifecycle_record,
    to_profile_record,
)
from fictional_world.application.npc.types import (
    BudgetSnapshot,
    BudgetViolation,
    NpcCompactCard,
    NpcKnowledgePackage,
    NpcProposalInput,
    NpcRegistryEntry,
    ProposeNpcResult,
)

__all__ = [
    "BudgetSnapshot",
    "BudgetViolation",
    "NpcBudgetConfig",
    "NpcCompactCard",
    "NpcKnowledgePackage",
    "NpcProposalInput",
    "NpcRegistryEntry",
    "NpcTtlConfig",
    "ProposeNpcResult",
    "archive_npc",
    "build_compact_card",
    "build_npc_knowledge_package",
    "check_new_npc_budgets",
    "compact_card_as_json",
    "compute_similarity_fingerprint",
    "extend_ttl_on_meaningful_scene",
    "find_duplicate",
    "may_receive_ordinary_actor_task",
    "normalize_token",
    "normalize_token_set",
    "package_contains_forbidden_text",
    "proposal_from_director_stub",
    "propose_or_register_npc",
    "recall_archived_npc",
    "to_lifecycle_record",
    "to_profile_record",
]
