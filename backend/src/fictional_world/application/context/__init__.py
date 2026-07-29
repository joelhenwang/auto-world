"""Perspective-safe context assembly (Stage 1 / S1-KNOW-001)."""

from fictional_world.application.context.assembler import assemble_character_context
from fictional_world.application.context.hashing import verify_package_hash
from fictional_world.application.context.types import (
    STAGE1_ACTION_FAMILIES,
    ContextSection,
    ContextSectionId,
    ContextTaskType,
    SealedContextPackage,
)

__all__ = [
    "STAGE1_ACTION_FAMILIES",
    "ContextSection",
    "ContextSectionId",
    "ContextTaskType",
    "SealedContextPackage",
    "assemble_character_context",
    "verify_package_hash",
]
