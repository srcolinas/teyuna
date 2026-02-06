.PHONY: install dev format lint test check run

install:
	uv sync

dev:
	uv sync --dev

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:
	uv run ruff check src tests
	uv run mypy .

test:
	uv run pytest tests -v

check: lint test
	@echo "All checks passed!"

run:
	uv run uvicorn teyuna.main:app --reload --host 0.0.0.0 --port 8000
