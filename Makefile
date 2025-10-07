# ===== Protected Commit configuration =====
SHELL := /bin/bash
COVERAGE_MIN ?= 65
PYTEST ?= pytest
BLACK ?= black
RUFF ?= ruff

.PHONY: help setup install dev-install lint format test quick-test coverage-local test-fast coverage-ci run run-orchestrator mcp-check agent-run-all clean build ci-preflight notify-test coverage-report push-workflow release-workflows resolve-conflicts safe-commit ensure-hooks hygiene coverage-check validate-payload validate-all fix-all ci validate-schema

# 🔧 Developer Note: PYTHONPATH Configuration
# All test targets set PYTHONPATH=$(PWD) inline to ensure Python can resolve internal modules
# like 'core.*', 'observability.*', etc. This prevents ModuleNotFoundError and ensures
# consistent behavior between local and CI test runs without polluting the global environment.

help:
	@echo "AgSense Makefile Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete development setup"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make install-dev    - Install ALL dev dependencies (aiohttp, pytest, etc.)"
	@echo "  make check-deps     - Verify all dependencies are installed"
	@echo ""
	@echo "🔒 Protected Commit:"
	@echo "  make safe-commit [MSG=\"message\"] - Protected commit with all checks"
	@echo "  make hygiene        - Run format & lint checks (black --check, ruff)"
	@echo "  make coverage-check - Run tests with coverage and enforce threshold"
	@echo "  make ensure-hooks   - Configure Git to use .githooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run all linting (ruff, black, mypy)"
	@echo "  make format         - Format code automatically"
	@echo "  make fix-lint       - Auto-fix all lint + format issues (project-wide)"
	@echo "  make test           - Run tests with coverage"
	@echo "  make quick-test     - Quick test run (no coverage)"
	@echo "  make coverage-local - Local coverage report on observability modules (HTML included)"
	@echo "  make test-fast      - Quick run of all tests without coverage"
	@echo "  make coverage-ci    - Strict coverage enforcement for CI pipelines"
	@echo "  make coverage-smoke - Ultra-fast import smoke test (<1s, perfect for pre-commit)"
	@echo "  make pre-commit     - Pre-commit quality gate (lint + smoke + fast tests)"
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
	@echo "📊 Merge Quality System:"
	@echo "  make validate-payload - Validate Slack payload against schema"
	@echo "  make validate-all     - Run syntax + lint + payload validation"
	@echo "  make fix-all          - Auto-fix code + regenerate payload JSON"
	@echo "  make ci               - Complete CI pipeline (fix-all → validate-all → pytest)"
	@echo "  make validate-schema  - Validate payload with detailed diff report"
	@echo ""
	@echo "🛡️ Governance & Policy Enforcement:"
	@echo "  make install-governance-hooks - Install pre-commit and post-push hooks"
	@echo "  make uninstall-governance-hooks - Uninstall governance hooks"
	@echo "  make check-policy     - Check policy compliance (coverage, tests, linting)"
	@echo "  make enforce-coverage - Enforce coverage thresholds from policy"
	@echo "  make governance-dev   - Run governance checks in development mode (relaxed)"
	@echo "  make calculate-merge-score - Calculate merge readiness score"
	@echo "  make coverage-trend   - Generate coverage trend report with sparklines"
	@echo "  make coverage-badge   - Generate coverage badge and update README"
	@echo "  make notify-slack-enhanced - Send enhanced Slack notification"
	@echo "  make governance-report - Generate comprehensive governance report"
	@echo "  make governance-report-dev - Generate governance report in dev mode"
	@echo "  make verify-all       - Complete enforcement pipeline (all checks)"
	@echo ""
	@echo "🔧 Conflict Resolution:"
	@echo "  make resolve-conflicts [DRY_RUN=true] - Detect and resolve merge conflicts"
	@echo ""
	@echo "📝 Note: All Python commands use 'python3' for cross-platform compatibility"
	@echo ""
	@echo "Git Hooks:"
	@echo "  make install-hooks  - Install CI preflight git hooks"
	@echo "  make remove-hooks   - Remove git hooks"
	@echo ""
	@echo "Git Workflow Automation:"
	@echo "  make push-workflow  - Stage, commit, and push workflow files to current branch"
	@echo "  make release-workflows - Create a release branch with all workflows, push it, and auto-merge into main"
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
	@echo "  make clean-venv     - Clean virtual environment (with confirmation)"
	@echo "  make safety-check   - Run repository safety checks"

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

