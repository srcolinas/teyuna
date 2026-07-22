.PHONY: install dev format lint test check publish clean setup

clean:
	rm -rf .venv __pycache__ .mypy_cache .ruff_cache dist
	rm -rf src/__pycache__ src/**/__pycache__

setup:
	uv sync --dev

dev:
	uv sync --dev

format:
	uv run ruff format src
	uv run ruff check --fix src

lint:
	uv run ruff format . --check
	uv run ruff check src
	uv run mypy .

test:
	echo "No tests to run"

check: lint test
	@echo "All checks passed!"

publish:
	uv build
	uv publish
