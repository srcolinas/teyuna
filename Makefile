# Teyuna - The Lost City
# Root Makefile

.PHONY: all setup format lint test check run stop clean

# Default target
all: check

# Clean cache files and artifacts
clean:
	rm -rf .venv
	cd packages/shared-core && make clean
	cd packages/backend && make clean
	cd packages/sdk-python && make clean

# Install all workspace dependencies
setup:
	uv sync --all-packages --dev
	uv run pre-commit install

# Format all code
format:
	cd packages/shared-core && make format
	cd packages/backend && make format
	cd packages/sdk-python && make format

# Lint all code
lint:
	cd packages/shared-core && make lint
	cd packages/backend && make lint
	cd packages/sdk-python && make lint

# Run all tests
test:
	cd packages/shared-core && make test
	cd packages/backend && make test
	cd packages/sdk-python && make test

# Run all checks
check:
	cd packages/shared-core && make check
	cd packages/backend && make check
	cd packages/sdk-python && make check

# Run with Docker/Podman Compose
run:
	mkdir -p logs
	docker compose up --build --detach

# Stop Docker/Podman services
stop:
	docker compose down
