"""Object-storage prefix policy (handbook 29 S4-STORAGE-001).

Canonical prefix layout:
  worlds/{world_id}/events/{event_id}/images/{job_id}/{asset_id}.{ext}
  worlds/{world_id}/references/characters/{character_id}/{asset_id}.{ext}
  worlds/{world_id}/references/locations/{location_id}/{asset_id}.{ext}
  worlds/{world_id}/exports/{export_id}/...
  workflows/comfyui/{workflow_version}/...
"""

from __future__ import annotations

from uuid import UUID

DEFAULT_BUCKET = "fictional-world-assets"
WORKFLOW_BUCKET = "fictional-world-workflows"


def event_image_prefix(world_id: UUID, event_id: UUID, job_id: UUID) -> str:
    """Return the key prefix for a generated event image."""
    return f"worlds/{world_id}/events/{event_id}/images/{job_id}/"


def event_image_key(
    world_id: UUID,
    event_id: UUID,
    job_id: UUID,
    asset_id: UUID,
    ext: str = "webp",
) -> str:
    """Return a complete, immutable object key for an event image."""
    return f"worlds/{world_id}/events/{event_id}/images/{job_id}/{asset_id}.{ext}"


def character_reference_key(
    world_id: UUID,
    character_id: UUID,
    asset_id: UUID,
    ext: str = "webp",
) -> str:
    return f"worlds/{world_id}/references/characters/{character_id}/{asset_id}.{ext}"


def location_reference_key(
    world_id: UUID,
    location_id: UUID,
    asset_id: UUID,
    ext: str = "webp",
) -> str:
    return f"worlds/{world_id}/references/locations/{location_id}/{asset_id}.{ext}"


def export_prefix(world_id: UUID, export_id: UUID) -> str:
    return f"worlds/{world_id}/exports/{export_id}/"


def workflow_key(workflow_version: str, filename: str) -> str:
    """Return the object key for a stored workflow JSON file."""
    return f"workflows/comfyui/{workflow_version}/{filename}"
