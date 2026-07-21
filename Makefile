# Teyuna - The Lost City
# Root Makefile

.PHONY: all setup format lint test check run stop clean

# Default target
all: check

# Clean cache files and artifacts
clean:
	cd backend && make clean
	cd teyuna-players && make clean

# Install all dependencies
setup:
	cd backend && make setup
	cd teyuna-players && make setup

# Format all code
format:
	cd backend && make format
	cd teyuna-players && make format

# Lint all code
lint:
	cd backend && make lint
	cd teyuna-players && make lint

# Run all tests
test:
	cd backend && make test
	cd teyuna-players && make test

# Run all checks
check:
	cd backend && make check
	cd teyuna-players && make check

# Run with Docker/Podman Compose
run:
	mkdir -p logs
	docker compose up --build --detach

# Stop Docker/Podman services
stop:
	docker compose down
