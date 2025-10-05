.PHONY: help setup install dev-install lint format test quick-test run run-orchestrator mcp-check agent-run-all clean build

help:
	@echo "AgSense Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete development setup"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run all linting (ruff, black, mypy)"
	@echo "  make format         - Format code automatically"
	@echo "  make test           - Run tests with coverage"
	@echo "  make quick-test     - Quick test run (no coverage)"
	@echo ""
	@echo "MCP Simulation:"
	@echo "  make mcp-check      - Check MCP readiness"
	@echo "  make agent-run-all  - Run all agents with trace"
	@echo "  make mcp-demo       - Full MCP demo (check + run)"
	@echo ""
	@echo "Agent Management:"
	@echo "  make run            - Start all agents"
	@echo "  make run-orchestrator - Start orchestrator only"
	@echo ""
	@echo "Build & Release:"
	@echo "  make build          - Build all packages"
	@echo "  make clean          - Clean build artifacts"

setup:
	@echo "🚀 Setting up AgSense development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv sync --dev
	@echo "📦 Installing pre-commit hooks..."
	uv run pre-commit install || echo "⚠️  pre-commit not available"
	@echo "✅ Setup complete! Run 'ags mcp-check' to validate."

install:
	uv sync

dev-install:
	uv sync --dev

lint:
	@echo "🔍 Running linters..."
	uv run ruff check packages/
	uv run black --check packages/
	uv run mypy packages/ --ignore-missing-imports || true

format:
	@echo "✨ Formatting code..."
	uv run ruff check --fix packages/
	uv run black packages/

test:
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ -v --tb=short --cov=packages --cov-report=term-missing --cov-report=html || true

quick-test:
	@echo "🧪 Running quick tests..."
	uv run pytest tests/ -v --tb=short || true

mcp-check:
	@echo "🧠 Checking MCP readiness..."
	@export AGS_MCP_ENABLED=true && uv run ags mcp-check

agent-run-all:
	@echo "🔄 Running agent simulation..."
	@export AGS_MCP_ENABLED=true && uv run ags agent run all --trace

mcp-demo: mcp-check agent-run-all
	@echo ""
	@echo "✅ MCP demo complete!"

run:
	@echo "🚀 Starting all agents..."
	@echo "Note: This is a placeholder. Use 'make agent-run-all' for simulation."
	@make agent-run-all

run-orchestrator:
	@echo "🎯 Starting orchestrator..."
	cd packages/agent-orchestrator && uv run python main.py

build:
	@echo "📦 Building packages..."
	uv build

clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage coverage.xml
	@echo "✅ Clean complete!"
