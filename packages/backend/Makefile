.PHONY: install dev format lint test check run

clean:
	rm -rf .venv __pycache__ .mypy_cache .ruff_cache
	rm -rf src/__pycache__ src/**/__pycache__
	rm -rf tests/__pycache__ tests/**/__pycache__
	rm -rf .coverage .coverage.* coverage.xml htmlcov
	
setup:
	uv sync --all-packages --dev
	uv run pre-commit install

dev:
	uv sync --all-packages --dev

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

lint:
	uv run ruff format . --check
	uv run ruff check src tests
	uv run mypy .

slow-test:
	uv run pytest -m "slow" tests -vv

test:
	uv run pytest -n auto -m "not slow" tests -vv

check: lint test
	@echo "All checks passed!"

coverage:
	uv run pytest -n auto -m "not slow" tests --cov=src

coverage-html:
	uv run pytest -n auto -m "not slow" tests --cov=src --cov-report=html

