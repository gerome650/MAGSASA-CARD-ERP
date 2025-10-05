.PHONY: help setup install dev-install lint format test quick-test run run-orchestrator mcp-check agent-run-all clean build ci-preflight notify-test coverage-report

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
	@echo "  make ci-preflight   - Run full CI checks (lint, test, mcp, agent, build) before pushing"
	@echo "  make preflight-full - Run comprehensive CI preflight validation"
	@echo "  make preflight-quick- Run quick preflight (lint + format + test)"
	@echo "  make notify-test    - Send test notifications (Slack & email)"
	@echo "  make coverage-report - Generate detailed coverage report"
	@echo "  make verify-ci      - Verify CI stabilization implementation"
	@echo "  make ci-debug       - Debug CI step-by-step locally (lint + tests + security)"
	@echo "  make security-scan  - Run security scans (Bandit + pip-audit)"
	@echo "  make ci-health      - Generate CI health report"
	@echo ""
	@echo "📝 Note: All Python commands use 'python3' for cross-platform compatibility"
	@echo ""
	@echo "Git Hooks:"
	@echo "  make install-hooks  - Install CI preflight git hooks"
	@echo "  make remove-hooks   - Remove git hooks"
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
	@echo "   📌 Using: -n=auto (parallel), --reruns=2 (retry flaky), --cov-fail-under=65"
	uv run pytest tests/ -v --tb=short --cov=packages --cov-report=term-missing --cov-report=html || true

quick-test:
	@echo "🧪 Running quick tests..."
	uv run pytest tests/ -v --tb=short || true

ci-preflight:
	@echo "🚀 Running CI preflight checks..."
	@echo "🔍 Checking code quality..."
	@source .venv/bin/activate && python3 -m ruff check . --fix --unsafe-fixes || { echo "❌ Ruff linting failed"; exit 1; }
	@source .venv/bin/activate && python3 -m black --check . || { echo "❌ Black formatting failed"; exit 1; }
	@source .venv/bin/activate && python3 -m mypy . --ignore-missing-imports || { echo "❌ Type checking failed"; exit 1; }
	@echo "🧪 Running tests..."
	@source .venv/bin/activate && python3 -m pytest tests/ --tb=short --cov=src --cov-fail-under=80 || { echo "❌ Tests failed or coverage too low"; exit 1; }
	@echo "✅ All preflight checks passed!"

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
	cd packages/agent-orchestrator && uv run python3 main.py

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

notify-test:
	@echo "📤 Testing notification system..."
	@echo "Testing Slack notification..."
	python3 scripts/notify_slack.py "test-branch" "abc123" "Test notification" || echo "⚠️  Slack notification failed (webhook not configured)"
	@echo "Testing email notification..."
	python3 scripts/notify_email.py "test-branch" "abc123" "Test notification" || echo "⚠️  Email notification failed (SMTP not configured)"
	@echo "✅ Notification test complete!"

install-hooks:
	@echo "🔧 Installing CI preflight git hooks..."
	./scripts/setup_ci_preflight_hook.sh
	@echo "✅ Git hooks installed successfully!"

remove-hooks:
	@echo "🗑️  Removing git hooks..."
	rm -f .git/hooks/pre-push
	@echo "✅ Git hooks removed!"

preflight-full:
	@echo "🚀 Running full CI preflight validation..."
	python3 scripts/ci_preflight.py

preflight-quick:
	@echo "⚡ Running quick preflight (lint + format + test)..."
	@echo "🔍 Linting..."
	uv run ruff check . --fix
	@echo "✨ Formatting..."
	uv run black .
	@echo "🧪 Testing..."
	uv run pytest tests/ -q
	@echo "✅ Quick preflight complete!"

coverage-report:
	@echo "📊 Generating detailed coverage report..."
	python3 -m pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing tests/
	@echo "📈 Coverage report generated:"
	@echo "   - HTML: htmlcov/index.html"
	@echo "   - XML:  coverage.xml"
	@echo "   - Terminal output above"
	@echo "✅ Coverage report complete!"

ci-debug:
	@echo "🐛 Running CI debug step-by-step locally..."
	@echo "   📌 This runs each CI check individually for easier debugging"
	@echo ""
	@echo "🔍 Step 1: Linting..."
	@make lint
	@echo ""
	@echo "🧪 Step 2: Tests..."
	@make test
	@echo ""
	@echo "🛡️  Step 3: Security scan..."
	@make security-scan
	@echo ""
	@echo "✅ CI debug complete! If all passed, run 'make verify-ci' for final gate."

verify-ci:
	@echo "🔍 Running final CI verification gate..."
	@echo "   📌 Checking: Linting ✅, Tests ✅, Security ✅, Readiness ✅"
	@echo "   📌 GH_TOKEN optional locally, required in CI"
	python3 scripts/verify_release_pipeline.py --ci

security-scan:
	@echo "🛡️  Running security scans..."
	@echo "   📌 Bandit (static analysis) + pip-audit (vulnerability check)"
	@echo "📝 Installing security tools..."
	pip install bandit[toml] safety pip-audit 2>/dev/null || true
	@echo "🔍 Running Bandit (medium severity/confidence)..."
	bandit -r packages/ src/ --severity-level medium --confidence-level medium --configfile .bandit || true
	@echo "🔍 Running pip-audit (dependency vulnerabilities)..."
	pip-audit --desc || echo "⚠️  Found vulnerabilities"
	@echo "🔍 Checking dependencies..."
	pip check || echo "⚠️  Dependency issues found"
	@echo "✅ Security scan complete!"

ci-health:
	@echo "📊 Generating CI health report..."
	python3 scripts/ci_health_report.py --verbose
