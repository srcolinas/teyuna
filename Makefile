# Teyuna - The Lost City
# Root Makefile

.PHONY: all setup format lint test check run simulate stop clean

# Default target
all: check

# Clean cache files and artifacts
clean:
	rm -rf .venv
	cd packages/shared-core && make clean
	cd packages/backend && make clean
	cd packages/sdk-python && make clean
	cd apps/frontend && make clean

# Install all workspace dependencies
setup:
	uv sync --all-packages --dev
	uv run pre-commit install
	cd apps/frontend && make setup

# Format all code
format:
	cd packages/shared-core && make format
	cd packages/backend && make format
	cd packages/sdk-python && make format
	cd apps/frontend && make format

# Lint all code
lint:
	cd packages/shared-core && make lint
	cd packages/backend && make lint
	cd packages/sdk-python && make lint
	cd apps/frontend && make lint

# Run all tests
test:
	cd packages/shared-core && make test
	cd packages/backend && make test
	cd packages/sdk-python && make test
	cd apps/frontend && make test

# Run all checks
check:
	cd packages/shared-core && make check
	cd packages/backend && make check
	cd packages/sdk-python && make check
	cd apps/frontend && make check

# Start backend + frontend with Docker Compose (attached so service URLs stay visible)
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173

run:
	docker compose up --build

# Detach Compose, wait for health, then run agents in the foreground (with game id / tokens)
simulate:
	docker compose up --build --detach
	@echo "Waiting for backend at http://127.0.0.1:$(BACKEND_PORT)/health ..."
	@until curl -sf "http://127.0.0.1:$(BACKEND_PORT)/health" >/dev/null; do sleep 1; done
	@echo "Backend:  http://127.0.0.1:$(BACKEND_PORT)"
	@echo "Frontend: http://127.0.0.1:$(FRONTEND_PORT)"
	FRONTEND_PORT=$(FRONTEND_PORT) uv run teyuna-simulate --host "http://127.0.0.1:$(BACKEND_PORT)" stochastic:alice stochastic:bob stochastic:carol

# Stop Docker Compose services
stop:
	docker compose down