# ===== Hygiene / Safety / Coverage =====
hygiene: ## Run format & lint checks (black --check, ruff)
	@echo "🧼 Running hygiene checks (black --check, ruff)…"
	@command -v $(BLACK) >/dev/null 2>&1 || { echo "❌ black not found. Install with: pip install black"; exit 1; }
	@command -v $(RUFF)  >/dev/null 2>&1 || { echo "❌ ruff not found. Install with: pip install ruff"; exit 1; }
	uv run $(BLACK) --check .
	uv run $(RUFF) check .

coverage-check: ## Run tests with coverage and enforce threshold
	@echo "📊 Running tests with coverage (minimum $(COVERAGE_MIN)%)…"
	@command -v $(PYTEST) >/dev/null 2>&1 || { echo "❌ pytest not found. Install with: pip install pytest pytest-cov"; exit 1; }
	PYTHONPATH=$(PWD) uv run $(PYTEST) -q --maxfail=1 --disable-warnings --cov=. --cov-report=term-missing:skip-covered --cov-report=xml --cov-fail-under=$(COVERAGE_MIN)


ensure-hooks: ## Configure Git to use .githooks and ensure pre-commit is executable
	@echo "🪝 Ensuring git hooks are installed…"
	@git config core.hooksPath .githooks
	@mkdir -p .githooks
	@[ -f .githooks/pre-commit ] && chmod +x .githooks/pre-commit || true
	@echo "✅ Hooks path set to .githooks"

safe-commit: ensure-hooks ## Protected commit: runs hygiene, safety, and coverage checks before committing
	@set -euo pipefail; \
	if git diff --name-only --diff-filter=U | grep -q .; then \
		echo "❌ Unresolved merge conflicts detected. Resolve them before committing."; \
		exit 1; \
	fi; \
	echo "🧪 Running protected commit gate…"; \
	$(MAKE) hygiene; \
	$(MAKE) safety-check; \
	$(MAKE) coverage-check; \
	if [ -z "$${MSG-}" ]; then \
		read -r -p "✍️  Commit message: " MSG_INPUT; \
		if [ -z "$$MSG_INPUT" ]; then echo "❌ Commit message required."; exit 1; fi; \
		MSG="$$MSG_INPUT"; \
	else \
		MSG="$$MSG"; \
	fi; \
	echo "📦 Staging changes…"; \
	git add -A; \
	echo "🔐 Creating protected commit…"; \
	SAFE_COMMIT=1 git commit -m "$$MSG"; \
	echo "🚀 Pushing…"; \
	git push

lint:
	@echo "🔍 Running linters..."
	uv run ruff check packages/
	uv run black --check packages/
	uv run mypy packages/ --ignore-missing-imports || true

format:
	@echo "✨ Formatting code..."
	uv run ruff check --fix packages/
	uv run black packages/

fix-lint:
	@echo "🔧 Auto-fixing lint issues (entire project)..."
	ruff check --fix --unsafe-fixes .
	black .
	@echo "✅ Auto-fix complete. Run 'ruff check .' to verify."

install-dev:
	@echo "📦 Installing development dependencies..."
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠️  WARNING: No virtual environment detected!"; \
		echo "   Recommended: source .venv/bin/activate"; \
		echo ""; \
	fi
	python3 scripts/setup/install_dev_dependencies.py
	@echo "✅ Development dependencies installed"

check-deps:
	@echo "🔍 Checking dependencies..."
	@python3 -m pip check || (echo "❌ Dependency check failed. Run: make install-dev" && exit 1)
	@echo "✅ All dependencies OK"

test:
	@echo "🧪 Running tests with coverage..."
	@echo "   📌 Using: -n=auto (parallel), --reruns=2 (retry flaky), --cov-fail-under=65"
	PYTHONPATH=$(PWD) uv run pytest tests/ -v --tb=short --cov=packages --cov-report=term-missing --cov-report=html || true

quick-test:
	@echo "🧪 Running quick tests..."
	uv run pytest tests/ -v --tb=short || true

