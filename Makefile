# Thin aliases — underlying commands remain the source of truth (handbook 20 §7).
# Targets that depend on later Stage 0 tasks are stubs that print guidance.

.PHONY: help bootstrap sync test lint format typecheck check compose-config compose-up compose-down migrate seed

help:
	@echo "S0-ENG-001 bootstrap aliases:"
	@echo "  make sync            uv sync"
	@echo "  make test            pytest (suite grows in S0-QA-001+)"
	@echo "  make lint            ruff check"
	@echo "  make format          ruff format --check"
	@echo "  make typecheck       basedpyright (strict gate is S0-ENG-002)"
	@echo "  make check           format + lint"
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

check: format lint

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
