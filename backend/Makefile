.PHONY: install dev format lint test check run

clean:
	rm -rf .venv __pycache__ src/__pycache__ src/**/__pycache__ .mypy_cache .ruff_cache
	
setup:
	uv sync --dev
	uv run pre-commit install

dev:
	uv sync --dev

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:
	uv run ruff format . --check
	uv run ruff check src tests
	uv run mypy .

test:
	uv run pytest tests -vv

check: lint test
	@echo "All checks passed!"

run:
	uv run uvicorn teyuna.main:app --reload --host 0.0.0.0 --port 8000