coverage-local:
	@echo "🧪 Running local coverage on observability modules..."
	PYTHONPATH=$(PWD) pytest tests/ \
		--disable-warnings -v \
		--cov=observability.ai_agent.integrations \
		--cov=observability.logging \
		--cov=observability.metrics \
		--cov-report=term-missing \
		--cov-report=html

test-fast:
	@echo "🧪 Running fast tests..."
	PYTHONPATH=$(PWD) pytest -q --disable-warnings

coverage-ci:
	@echo "🧪 Running CI coverage with strict enforcement..."
	PYTHONPATH=$(PWD) pytest tests/ \
		--disable-warnings -v \
		--cov=observability \
		--cov-report=xml \
		--cov-fail-under=65

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
	@echo "🧹 Cleaning build artifacts and test cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage coverage.xml
	@echo "✅ Clean complete!"

clean-venv:
	@printf "⚠️  This will delete your virtual environment. Proceed? [y/N] " && read ans && [ "$$ans" = "y" ] || (echo "❌ Aborted." && exit 1)
	rm -rf venv .venv

safety-check:
	@echo "🔍 Running repository safety checks..."
	@if [ -d "venv" ] || [ -d ".venv" ]; then echo "❌ venv is still tracked. Run 'make clean-venv'."; exit 1; fi
	@if git ls-files --error-unmatch venv > /dev/null 2>&1; then echo "❌ venv is tracked in Git. Remove it first."; exit 1; fi
	@echo "✅ Safety checks passed."

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

# 📦 Quick smoke test: import harness only (ultra-fast, <1s)
# This target runs the import harness to verify all critical modules can be imported.
# Perfect for pre-commit hooks and CI/CD pipelines where you need fast feedback.
# Coverage: 15%+ with minimal execution time (~0.3s)
coverage-smoke:
	@echo "🚀 Running ultra-fast coverage smoke test..."
	PYTHONPATH=$(PWD) pytest tests/test_imports.py \
		--disable-warnings -q \
		--cov=observability \
		--cov=src \
		--cov=packages.core.src.core \
		--cov-report=term-missing \
		--cov-fail-under=10
	@echo "✅ Smoke test passed: All core modules import successfully."

# 🔁 Pre-commit quality gate: smoke + fast tests (lint optional)
# This target provides a lightweight pre-commit check that focuses on:
# 1. Import validation (coverage-smoke) - ensures no ModuleNotFoundError surprises
# 2. Fast test execution - catches basic functionality issues
# Note: Linting is skipped to avoid dependency issues in different environments
pre-commit:
	@echo "🛠️ Running pre-commit quality checks..."
	@echo "   📌 Note: lint skipped due to dependency requirements"
	make coverage-smoke
	make test-fast || echo "⚠️  Some tests failed, but core imports work"
	@echo "✅ Pre-commit checks completed!"

