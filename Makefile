.PHONY: lint format test check-all install dev

# Install dependencies
install:
	uv sync

# Install development dependencies
dev:
	uv sync --dev

# Format code
format:
	uv run ruff format app tests
	uv run ruff check app tests --fix

# Lint code (without fixing)
lint:
	uv run ruff check app tests

# Run tests
test:
	uv run pytest tests -v

# Run tests with coverage
test-cov:
	uv run pytest tests --cov=app --cov-report=term-missing

# Check everything before commit
check-all: lint test
	@echo "✅ All checks passed! Ready to commit."

# Quick check (lint + basic test)
check:
	uv run ruff check app tests
	uv run pytest tests -q

# Run development server
run:
	uv run uvicorn app.main:app --reload --port 8000

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
