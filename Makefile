# Thin aliases — underlying commands remain the source of truth (handbook 20 §7).

.PHONY: help bootstrap sync test lint format typecheck check compose-config compose-up compose-down migrate seed export-schemas pre-commit

help:
	@echo "Stage 0 aliases:"
	@echo "  make sync            uv sync"
	@echo "  make test            pytest (default excludes live/soak)"
	@echo "  make lint            ruff check"
	@echo "  make format          ruff format --check"
	@echo "  make typecheck       basedpyright (strict)"
	@echo "  make check           format + lint + typecheck"
	@echo "  make export-schemas  generate domain JSON Schemas"
	@echo "  make pre-commit      run pre-commit on all files"
	@echo "  make compose-config  validate compose.yaml"
	@echo "  make compose-up      start postgres"
	@echo "  make compose-down    stop compose services"
	@echo "  make bootstrap       sync + compose-up (migrate/seed later)"

sync:
	uv sync

bootstrap: sync compose-up
	@echo "Migrations and seed are owned by S0-DB-001 / S0-CONTENT-001 — not yet available."

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

typecheck:
	uv run basedpyright

check: format lint typecheck

export-schemas:
	uv run python scripts/generate_json_schemas.py

pre-commit:
	uv run pre-commit run --all-files

compose-config:
	docker compose config

compose-up:
	docker compose up -d postgres

compose-down:
	docker compose down

migrate:
	@echo "S0-DB-001 not landed yet: uv run alembic -c backend/alembic.ini upgrade head"

seed:
	@echo "S0-CONTENT-001 not landed yet: uv run python scripts/seed_world.py"