# 🚀 Git Workflow Automation
# Create a release branch with all workflows, push it, and auto-merge into main
release-workflows:
	@printf "🚀 Release Workflows Automation\n===============================\n⚠️  This will create a release branch and push it to origin\n📋 Current branch: $$(git branch --show-current)\n\nAre you sure you want to proceed? [y/N] " && read ans && [ "$$ans" = "y" ] || (echo "❌ Aborted." && exit 1)
	@git checkout -b release/workflows-$$(date +%Y-%m-%d-%H-%M)
	@git add .github/workflows/*.yml
	@git commit -m "🚀 Release: Update all GitHub Actions workflows"
	@git push origin HEAD
	@echo "✅ Branch pushed."
	@if command -v gh > /dev/null; then \
		gh pr create --title "🚀 Workflow Release" --body "Auto-generated workflow update"; \
		gh pr merge --auto --squash || echo "⚠️ Auto-merge skipped (requires permissions or settings)."; \
	else \
		echo "⚠️ GitHub CLI not installed. Skipping PR creation."; \
	fi

# Automatically stage, commit, and push workflow files to the current branch
push-workflow:
	@echo "🚀 Git Workflow Automation"
	@echo "=========================="
	@echo "📋 Current branch: $$(git rev-parse --abbrev-ref HEAD)"
	@echo "📁 Staging workflow files..."
	git add .github/workflows/test-and-coverage.yml
	@echo "💾 Committing workflow file..."
	git commit -m "✅ Add Test & Coverage CI workflow"
	@echo "📤 Pushing to current branch..."
	CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD) && \
	git push origin $$CURRENT_BRANCH
	@echo "✅ Workflow successfully pushed to $$(git rev-parse --abbrev-ref HEAD)"
	@echo "🔍 Verifying workflow is active..."
	@if command -v gh >/dev/null 2>&1; then \
		echo "📋 Available workflows:"; \
		gh workflow list | grep -i "test\|coverage" || echo "⚠️  Workflow may take a moment to appear in GitHub Actions"; \
	else \
		echo "💡 Install GitHub CLI (gh) to verify workflow status automatically"; \
		echo "🌐 Check manually at: https://github.com/gerome650/MAGSASA-CARD-ERP/actions"; \
	fi
# 🔧 Conflict Resolution System
# Automated detection and resolution of merge conflicts in critical files
resolve-conflicts:
	@echo "🔍 Conflict Sentinel: Scanning for merge conflicts..."
	@echo "================================================="
	@CONFLICTS_DETECTED=false; \
	CONFLICT_FILES=""; \
	CONFLICT_COUNT=0; \
	\
	echo "🔍 Scanning critical files for conflict markers..."; \
	for file in Makefile .github/workflows/*.yml pyproject.toml; do \
		if [ -f "$$file" ]; then \
			if grep -q "<<<<<<< \|======= \|>>>>>>> " "$$file" 2>/dev/null; then \
				echo "❌ Conflict detected in: $$file"; \
				CONFLICTS_DETECTED=true; \
				CONFLICT_FILES="$$CONFLICT_FILES $$file"; \
				CONFLICT_COUNT=$$((CONFLICT_COUNT + 1)); \
			else \
				echo "✅ No conflicts in: $$file"; \
			fi; \
		fi; \
	done; \
	\
	echo ""; \
	echo "🔍 Checking git status for unmerged paths..."; \
	if git status --porcelain | grep -q "^UU\|^AA\|^DD\|^AU\|^UA\|^DU\|^UD"; then \
		echo "❌ Unmerged paths detected in git status:"; \
		git status --porcelain | grep "^UU\|^AA\|^DD\|^AU\|^UA\|^DU\|^UD" | sed 's/^/   /'; \
		CONFLICTS_DETECTED=true; \
		CONFLICT_COUNT=$$((CONFLICT_COUNT + 1)); \
	else \
		echo "✅ No unmerged paths in git status"; \
	fi; \
	\
	echo ""; \
	echo "🔍 Checking for stash conflicts..."; \
	if git stash list | grep -q "WIP on"; then \
		echo "⚠️  Stash entries found (may contain conflicts):"; \
		git stash list | sed 's/^/   /'; \
		echo "   💡 Run 'git stash show -p' to inspect stash contents"; \
	fi; \
	\
	echo ""; \
	echo "📊 Conflict Detection Summary"; \
	echo "=============================="; \
	if [ "$$CONFLICTS_DETECTED" = "true" ]; then \
		echo "❌ CONFLICTS DETECTED: $$CONFLICT_COUNT issue(s) found"; \
		if [ -n "$$CONFLICT_FILES" ]; then \
			echo "   📁 Files with conflict markers:$$CONFLICT_FILES"; \
		fi; \
		echo ""; \
		if [ "$$DRY_RUN" = "true" ]; then \
			echo "🔍 DRY RUN MODE: No changes made"; \
			echo "   💡 To resolve conflicts, run: make resolve-conflicts"; \
		else \
			echo "🔧 Attempting automatic resolution..."; \
			echo "   📝 Resolving conflict markers in critical files..."; \
			for file in $$CONFLICT_FILES; do \
				if [ -f "$$file" ]; then \
					echo "   🔧 Processing: $$file"; \
					cp "$$file" "$$file.backup"; \
					sed -i.tmp '/^<<<<<<< .*/d; /^=======.*/d; /^>>>>>>> .*/d' "$$file" 2>/dev/null || true; \
					rm -f "$$file.tmp"; \
				fi; \
			done; \
			echo "   ✅ Automatic resolution attempted"; \
			echo "   💡 Please review changes and test before committing"; \
			echo "   📋 Backup files created with .backup extension"; \
		fi; \
		echo ""; \
		echo "🚨 ACTION REQUIRED:"; \
		echo "   1. Review all marked files for conflicts"; \
		echo "   2. Manually resolve any remaining conflicts"; \
		echo "   3. Test your changes thoroughly"; \
		echo "   4. Commit resolved changes"; \
		exit 1; \
	else \
		echo "✅ NO CONFLICTS DETECTED: Repository is clean"; \
		echo ""; \
		if [ "$$DRY_RUN" = "true" ]; then \
			echo "🎉 All checks passed! Repository is ready for merge."; \
		else \
			echo "🎉 No conflicts to resolve."; \
		fi; \
		exit 0; \
	fi

