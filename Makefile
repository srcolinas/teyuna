# Teyuna - The Lost City
# Root Makefile

.PHONY: all setup format lint test check run simulate stop clean

# Default target
all: check

# Clean cache files and artifacts
clean:
	rm -rf .venv
	cd packages/teyuna-core && make clean
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
	cd packages/teyuna-core && make format
	cd packages/backend && make format
	cd packages/sdk-python && make format
	cd apps/frontend && make format

# Lint all code
lint:
	cd packages/teyuna-core && make lint
	cd packages/backend && make lint
	cd packages/sdk-python && make lint
	cd apps/frontend && make lint

# Run all tests
test:
	cd packages/teyuna-core && make test
	cd packages/backend && make test
	cd packages/sdk-python && make test
	cd apps/frontend && make test

# Run all checks
check:
	cd packages/teyuna-core && make check
	cd packages/backend && make check
	cd packages/sdk-python && make check
	cd apps/frontend && make check

# Host ports published by Docker Compose (see docker-compose.yml)
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 5173
export BACKEND_PORT FRONTEND_PORT
# Keep the frontend build's API URL aligned with the published backend port.
VITE_API_URL ?= http://localhost:$(BACKEND_PORT)
export VITE_API_URL

# Start backend + frontend with Docker Compose (attached so service URLs stay visible)
run:
	docker compose up --build
	@echo "Backend:  http://127.0.0.1:$(BACKEND_PORT)"
	@echo "Frontend: http://127.0.0.1:$(FRONTEND_PORT)"

# Detach Compose, wait for health, then create a game and join with agents
simulate:
	docker compose up --build --detach
	@echo "Waiting for backend at http://127.0.0.1:$(BACKEND_PORT)/health ..."
	@until curl -sf "http://127.0.0.1:$(BACKEND_PORT)/health" >/dev/null; do sleep 1; done
	@echo "Backend:  http://127.0.0.1:$(BACKEND_PORT)"
	@echo "Frontend: http://127.0.0.1:$(FRONTEND_PORT)"
	@GAME_ID=$$(uv run teyuna-simulate create --host "http://127.0.0.1:$(BACKEND_PORT)"); \
	echo "Watch: http://127.0.0.1:$(FRONTEND_PORT)/?gameId=$$GAME_ID"; \
	uv run teyuna-simulate join "$$GAME_ID" --host "http://127.0.0.1:$(BACKEND_PORT)" \
		stochastic:alice stochastic:bob stochastic:carol

# Stop Docker Compose services
stop:
	docker compose down
