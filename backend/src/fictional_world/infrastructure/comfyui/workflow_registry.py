"""Versioned workflow registry (handbook 16 §8.2/§8.3; S4-IMG-001).

Workflows are stored as exported API-format JSON.  The registry loads them
from a local directory by version slug.  It never scrapes the interactive
ComfyUI graph at runtime.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

_DEFAULT_DIR = Path(__file__).parent.parent.parent.parent.parent / "config" / "comfyui_workflows"


class WorkflowRegistry:
    """Load and cache versioned workflow JSON files from a directory."""

    def __init__(self, workflows_dir: Path | None = None) -> None:
        self._dir = workflows_dir or _DEFAULT_DIR
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, version: str) -> dict[str, Any]:
        """Return the workflow dict for *version*.

        Raises ``KeyError`` if the version file is not found.
        """
        if version in self._cache:
            return self._cache[version]

        candidates = list(self._dir.glob(f"{version}.json"))
        if not candidates:
            raise KeyError(
                f"Workflow version '{version}' not found in {self._dir}. "
                f"Available: {[p.stem for p in self._dir.glob('*.json')]}"
            )
        raw = candidates[0].read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(raw)
        self._cache[version] = data
        return data

    def hash(self, version: str) -> str:
        """Return SHA-256 of the raw workflow JSON for the given version."""
        workflow = self.load(version)
        raw = json.dumps(workflow, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()

    def list_versions(self) -> list[str]:
        """Return all available workflow version slugs."""
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def metadata(self, version: str) -> dict[str, Any]:
        """Return the ``_meta`` block of a workflow, or empty dict."""
        wf = self.load(version)
        meta_raw = wf.get("_meta")
        if isinstance(meta_raw, dict):
            return {str(k): v for k, v in cast(dict[str, Any], meta_raw).items()}
        return {}