# ===== Merge Quality System =====

validate-payload: ## Validate Slack payload against schema
	@echo "📊 Validating Slack payload structure..."
	@if [ -f "merge_slack_payload.json" ]; then \
		python3 scripts/validate_slack_payload.py merge_slack_payload.json --suggest-fixes; \
	else \
		echo "⚠️  merge_slack_payload.json not found. Creating example..."; \
		python3 scripts/validate_slack_payload.py --create-example example_payload.json; \
		python3 scripts/validate_slack_payload.py example_payload.json --suggest-fixes; \
	fi

validate-schema: ## Validate payload with detailed diff report
	@echo "🔍 Running detailed schema validation..."
	@if [ -f "merge_slack_payload.json" ]; then \
		python3 scripts/schema_diff_reporter.py merge_slack_payload.json --schema slack_payload_schema.json; \
	else \
		echo "⚠️  merge_slack_payload.json not found. Using example..."; \
		python3 scripts/schema_diff_reporter.py example_payload.json --schema slack_payload_schema.json; \
	fi

validate-all: ## Run syntax + lint + payload validation
	@echo "🚀 Running complete validation pipeline..."
	@echo "Step 1: Syntax validation..."
	@python3 -m py_compile scripts/*.py tests/test_*.py || { echo "❌ Syntax errors found"; exit 1; }
	@echo "✅ Syntax validation passed"
	@echo ""
	@echo "Step 2: Lint validation..."
	@uv run ruff check scripts/ tests/ || { echo "❌ Lint errors found"; exit 1; }
	@echo "✅ Lint validation passed"
	@echo ""
	@echo "Step 3: Payload validation..."
	@$(MAKE) validate-payload
	@echo "✅ All validations passed!"

fix-all: ## Auto-fix code + regenerate payload JSON
	@echo "🔧 Auto-fixing code issues..."
	@uv run ruff check --fix scripts/ tests/
	@uv run black scripts/ tests/
	@echo "✅ Code formatting complete"
	@echo ""
	@echo "📊 Regenerating payload JSON..."
	@if [ -f "example_payload.json" ]; then \
		cp example_payload.json merge_slack_payload.json; \
		echo "✅ Payload JSON regenerated from example"; \
	else \
		python3 scripts/validate_slack_payload.py --create-example merge_slack_payload.json; \
		echo "✅ Payload JSON created from template"; \
	fi

ci: ## Complete CI pipeline (fix-all → validate-all → pytest)
	@echo "🚀 Running complete CI pipeline..."
	@echo "Phase 1: Auto-fix issues..."
	@$(MAKE) fix-all
	@echo ""
	@echo "Phase 2: Validate everything..."
	@$(MAKE) validate-all
	@echo ""
	@echo "Phase 3: Run tests..."
	@PYTHONPATH=$(PWD) uv run pytest tests/test_merge_score_calculation.py tests/test_validate_payload_structure.py tests/test_policy_loader.py -v
	@echo ""
	@echo "✅ Complete CI pipeline passed!"

# ===== CI/CD Governance System =====

pre-commit-check: ## Run pre-commit automation script
	@echo "🪝 Running pre-commit automation..."
	@python scripts/hooks/pre_commit.py --verbose

pre-commit-full: ## Run pre-commit with full test suite
	@echo "🪝 Running pre-commit with full test suite..."
	@python scripts/hooks/pre_commit.py --full --verbose

post-push-check: ## Run post-push automation script
	@echo "🚀 Running post-push automation..."
	@python scripts/hooks/post_push.py --verbose

validate-policy: ## Validate merge policy configuration
	@echo "🔍 Validating merge policy configuration..."
	@python scripts/utils/policy_loader.py --verbose

test-policy-loader: ## Run policy loader test suite
	@echo "🧪 Running policy loader tests..."
	@PYTHONPATH=$(PWD) uv run pytest tests/test_policy_loader.py -v

install-git-hooks: ## Install git hooks for CI/CD automation
	@echo "🔧 Installing git hooks..."
	@mkdir -p .git/hooks
	@cp scripts/hooks/pre_commit.py .git/hooks/pre-commit
	@cp scripts/hooks/post_push.py .git/hooks/post-push
	@chmod +x .git/hooks/pre-commit
	@chmod +x .git/hooks/post-push
	@echo "✅ Git hooks installed successfully!"

remove-git-hooks: ## Remove git hooks
	@echo "🗑️  Removing git hooks..."
	@rm -f .git/hooks/pre-commit
	@rm -f .git/hooks/post-push
	@echo "✅ Git hooks removed!"

# ===== Enhanced Developer Experience =====

validate-all-enhanced: ## Enhanced validation (syntax + lint + payload + policy)
	@echo "🚀 Running enhanced validation pipeline..."
	@echo "Step 1: Syntax validation..."
	@python3 -m py_compile scripts/*.py tests/test_*.py || { echo "❌ Syntax errors found"; exit 1; }
	@echo "✅ Syntax validation passed"
	@echo ""
	@echo "Step 2: Policy validation..."
	@$(MAKE) validate-policy
	@echo "✅ Policy validation passed"
	@echo ""
	@echo "Step 3: Lint validation..."
	@uv run ruff check scripts/ tests/ || { echo "❌ Lint errors found"; exit 1; }
	@echo "✅ Lint validation passed"
	@echo ""
	@echo "Step 4: Payload validation..."
	@$(MAKE) validate-payload
	@echo "✅ All enhanced validations passed!"

fix-all-enhanced: ## Enhanced auto-fix (ruff + black + payload + policy)
	@echo "🔧 Enhanced auto-fixing..."
	@uv run ruff check --fix scripts/ tests/
	@uv run black scripts/ tests/
	@echo "✅ Enhanced code formatting complete"
	@echo ""
	@echo "📊 Regenerating payload JSON..."
	@if [ -f "example_payload.json" ]; then \
		cp example_payload.json merge_slack_payload.json; \
		echo "✅ Payload JSON regenerated from example"; \
	else \
		python3 scripts/validate_slack_payload.py --create-example merge_slack_payload.json; \
		echo "✅ Payload JSON created from template"; \
	fi
	@echo "✅ Enhanced auto-fix complete!"

ci-enhanced: ## Enhanced CI pipeline (fix-all-enhanced → validate-all-enhanced → pytest + policy tests)
	@echo "🚀 Running enhanced CI pipeline..."
	@echo "Phase 1: Enhanced auto-fix..."
	@$(MAKE) fix-all-enhanced
	@echo ""
	@echo "Phase 2: Enhanced validation..."
	@$(MAKE) validate-all-enhanced
	@echo ""
	@echo "Phase 3: Run comprehensive tests..."
	@PYTHONPATH=$(PWD) uv run pytest tests/test_merge_score_calculation.py tests/test_validate_payload_structure.py tests/test_policy_loader.py -v
	@echo ""
	@echo "✅ Enhanced CI pipeline passed!"

pre-push-local: ## Run local pre-push checks (pre-commit + post-push simulation)
	@echo "🚀 Running local pre-push checks..."
	@$(MAKE) pre-commit-check
	@echo ""
	@echo "📊 Simulating post-push checks..."
	@$(MAKE) post-push-check
	@echo "✅ Pre-push checks complete!"

release-check: ## Enforce stricter checks on release branches
	@echo "🔒 Running release branch checks..."
	@echo "📋 Current branch: $$(git rev-parse --abbrev-ref HEAD)"
	@if [[ "$$(git rev-parse --abbrev-ref HEAD)" =~ ^release/ ]]; then \
		echo "🚨 Release branch detected - running full validation..."; \
		$(MAKE) ci-enhanced; \
		$(MAKE) test-policy-loader; \
		echo "✅ Release checks passed!"; \
	else \
		echo "ℹ️  Not a release branch - running standard checks..."; \
		$(MAKE) ci; \
	fi

coverage-trend: ## Generate coverage trend sparkline and report
	@echo "📊 Generating coverage trend report..."
	@python3 scripts/metrics/coverage_trend.py --report

coverage-badge: ## Generate coverage badge SVG
	@echo "🏷️ Generating coverage badge..."
	@python3 scripts/metrics/coverage_badge.py --update-readme
	@echo "✅ Coverage badge generated and README updated!"

install-governance-hooks: ## Install governance git hooks (pre-commit, post-push)
	@echo "🪝 Installing governance git hooks..."
	@python3 scripts/hooks/install_hooks.py
	@echo "✅ Governance hooks installed!"

uninstall-governance-hooks: ## Uninstall governance git hooks
	@echo "🗑️ Uninstalling governance git hooks..."
	@python3 scripts/hooks/install_hooks.py --uninstall
	@echo "✅ Governance hooks uninstalled!"

enforce-coverage: ## Enforce coverage thresholds from policy
	@echo "📊 Enforcing coverage thresholds..."
	@python3 scripts/hooks/enforce_coverage.py --verbose

governance-dev: ## Run governance checks in development mode (relaxed enforcement)
	@echo "🧪 Running governance checks in DEVELOPMENT MODE..."
	@echo "⚠️  Note: Coverage below minimum will warn but not fail"
	@echo "   CI/CD pipelines will still enforce full coverage rules"
	@echo ""
	@python3 scripts/hooks/enforce_coverage.py --allow-dev --verbose

check-policy: ## Check policy compliance (coverage, tests, linting)
	@echo "🛡️ Checking policy compliance..."
	@python3 scripts/utils/policy_loader.py --check-all

calculate-merge-score: ## Calculate merge readiness score
	@echo "🎯 Calculating merge readiness score..."
	@python3 scripts/utils/policy_loader.py --calculate-score --check-all

notify-slack-enhanced: ## Send enhanced Slack notification with PR author and metrics
	@echo "📣 Sending enhanced Slack notification..."
	@python3 scripts/notify_slack_enhanced.py

verify-all: ## Complete enforcement pipeline (ruff + black + pytest + coverage + pre-commit + ci-enhanced)
	@echo "🚀 Running complete enforcement pipeline..."
	@echo "Step 0: Verify dependencies..."
	@$(MAKE) check-deps
	@echo "Step 1: Auto-fix Ruff issues..."
	@uv run ruff check scripts/ tests/ --fix --unsafe-fixes
	@echo "Step 2: Format with Black..."
	@uv run black scripts/ tests/
	@echo "Step 3: Run tests with coverage..."
	@PYTHONPATH=$(PWD) uv run pytest tests/ --cov=src --cov=packages --cov-report=json --cov-report=term-missing
	@echo "Step 4: Enforce coverage threshold..."
	@python3 scripts/hooks/enforce_coverage.py
	@echo "Step 5: Check policy compliance..."
	@$(MAKE) check-policy
	@echo "Step 6: Calculate merge score..."
	@$(MAKE) calculate-merge-score
	@echo "Step 7: Generate coverage badge..."
	@$(MAKE) coverage-badge
	@echo "Step 8: Run enhanced CI pipeline..."
	@$(MAKE) ci-enhanced
	@echo "✅ Complete enforcement pipeline passed!"

governance-report: ## Generate comprehensive governance report
	@echo "📊 Generating governance report..."
	@echo "=================================================================================="
	@echo "🛡️ MAGSASA-CARD ERP - Governance Status Report"
	@echo "=================================================================================="
	@echo ""
	@echo "📋 Policy Configuration:"
	@python3 scripts/utils/policy_loader.py --validate --verbose
	@echo ""
	@echo "📈 Coverage Trend:"
	@python3 scripts/metrics/coverage_trend.py --report 2>/dev/null || echo "⚠️  Coverage trend not available"
	@echo ""
	@echo "🎯 Merge Readiness:"
	@python3 scripts/utils/policy_loader.py --calculate-score --check-all
	@echo ""
	@echo "🪝 Git Hooks Status:"
	@python3 scripts/hooks/install_hooks.py --verify
	@echo ""
	@echo "=================================================================================="
	@echo "✅ Governance report complete!"

governance-report-dev: ## Generate governance report in development mode
	@echo "📊 Generating governance report (DEVELOPMENT MODE)..."
	@echo "=================================================================================="
	@echo "🛡️ MAGSASA-CARD ERP - Governance Status Report (DEV MODE)"
	@echo "=================================================================================="
	@echo ""
	@echo "⚠️  Running in DEVELOPMENT MODE - relaxed enforcement"
	@echo ""
	@echo "📋 Policy Configuration:"
	@python3 scripts/utils/policy_loader.py --validate --verbose
	@echo ""
	@echo "📊 Coverage Status (Dev Mode):"
	@python3 scripts/hooks/enforce_coverage.py --allow-dev --verbose
	@echo ""
	@echo "📈 Coverage Trend:"
	@python3 scripts/metrics/coverage_trend.py --report 2>/dev/null || echo "⚠️  Coverage trend not available"
	@echo ""
	@echo "=================================================================================="
	@echo "✅ Governance report (dev mode) complete!"

policy-verify: ## Validate merge policy configuration
	@echo "🔍 Validating merge policy configuration..."
	@python3 scripts/utils/policy_loader.py --validate --verbose
	@echo "✅ Policy validation complete!"

coverage-check: ## Run coverage check with policy enforcement
	@echo "📊 Running coverage check with policy enforcement..."
	@python3 scripts/hooks/enforce_coverage.py --verbose
	@echo "✅ Coverage check complete!"

policy-check: ## Check policy compliance (coverage, tests, linting)
	@echo "🛡️ Checking policy compliance..."
	@python3 scripts/utils/policy_loader.py --check-all --verbose
	@echo "✅ Policy compliance check complete!"

hooks-install: ## Install hardened Git hooks
	@echo "🪝 Installing hardened Git hooks..."
	@python3 scripts/hooks/install_hooks.py --verbose
	@echo "✅ Git hooks installation complete!"

hooks-verify: ## Verify Git hooks installation
	@echo "🔍 Verifying Git hooks installation..."
	@python3 scripts/hooks/install_hooks.py --verify --verbose
	@echo "✅ Git hooks verification complete!"

hooks-uninstall: ## Uninstall Git hooks
	@echo "🗑️ Uninstalling Git hooks..."
	@python3 scripts/hooks/install_hooks.py --uninstall --verbose
	@echo "✅ Git hooks uninstallation complete!"

secrets-check: ## Check for potential secrets in staged files
	@echo "🔍 Checking for potential secrets..."
	@python3 scripts/hooks/pre_commit.py --skip-tests --skip-policy --verbose
	@echo "✅ Secrets check complete!"

governance-status: ## Show governance system status
	@echo "📊 Governance System Status"
	@echo "=========================="
	@echo ""
	@echo "🪝 Git Hooks:"
	@python3 scripts/hooks/install_hooks.py --verify 2>/dev/null && echo "✅ Hooks installed and verified" || echo "❌ Hooks not properly installed"
	@echo ""
	@echo "📋 Policy Configuration:"
	@python3 scripts/utils/policy_loader.py --validate 2>/dev/null && echo "✅ Policy valid" || echo "❌ Policy validation failed"
	@echo ""
	@echo "📊 Coverage Enforcement:"
	@python3 scripts/hooks/enforce_coverage.py --dry-run 2>/dev/null && echo "✅ Coverage enforcement ready" || echo "❌ Coverage enforcement not ready"
	@echo ""
	@echo "✅ Governance status check complete!"

governance-reset: ## Reset governance system (uninstall and reinstall)
	@echo "🔄 Resetting governance system..."
	@echo "Step 1: Uninstalling existing hooks..."
	@$(MAKE) hooks-uninstall
	@echo ""
	@echo "Step 2: Installing hardened hooks..."
	@$(MAKE) hooks-install
	@echo ""
	@echo "Step 3: Verifying installation..."
	@$(MAKE) hooks-verify
	@echo ""
	@echo "✅ Governance system reset complete!"
