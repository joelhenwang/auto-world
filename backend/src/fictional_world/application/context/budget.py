"""Token estimation and Stage 1 context budget trimming."""

from __future__ import annotations

from typing import Any

from fictional_world.application.context.hashing import content_hash
from fictional_world.application.context.types import (
    ContextSection,
    ContextSectionId,
    SealedContextPackage,
)

# Approximate tokens ≈ ceil(chars / 4). Versioned heuristic for Stage 1.
CHARS_PER_TOKEN = 4

SECTION_SOFT_CAPS: dict[ContextSectionId, int] = {
    ContextSectionId.STABLE_IDENTITY: 2_000,
    ContextSectionId.CURRENT_STATE: 1_200,
    ContextSectionId.CURRENT_PERCEPTION: 1_300,
    ContextSectionId.GOALS_AND_PLANS: 1_200,
    ContextSectionId.RELATIONSHIPS: 1_300,
    ContextSectionId.RECENT_MEMORY: 3_000,
    ContextSectionId.CAPABILITIES: 1_200,
    ContextSectionId.KNOWN_LOCAL_MAP: 1_300,
    ContextSectionId.ALLOWED_ACTION_FAMILIES: 200,
    ContextSectionId.PRIVATE_BELIEFS: 800,
    ContextSectionId.SCENE_WORKING: 1_500,
}

PACKAGE_SOFT_CAP = 18_000
PACKAGE_HARD_CAP = 32_000

# Trim order: never strip perception / hard state / allowed actions / private commitments.
TRIM_ORDER: tuple[ContextSectionId, ...] = (
    ContextSectionId.RECENT_MEMORY,
    ContextSectionId.KNOWN_LOCAL_MAP,
    ContextSectionId.RELATIONSHIPS,
    ContextSectionId.STABLE_IDENTITY,
    ContextSectionId.GOALS_AND_PLANS,
    ContextSectionId.CAPABILITIES,
)

PROTECTED: frozenset[ContextSectionId] = frozenset(
    {
        ContextSectionId.CURRENT_STATE,
        ContextSectionId.CURRENT_PERCEPTION,
        ContextSectionId.ALLOWED_ACTION_FAMILIES,
        ContextSectionId.PRIVATE_BELIEFS,
        ContextSectionId.SCENE_WORKING,
    }
)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def estimate_content_tokens(content: object) -> int:
    from fictional_world.application.context.hashing import canonical_json

    if isinstance(content, str):
        return estimate_tokens(content)
    return estimate_tokens(canonical_json(content))


def _truncate_content(
    content: dict[str, Any] | str | list[Any], max_tokens: int
) -> dict[str, Any] | str | list[Any]:
    if max_tokens <= 0:
        return "" if isinstance(content, str) else []
    max_chars = max_tokens * CHARS_PER_TOKEN
    if isinstance(content, str):
        return content[:max_chars]
    if isinstance(content, list):
        kept: list[Any] = []
        used = 0
        for item in content:
            typed_item: Any = item
            cost = estimate_content_tokens(typed_item)
            if used + cost > max_tokens and kept:
                break
            kept.append(typed_item)
            used += cost
        return kept
    from fictional_world.application.context.hashing import canonical_json

    raw = canonical_json(content)
    if len(raw) <= max_chars:
        return content
    return raw[:max_chars]


def trim_sections(
    sections: tuple[ContextSection, ...],
    *,
    soft_cap: int = PACKAGE_SOFT_CAP,
) -> tuple[tuple[ContextSection, ...], tuple[str, ...]]:
    """Return trimmed sections and omitted-section notes."""

    mutable = {s.section_id: s for s in sections}
    omitted: list[str] = []
    total = sum(s.token_estimate for s in mutable.values())
    if total <= soft_cap:
        return sections, ()

    for section_id in TRIM_ORDER:
        if total <= soft_cap:
            break
        if section_id in PROTECTED or section_id not in mutable:
            continue
        section = mutable[section_id]
        cap = SECTION_SOFT_CAPS.get(section_id, 500)
        # If still over, shrink toward half then empty list/string.
        target = min(cap, max(0, soft_cap - (total - section.token_estimate)))
        if target >= section.token_estimate:
            continue
        new_content = _truncate_content(section.content, target)
        new_tokens = estimate_content_tokens(new_content)
        mutable[section_id] = ContextSection(
            section_id=section.section_id,
            content=new_content,
            source_record_ids=section.source_record_ids,
            token_estimate=new_tokens,
            trusted=section.trusted,
            content_hash=content_hash(
                {
                    "section_id": section.section_id.value,
                    "content": new_content,
                    "source_record_ids": list(section.source_record_ids),
                    "trusted": section.trusted,
                }
            ),
        )
        omitted.append(f"trimmed:{section_id.value}:{section.token_estimate}->{new_tokens}")
        total = sum(s.token_estimate for s in mutable.values())

    ordered = tuple(mutable[s.section_id] for s in sections if s.section_id in mutable)
    return ordered, tuple(omitted)


def package_within_hard_cap(package: SealedContextPackage) -> bool:
    return package.token_estimate <= PACKAGE_HARD_CAP
