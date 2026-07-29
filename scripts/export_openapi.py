#!/usr/bin/env python3
"""Export Stage 0 OpenAPI document to docs/generated/openapi.json."""

from __future__ import annotations

import json

from fictional_world.config.settings import (
    ApiSettings,
    AppSettings,
    AuthSettings,
    repo_root,
)
from fictional_world.interfaces.http.app import create_app


def main() -> None:
    # Avoid touching a real database while generating schema.
    settings = AppSettings(
        api=ApiSettings(bind_host="127.0.0.1", bind_port=8000),
        auth=AuthSettings(enabled=False, allow_insecure_public_bind=False),
    )
    application = create_app(settings=settings)
    schema = application.openapi()
    out = repo_root() / "docs" / "generated" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(repo_root())}")


if __name__ == "__main__":
    main()
