# Thin aliases — underlying commands remain the source of truth (handbook 20 §7).

.PHONY: help bootstrap sync test lint format typecheck check compose-config compose-up compose-down migrate seed export-schemas pre-commit verify-migrations

help:
	@echo "Stage 0 aliases:"
	@echo "  make sync / test / lint / format / typecheck / check"
	@echo "  make export-schemas / verify-migrations / migrate"
	@echo "  make compose-up / compose-down / bootstrap"

sync:
	uv sync

bootstrap: sync compose-up
	@echo "Run: make migrate (seed arrives with S0-CONTENT-001)"

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

verify-migrations:
	uv run python scripts/verify_migrations.py

pre-commit:
	uv run pre-commit run --all-files

compose-config:
	docker compose config

compose-up:
	docker compose up -d postgres

compose-down:
	docker compose down

migrate:
	uv run alembic -c backend/alembic.ini upgrade head

seed:
	@echo "S0-CONTENT-001 not landed yet: uv run python scripts/seed_world.py"
