"""Generate JSON Schemas for Stage 0 domain contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fictional_world.domain.effects.commands import EFFECT_COMMAND_TYPES
from fictional_world.domain.events import CommittedWorldEvent, Provenance
from fictional_world.domain.knowledge import ObservationRecord
from fictional_world.domain.memory import EmbeddingMetadata, MemoryRecord
from fictional_world.domain.scenes import ActionProposal, PhaseRun, SceneResolution, SceneRun
from fictional_world.domain.tasks import TaskRun
from fictional_world.domain.time import FictionalTime

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "generated" / "domain-schemas"

MODELS: list[type[object]] = [
    FictionalTime,
    Provenance,
    PhaseRun,
    SceneRun,
    ActionProposal,
    SceneResolution,
    CommittedWorldEvent,
    ObservationRecord,
    MemoryRecord,
    EmbeddingMetadata,
    TaskRun,
    *EFFECT_COMMAND_TYPES,
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    for model in MODELS:
        name = getattr(model, "__name__", "Unknown")
        schema = model.model_json_schema()  # type: ignore[attr-defined]
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest[name] = str(path.relative_to(ROOT))
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(manifest)} schemas to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
