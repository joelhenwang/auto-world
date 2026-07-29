"""Filesystem registry for versioned prompt assets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from fictional_world.prompts.metadata import PromptMeta


class PromptRegistryError(ValueError):
    """Raised when prompt assets are missing, duplicated, or inconsistent."""


@dataclass(frozen=True, slots=True)
class PromptAsset:
    """One validated prompt version and its immutable template sources."""

    meta: PromptMeta
    system_template: str
    user_template: str
    source_hash: str


def default_prompt_root() -> Path:
    """Return the repository backend prompt-asset directory."""

    return Path(__file__).resolve().parents[3] / "prompts"


class PromptRegistry:
    """Load prompt assets by stable prompt ID."""

    def __init__(self, prompt_root: Path | None = None) -> None:
        self._prompt_root = (prompt_root or default_prompt_root()).resolve()
        self._assets: dict[str, PromptAsset] | None = None

    def load(self, prompt_id: str) -> PromptAsset:
        """Return a registered prompt, failing closed for an unknown ID."""

        try:
            return self._load_all()[prompt_id]
        except KeyError as exc:
            raise PromptRegistryError(f"unknown prompt_id: {prompt_id}") from exc

    def list_active(self) -> tuple[PromptMeta, ...]:
        """List active prompt metadata in stable prompt-ID order."""

        return tuple(
            asset.meta
            for _, asset in sorted(self._load_all().items())
            if asset.meta.status == "active"
        )

    def _load_all(self) -> dict[str, PromptAsset]:
        if self._assets is not None:
            return self._assets
        if not self._prompt_root.is_dir():
            raise PromptRegistryError(f"prompt root does not exist: {self._prompt_root}")

        assets: dict[str, PromptAsset] = {}
        for meta_path in sorted(self._prompt_root.glob("*/v*.meta.yaml")):
            asset = self._load_asset(meta_path)
            if asset.meta.prompt_id in assets:
                raise PromptRegistryError(f"duplicate prompt_id: {asset.meta.prompt_id}")
            assets[asset.meta.prompt_id] = asset
        self._assets = assets
        return assets

    @staticmethod
    def _load_asset(meta_path: Path) -> PromptAsset:
        try:
            raw_meta: object = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            prompt_meta = PromptMeta.model_validate(raw_meta)
        except (OSError, ValidationError, yaml.YAMLError) as exc:
            raise PromptRegistryError(f"invalid prompt metadata: {meta_path}") from exc

        expected_stem = f"v{prompt_meta.version}"
        expected_id = f"{meta_path.parent.name}_v{prompt_meta.version}"
        if meta_path.name != f"{expected_stem}.meta.yaml":
            raise PromptRegistryError(f"metadata filename/version mismatch: {meta_path}")
        if prompt_meta.prompt_id != expected_id:
            raise PromptRegistryError(f"prompt ID/path mismatch: {meta_path}")

        system_path = meta_path.with_name(f"{expected_stem}.system.md.j2")
        user_path = meta_path.with_name(f"{expected_stem}.user.md.j2")
        try:
            system_template = system_path.read_text(encoding="utf-8")
            user_template = user_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise PromptRegistryError(f"missing template for {prompt_meta.prompt_id}") from exc

        digest_payload = json.dumps(
            {
                "meta": prompt_meta.model_dump(mode="json"),
                "system_template": system_template,
                "user_template": user_template,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        source_hash = hashlib.sha256(digest_payload.encode()).hexdigest()
        return PromptAsset(
            meta=prompt_meta,
            system_template=system_template,
            user_template=user_template,
            source_hash=source_hash,
        )
