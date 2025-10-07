# 🛡️ CI/CD Governance & Automation System

A complete CI/CD governance layer for the MAGSASA-CARD-ERP Python monorepo that enforces quality, security, and merge-readiness automatically before code reaches `main` or `release/*` branches.

## 🎯 System Overview

This system provides:
- **Pre-commit automation** with selective testing and auto-fixing
- **Post-push hooks** with rich Slack notifications
- **Merge gates** that block low-quality PRs
- **Policy enforcement** through centralized configuration
- **Trend analysis** and team metrics
- **Developer experience** enhancements

## 📋 Components

### 1. 🪝 Pre-Commit Automation (`scripts/hooks/pre_commit.py`)

Runs comprehensive pre-commit checks:
- **Black formatting** with auto-fix and re-staging
- **Ruff linting** with auto-fix
- **Selective pytest** execution (only tests related to changed files)
- **Full test suite** for `main`/`release/*` branches or with `--full` flag
- **Coverage validation** against policy thresholds
- **Slack notifications** with detailed summary

```bash
# Run pre-commit checks
python scripts/hooks/pre_commit.py

# Run with full test suite
python scripts/hooks/pre_commit.py --full

# Skip Slack notifications
python scripts/hooks/pre_commit.py --no-slack
```

### 2. 🚀 Post-Push Hook (`scripts/hooks/post_push.py`)

Provides comprehensive CI reporting after git push:
- **Lint metrics** (Ruff/Black status)
- **Test coverage** with trend analysis
- **PR diff analysis** (files, lines added/removed)
- **Merge readiness scoring** based on policy weights
- **Rich Slack reports** with PR links and metadata
- **GitHub API integration** for PR information

```bash
# Run post-push checks
python scripts/hooks/post_push.py

# Specify PR number manually
python scripts/hooks/post_push.py --pr-number 123
```

### 3. 🛡️ Merge Gate GitHub Action (`.github/workflows/merge-gate.yml`)

Enforces merge-blocking rules on every PR to protected branches:
- **Code quality checks** (Black, Ruff, MyPy)
- **Security scans** (Bandit, Safety)
- **Comprehensive testing** with coverage enforcement
- **Merge readiness scoring** with weighted components
- **Automatic blocking** for low-quality PRs
- **Slack notifications** with merge status

### 4. 🧪 CI Check Workflow (`.github/workflows/ci-check.yml`)

Runs on every push and PR with enhanced features:
- **Multi-component scoring** (formatting, linting, tests, security, coverage)
- **Trend analysis** with rolling averages
- **Early warning system** for declining quality
- **Team performance metrics**
- **Comprehensive reporting** with Slack integration

### 5. 📜 Central Policy Config (`merge_policy.yml`)

Defines all CI enforcement rules in one place:

```yaml
coverage:
  min_percent: 85
  fail_threshold: 80
  warning_threshold: 82

merge_scoring:
  weights:
    coverage: 0.3
    tests: 0.25
    linting: 0.2
    security: 0.15
    reviewers: 0.1
  min_score: 90
  goal_score: 95
  warning_score: 85

slack:
  channel: "#dev-ci-checks"
  webhook_secret: SLACK_WEBHOOK_URL
```

### 6. 🧠 Policy Loader Utility (`scripts/utils/policy_loader.py`)

Centralized policy loading with schema validation:
- **JSON schema validation** for policy structure
- **Business rule validation** (thresholds, weight sums)
- **Caching** for performance
- **Error handling** with detailed messages
- **CLI interface** for validation

```python
from scripts.utils.policy_loader import get_policy, get_coverage_threshold

policy = get_policy()
coverage_threshold = get_coverage_threshold()

if current_coverage < coverage_threshold["min_percent"]:
    raise ValueError("Coverage below threshold")
```

### 7. 📊 Merge Dashboard CLI (`scripts/metrics/merge_dashboard.py`)

Visualizes merge readiness scores and trends:
- **GitHub API integration** for PR data
- **Team performance metrics**
- **Trend analysis** with weekly breakdowns
- **Multiple output formats** (HTML, JSON, terminal)
- **Historical analysis** with configurable time ranges

```bash
# Generate HTML dashboard
python scripts/metrics/merge_dashboard.py --output html --days 30

# JSON report for automation
python scripts/metrics/merge_dashboard.py --output json --days 7

# Terminal output with trends
python scripts/metrics/merge_dashboard.py --trends --team-metrics
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required Python packages
pip install pytest pytest-cov black ruff mypy bandit safety jsonschema pyyaml requests

# Or use the project's dependency manager
uv sync --dev
```

