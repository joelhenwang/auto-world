"""Profile loading for AppSettings."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

from fictional_world.config.settings import AppSettings, repo_root


def profile_path(profile_name: str, *, profiles_dir: Path | None = None) -> Path:
    root = profiles_dir if profiles_dir is not None else repo_root() / "config" / "profiles"
    path = root / f"{profile_name}.toml"
    if not path.is_file():
        msg = f"profile not found: {path}"
        raise FileNotFoundError(msg)
    return path


def load_profile_dict(profile_name: str, *, profiles_dir: Path | None = None) -> dict[str, object]:
    path = profile_path(profile_name, profiles_dir=profiles_dir)
    with path.open("rb") as handle:
        data = cast(dict[str, object], tomllib.load(handle))
    return data


def settings_from_profile(
    profile_name: str,
    *,
    profiles_dir: Path | None = None,
) -> AppSettings:
    """Build settings from a named TOML profile (env overlays via AppSettings() separately)."""

    data = load_profile_dict(profile_name, profiles_dir=profiles_dir)
    data.setdefault("profile", profile_name)
    return AppSettings.model_validate(data)
