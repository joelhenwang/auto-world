"""Deterministic hashing helpers for sealed context packages."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fictional_world.application.context.types import ContextSection, SealedContextPackage


def canonical_json(value: Any) -> str:
    """Stable JSON for hashing (sorted keys, no whitespace variance)."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def section_content_hash(section: ContextSection) -> str:
    return content_hash(
        {
            "section_id": section.section_id.value,
            "content": section.content,
            "source_record_ids": list(section.source_record_ids),
            "trusted": section.trusted,
        }
    )


def compute_package_hash(package: SealedContextPackage) -> str:
    payload = {
        "schema_version": package.schema_version,
        "observer_id": str(package.observer_id),
        "phase_snapshot_id": str(package.phase_snapshot_id),
        "task_type": package.task_type.value,
        "omitted_sections": list(package.omitted_sections),
        "sections": [
            {
                "section_id": section.section_id.value,
                "content_hash": section.content_hash,
                "source_record_ids": list(section.source_record_ids),
                "trusted": section.trusted,
            }
            for section in package.sections
        ],
    }
    return content_hash(payload)


def verify_package_hash(package: SealedContextPackage) -> bool:
    return package.package_hash == compute_package_hash(package)