### 2. Configure Environment Variables

```bash
# Required for Slack notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Required for GitHub API access
export GITHUB_TOKEN="ghp_your_github_token_here"
```

### 3. Install Git Hooks

```bash
# Install pre-commit and post-push hooks
make install-git-hooks

# Or manually
cp scripts/hooks/pre_commit.py .git/hooks/pre-commit
cp scripts/hooks/post_push.py .git/hooks/post-push
chmod +x .git/hooks/pre-commit .git/hooks/post-push
```

### 4. Validate Configuration

```bash
# Validate policy configuration
make validate-policy

# Run policy loader tests
make test-policy-loader

# Test pre-commit automation
make pre-commit-check
```

## 🛠️ Developer Experience

### Enhanced Makefile Commands

```bash
# CI/CD Governance System
make pre-commit-check          # Run pre-commit automation
make pre-commit-full          # Run with full test suite
make post-push-check          # Run post-push automation
make validate-policy          # Validate merge policy
make test-policy-loader       # Run policy loader tests
make install-git-hooks        # Install git hooks
make remove-git-hooks         # Remove git hooks

# Enhanced Developer Experience
make validate-all-enhanced    # Enhanced validation pipeline
make fix-all-enhanced         # Enhanced auto-fix
make ci-enhanced              # Enhanced CI pipeline
make pre-push-local           # Local pre-push checks
make release-check            # Stricter release branch checks
```

### Pre-Commit Workflow

1. **Make changes** to your code
2. **Stage files** with `git add`
3. **Commit** - pre-commit hook runs automatically:
   - Auto-fixes formatting and linting issues
   - Runs selective tests based on changed files
   - Validates coverage thresholds
   - Sends Slack notification
4. **Push** - post-push hook runs automatically:
   - Analyzes PR diff and impact
   - Calculates merge readiness score
   - Sends rich Slack report with PR links

### Post-Push Workflow

1. **Push changes** to remote branch
2. **Post-push hook** runs automatically:
   - Gathers PR metadata from GitHub API
   - Calculates comprehensive metrics
   - Determines merge readiness status
   - Sends Slack notification with PR links
3. **Create PR** if not already created
4. **Merge gate** runs on PR:
   - Enforces quality standards
   - Blocks low-quality PRs
   - Updates PR with detailed status

## 📱 Slack Integration

### Pre-Commit Notifications

```
📦 Pre-Commit Check — feature/add-merge-gate

✅ Tests: 154 passed (100%)
🧪 Coverage: 92.4%
🧹 Lint: 0 warnings
⏱️ Duration: 3m 12s

📍 Next: push to trigger full CI pipeline
```

### Post-Push Notifications

```
🚀 PR #42 — Ready for Review

📈 Coverage: 91.7% (🔴 -1.3%)
📊 Lint: 0 issues
🧪 Tests: 188 passed ✅
📊 Diff: +420/-86 (12 files)
👥 Reviewers: 2/2 ✅
🎯 Merge Readiness: 94% 🟢

🔗 View PR: https://github.com/org/repo/pull/42
```

### Merge Gate Notifications

```
🛡️ Merge Gate — PR #42
📊 Score: 88% 🟠 (🎯 Target: 90%)
📉 Rolling Avg: 86.7% 🔴
⚠️ 2/3 strikes — next PR below target will block merges
```

## 🎯 Merge Readiness Scoring

The system calculates merge readiness scores using weighted components:

- **Coverage (30%)**: Test coverage percentage
- **Tests (25%)**: Test execution results
- **Linting (20%)**: Code quality checks
- **Security (15%)**: Security scan results
- **Reviewers (10%)**: Review requirements met

### Score Thresholds

- **🟢 Ready (≥90%)**: Ready to merge
- **🟠 Warning (80-89%)**: Merge with caution
- **🔴 Blocked (<80%)**: Merge blocked

## 🔧 Configuration

### Policy Configuration (`merge_policy.yml`)

All CI enforcement rules are centralized in this file:

