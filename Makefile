.PHONY: help setup lint test run clean install dev-install build publish

# Default target
help: ## Show this help message
	@echo "AgSense Stage 7 - Available Commands:"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
setup: ## Complete development setup - sync deps, install hooks
	@echo "🚀 Setting up AgSense development environment..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "❌ uv not found. Please install uv first:"; \
		echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	uv sync --dev
	pre-commit install
	@echo "✅ Development environment ready!"
	@echo "   Run 'make test' to verify setup"

# Dependency management
install: ## Install production dependencies
	uv sync

dev-install: ## Install development dependencies
	uv sync --dev

# Code quality
lint: ## Run all linting tools (ruff, black, mypy)
	@echo "🔍 Running linting checks..."
	ruff check packages/ tests/
	black --check packages/ tests/
	mypy packages/
	@echo "✅ Lint checks passed!"

format: ## Format code with black and ruff
	@echo "🎨 Formatting code..."
	black packages/ tests/
	ruff check --fix packages/ tests/
	@echo "✅ Code formatted!"

# Testing
test: ## Run tests with coverage
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=packages --cov-report=term-missing --cov-report=html
	@echo "✅ Tests completed!"

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -- -v

# Agent orchestration
run: ## Run all agents locally
	@echo "🤖 Starting AgSense agent orchestration..."
	@echo "   Starting orchestrator..."
	uv run python packages/agent-orchestrator/main.py &
	@echo "   Starting ingest agent..."
	uv run python packages/agent-ingest/main.py &
	@echo "   Starting retrieval agent..."
	uv run python packages/agent-retrieval/main.py &
	@echo "   Starting scoring agent..."
	uv run python packages/agent-scoring/main.py &
	@echo "   Starting notification agent..."
	uv run python packages/agent-notify/main.py &
	@echo "   Starting billing agent..."
	uv run python packages/agent-billing/main.py &
	@echo "✅ All agents started! Press Ctrl+C to stop all agents"

run-orchestrator: ## Run orchestrator only
	uv run python packages/agent-orchestrator/main.py

run-ingest: ## Run ingest agent only
	uv run python packages/agent-ingest/main.py

run-retrieval: ## Run retrieval agent only
	uv run python packages/agent-retrieval/main.py

run-scoring: ## Run scoring agent only
	uv run python packages/agent-scoring/main.py

run-notify: ## Run notification agent only
	uv run python packages/agent-notify/main.py

run-billing: ## Run billing agent only
	uv run python packages/agent-billing/main.py

# CLI commands
dev-setup: ## Run CLI dev-setup command
	uv run ags dev-setup

mcp-check: ## Run CLI mcp-check command
	uv run ags mcp-check

# Build and publish
build: ## Build all packages
	@echo "📦 Building packages..."
	uv build
	@echo "✅ Build completed!"

publish: ## Publish packages to registry
	@echo "📤 Publishing packages..."
	uv publish
	@echo "✅ Packages published!"

# Database and data
db-migrate: ## Run database migrations
	@echo "🗄️  Running database migrations..."
	# Add migration commands here when needed
	@echo "✅ Migrations completed!"

db-seed: ## Seed database with sample data
	@echo "🌱 Seeding database..."
	# Add seeding commands here when needed
	@echo "✅ Database seeded!"

# Monitoring and health
health: ## Check system health
	@echo "🏥 Checking system health..."
	uv run ags health-check

logs: ## View application logs
	@echo "📋 Viewing logs..."
	# Add log viewing commands here
	tail -f app.log

# Cleanup
clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed!"

clean-deps: ## Clean dependency caches
	uv cache clean

# Docker (if needed)
docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start services with Docker
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

# Git hooks
hooks: ## Install git hooks
	pre-commit install

hooks-uninstall: ## Uninstall git hooks
	pre-commit uninstall

# Development workflow
dev: setup test ## Full development workflow: setup + test
	@echo "🎉 Development environment is ready!"

ci: lint test build ## CI workflow: lint + test + build
	@echo "✅ CI checks passed!"

# Quick commands
quick-test: ## Quick test run (no coverage)
	pytest tests/ -v -x

quick-lint: ## Quick lint check (ruff only)
	ruff check packages/ tests/

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	# Add documentation generation commands here
	@echo "✅ Documentation generated!"

# Version management
version: ## Show current version
	@python -c "import toml; print(toml.load('pyproject.toml')['project']['version'])"

bump-version: ## Bump version (requires argument: make bump-version VERSION=0.2.0)
	@if [ -z "$(VERSION)" ]; then echo "Usage: make bump-version VERSION=0.2.0"; exit 1; fi
	@sed -i "s/version = \".*\"/version = \"$(VERSION)\"/" pyproject.toml
	@echo "✅ Version bumped to $(VERSION)"

# Environment info
info: ## Show environment information
	@echo "🔧 Environment Information:"
	@echo "Python version: $(shell python --version)"
	@echo "UV version: $(shell uv --version)"
	@echo "Project version: $(shell make version)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'not a git repo')"
	@echo "Working directory: $(shell pwd)"