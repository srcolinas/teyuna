# Teyuna - The Lost City
# Root Makefile

.PHONY: all install format lint test check run clean

# Default target
all: check

# Clean cache files and artifacts
clean:
	cd backend && make clean

# Install all dependencies
setup:
	cd backend && make setup

# Format all code
format:
	cd backend && make format

# Lint all code
lint:
	cd backend && make lint

# Run all tests
test:
	cd backend && make test

# Run all checks
check:
	cd backend && make check

# Run with Docker/Podman Compose
run:
	# TODO: incorporate fronted when implemented
	cd backend && make run

# Stop Docker/Podman services
stop:
	echo "Not Implemented"

