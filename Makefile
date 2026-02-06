# Teyuna - The Lost City
# Root Makefile

.PHONY: all install format lint test check run clean

# Default target
all: check

# Install all dependencies
install:
	cd backend && make install
	cd frontend && make install
	cd ai_client && make install

# Format all code
format:
	cd backend && make format
	cd frontend && make format
	cd ai_client && make format

# Lint all code
lint:
	cd backend && make lint
	cd frontend && make lint
	cd ai_client && make lint

# Run all tests
test:
	cd backend && make test
	cd frontend && make test
	cd ai_client && make test

# Run all checks
check:
	cd backend && make check
	cd frontend && make check
	cd ai_client && make check

# Run with Docker/Podman Compose
run:
	podman compose up --build

# Stop Docker/Podman services
stop:
	podman compose down

# Clean build artifacts
clean:
	rm -rf backend/.venv backend/__pycache__ backend/src/**/__pycache__
	rm -rf frontend/node_modules frontend/dist
	rm -rf ai_client/.venv ai_client/__pycache__ ai_client/src/**/__pycache__
	podman compose down --rmi local 2>/dev/null || true
