.PHONY: help dev test lint format clean docker-up docker-down docker-logs

help:  ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev:  ## Start development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests with coverage
	pytest -ra -q --cov=app --cov-report=term-missing

test-ci:  ## Run tests for CI (with XML output)
	pytest -ra -q --cov=app --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

lint:  ## Run linting (ruff)
	ruff check app tests

format:  ## Format code with black
	black app tests

format-check:  ## Check code formatting
	black --check app tests

type-check:  ## Run type checking with mypy
	mypy app

clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage dist/ build/

docker-up:  ## Start Docker services
	docker-compose up -d

docker-down:  ## Stop Docker services
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f

docker-clean:  ## Stop and remove Docker containers and volumes
	docker-compose down -v

db-upgrade:  ## Run database migrations
	alembic upgrade head

db-downgrade:  ## Rollback database migration
	alembic downgrade -1

db-reset:  ## Reset database (dangerous!)
	alembic downgrade base && alembic upgrade head

install:  ## Install dependencies
	pip install -e ".[dev]"

check: lint type-check test  ## Run all checks (lint, type-check, test)

.DEFAULT_GOAL := help