```yaml
# Coverage requirements
coverage:
  min_percent: 85          # Minimum coverage for merge
  fail_threshold: 80       # Coverage threshold for failure
  warning_threshold: 82    # Coverage threshold for warnings

# Test requirements
tests:
  max_failures: 0          # Maximum allowed test failures
  max_skipped: 5           # Maximum allowed skipped tests
  timeout_seconds: 300     # Test timeout in seconds

# Merge scoring weights
merge_scoring:
  weights:
    coverage: 0.3          # 30% weight for coverage
    tests: 0.25            # 25% weight for tests
    linting: 0.2           # 20% weight for linting
    security: 0.15         # 15% weight for security
    reviewers: 0.1         # 10% weight for reviewers
  min_score: 90            # Minimum score for merge
  goal_score: 95           # Target score for excellence
  warning_score: 85        # Warning threshold
```

### Environment Variables

```bash
# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# GitHub Integration
GITHUB_TOKEN=ghp_your_github_token_here

# Optional: Custom policy file
MERGE_POLICY_FILE=path/to/custom_policy.yml
```

## 🧪 Testing

### Run Policy Loader Tests

```bash
# Run comprehensive test suite
make test-policy-loader

# Or directly with pytest
pytest tests/test_policy_loader.py -v
```

### Test Individual Components

```bash
# Test pre-commit automation
python scripts/hooks/pre_commit.py --verbose

# Test post-push automation
python scripts/hooks/post_push.py --verbose

# Test policy validation
python scripts/utils/policy_loader.py --verbose
```

## 📊 Dashboard and Analytics

### Generate HTML Dashboard

```bash
# Generate interactive HTML dashboard
python scripts/metrics/merge_dashboard.py --output html --days 30

# Open in browser
open merge_dashboard_20240101_120000.html
```

### Team Performance Metrics

```bash
# Show team metrics in terminal
python scripts/metrics/merge_dashboard.py --team-metrics --trends

# Export JSON for analysis
python scripts/metrics/merge_dashboard.py --output json --days 7 > metrics.json
```

## 🚨 Troubleshooting

### Common Issues

1. **Slack notifications not working**
   ```bash
   # Check webhook URL
   echo $SLACK_WEBHOOK_URL
   
   # Test webhook manually
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     $SLACK_WEBHOOK_URL
   ```

2. **GitHub API rate limits**
   ```bash
   # Check token permissions
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/user
   ```

3. **Policy validation failures**
   ```bash
   # Validate policy file
   python scripts/utils/policy_loader.py --verbose
   
   # Check schema compliance
   make validate-policy
   ```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with debug output
python scripts/hooks/pre_commit.py --verbose
```

## 🔄 Integration with Existing CI

This system integrates seamlessly with existing CI/CD pipelines:

1. **GitHub Actions**: Uses existing workflows as base
2. **Makefile**: Extends existing commands
3. **Dependencies**: Uses existing Python packages
4. **Configuration**: Extends existing patterns

### Migration Steps

1. **Install components** without disrupting existing CI
2. **Configure environment variables** for Slack/GitHub
3. **Test with feature branches** before enabling on main
4. **Gradually enable** on protected branches
5. **Monitor and adjust** thresholds based on team performance

## 📈 Benefits

### For Developers
- **Faster feedback** with pre-commit automation
- **Clear quality standards** with policy enforcement
- **Reduced context switching** with Slack notifications
- **Automated fixes** for common issues

### For Teams
- **Consistent quality** across all PRs
- **Visibility** into team performance
- **Trend analysis** for continuous improvement
- **Automated governance** without manual oversight

### For Projects
- **Higher code quality** with automated enforcement
- **Reduced technical debt** through coverage requirements
- **Better security** with automated scans
- **Faster delivery** with streamlined workflows

## 🤝 Contributing

### Adding New Policies

1. **Update schema** in `policy_loader.py`
2. **Add validation** logic
3. **Update tests** in `test_policy_loader.py`
4. **Document changes** in this README

### Extending Automation

1. **Create new scripts** in `scripts/` directory
2. **Follow patterns** from existing components
3. **Add Makefile targets** for easy access
4. **Include tests** and documentation

### Reporting Issues

1. **Check troubleshooting** section above
2. **Enable debug mode** for detailed logs
3. **Provide policy file** if validation related
4. **Include error messages** and context

## 📚 Additional Resources

- [Policy Configuration Reference](merge_policy.yml)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Slack API Documentation](https://api.slack.com/)
- [Python Testing Best Practices](https://docs.python.org/3/library/unittest.html)

---

**Built with ❤️ for the MAGSASA-CARD-ERP team**
