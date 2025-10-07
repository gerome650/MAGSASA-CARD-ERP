# 🛡️ Governance & PR Author Integration Guide

## Overview

This repository implements a **comprehensive governance and CI/CD enforcement system** that automatically:

- ✅ Enforces code quality standards (linting, formatting, tests)
- 📊 Tracks and enforces coverage thresholds
- 🎯 Calculates merge readiness scores
- 📣 Sends Slack notifications with PR author mentions
- 🏷️ Generates coverage badges and trends
- 🪝 Provides git hooks for local quality gates

---

## 🚀 Quick Start

### 1. Install Git Hooks

```bash
make install-governance-hooks
```

This installs:
- **pre-commit hook**: Runs linting, formatting, and tests before commits
- **post-push hook**: Runs coverage checks and sends notifications

### 2. Run Quality Checks

```bash
# Check policy compliance
make check-policy

# Enforce coverage thresholds
make enforce-coverage

# Calculate merge readiness score
make calculate-merge-score

# Run complete verification pipeline
make verify-all
```

### 3. Configure Slack Notifications

Set the `SLACK_WEBHOOK_URL` environment variable:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Add to your `.env` file or CI/CD secrets.

---

## 📋 Policy Configuration

The governance system is configured via `merge_policy.yml` at the repository root.

### Key Configuration Areas

#### Coverage Thresholds
```yaml
coverage:
  enabled: true
  minimum: 85    # Hard fail below this
  warning: 90    # Warning if below this
  target: 95     # Aspirational target
```

#### Test Requirements
```yaml
testing:
  enabled: true
  minimum_pass_rate: 100  # All tests must pass
```

#### Linting Standards
```yaml
linting:
  enabled: true
  tools:
    ruff:
      max_violations: 0  # Zero tolerance
```

#### Merge Score Weights
```yaml
merge_score:
  enabled: true
  passing_threshold: 80
  weights:
    coverage: 30
    tests_passing: 30
    linting: 20
    reviews: 15
    documentation: 5
```

### Editing the Policy

1. Open `merge_policy.yml`
2. Modify thresholds and settings
3. Validate changes:
   ```bash
   python scripts/utils/policy_loader.py
   ```

---

## 🪝 Git Hooks

### Pre-Commit Hook

Runs before every commit:

1. **Code Formatting** (Black) - Auto-formats code
2. **Linting** (Ruff) - Checks for code issues
3. **Type Checking** (Mypy) - Optional type validation
4. **Unit Tests** - Fast unit test execution

**Bypass (not recommended):**
```bash
git commit --no-verify
```

### Post-Push Hook

Runs after successful push:

1. **Coverage Enforcement** - Checks coverage thresholds
2. **Slack Notification** - Sends push notification (if configured)

**Install/Uninstall:**
```bash
make install-governance-hooks  # Install
make uninstall-governance-hooks  # Uninstall
```

---

## 📊 Coverage Tracking

### Coverage Enforcement

Automatically enforces coverage thresholds from `merge_policy.yml`:

```bash
# Manual enforcement
make enforce-coverage

# With verbose output
python scripts/hooks/enforce_coverage.py --verbose
```

**Exit Codes:**
- `0`: Coverage meets minimum threshold
- `1`: Coverage below minimum threshold

### Coverage Trends

Track coverage over time with sparklines:

```bash
# Generate trend report
make coverage-trend

# Add manual data point
python scripts/metrics/coverage_trend.py --add 87.5

# Show sparkline only
python scripts/metrics/coverage_trend.py --sparkline
```

**Output Example:**
```
📈 Coverage Trend Report
=============================================================
Current Coverage: 87.50%
Sparkline:        ▁▃▄▆█
Trend Direction:  ↑
Rolling Average:  86.20% (last 3 runs)
Change from Last: +2.3% ↑
```

### Coverage Badges

Generate SVG badges for your README:

```bash
# Generate and update README
make coverage-badge

# Manual generation
python scripts/metrics/coverage_badge.py --coverage 87.5
```

---

## 🛡️ Policy Enforcement

### Policy Loader

The policy loader validates and enforces governance rules:

```bash
# Load and validate policy
python scripts/utils/policy_loader.py

# Check specific metrics
python scripts/utils/policy_loader.py --check-coverage 87.5
python scripts/utils/policy_loader.py --check-tests --tests-passed 50 --tests-total 50
python scripts/utils/policy_loader.py --check-lint --lint-violations 5

# Run all checks
python scripts/utils/policy_loader.py --check-all

# Calculate merge score
python scripts/utils/policy_loader.py --calculate-score
```

### Merge Readiness Score

The system calculates a merge readiness score (0-100) based on:

| Component | Weight | Calculation |
|-----------|--------|-------------|
| Coverage | 30% | Linear: (actual/target) × 100 |
| Tests | 30% | Percentage: (passed/total) × 100 |
| Linting | 20% | Penalty: 100 - (violations × 5) |
| Reviews | 15% | Score per review: 50 per review |
| Documentation | 5% | Has description: 50 points |

**Passing Threshold:** 80/100

**Example:**
```bash
make calculate-merge-score
```

Output:
```
🎯 Merge Score: 85.0/100 (✅ PASS, threshold: 80)
   Components:
     - coverage: 92.1
     - tests_passing: 100.0
     - linting: 95.0
     - reviews: 50.0
     - documentation: 50.0
```

---

## 📣 Slack Notifications

### Enhanced Notifications

The system sends rich Slack notifications with:

- 👤 PR author mentions (`@username`)
- 📊 Coverage with sparkline trends
- 🎯 Merge readiness scores
- ✅ Test results
- 🧹 Linting status
- 📋 Required actions

### Environment Variables

Required for notifications:

```bash
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
PR_AUTHOR="github-username"
PR_NUMBER="123"
PR_TITLE="Add new feature"
COVERAGE="87.5"
MERGE_SCORE="85"
TESTS_PASSED="50"
TESTS_TOTAL="50"
LINT_VIOLATIONS="0"
```

### Sending Notifications

```bash
# Enhanced notification with all metrics
make notify-slack-enhanced

# Direct script call
python scripts/notify_slack_enhanced.py
```

### Notification Format

```
🛡️ Merge Gate: ✅ PASSED

PR #123: Add new feature
Author: @john-doe

┌─────────────┬────────────┐
│ Coverage    │ 87.5% ▁▃▄▆█│
│ Tests       │ 50/50 pass │
│ Merge Score │ 85/100 ✅  │
│ Linting     │ 0 violations│
└─────────────┴────────────┘

✅ All quality gates passed! This PR is ready to merge.
```

---

## 🔄 CI/CD Workflow

### Merge Gate Workflow

The `.github/workflows/merge-gate.yml` workflow runs on every PR:

**Jobs:**

1. **lint-and-format** - Code quality checks
2. **tests-and-coverage** - Test execution and coverage
3. **policy-check** - Policy compliance and scoring
4. **slack-notify** - Notification with PR author mention
5. **final-gate** - Final merge decision

**Key Features:**

- ✅ Automatic PR author detection
- 📊 Coverage trend visualization
- 🎯 Merge score calculation
- 📝 PR comments with results
- 📣 Slack notifications
- 🚫 Blocks merge if quality gates fail

### CI Environment Variables

Set in GitHub Actions secrets or repository settings:

```yaml
env:
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  PR_AUTHOR: ${{ github.event.pull_request.user.login }}
  PR_NUMBER: ${{ github.event.pull_request.number }}
  COVERAGE: ${{ needs.tests-and-coverage.outputs.coverage }}
  MERGE_SCORE: ${{ needs.policy-check.outputs.merge_score }}
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run policy loader tests
make test-policy-loader
pytest tests/test_policy_loader.py -v

# Run with coverage
pytest tests/ --cov --cov-report=html
```

### Test Coverage

The test suite provides **comprehensive coverage** of:

- ✅ Policy loading and validation
- ✅ Coverage enforcement (pass/fail/warn)
- ✅ Test pass rate checking
- ✅ Linting enforcement
- ✅ Merge score calculation
- ✅ Branch protection
- ✅ Violation reporting
- ✅ Integration scenarios

**Target Coverage:** 100% for governance modules

---

## 📖 Command Reference

### Makefile Commands

#### Installation & Setup
```bash
make install-governance-hooks    # Install git hooks
make uninstall-governance-hooks  # Remove git hooks
```

#### Quality Checks
```bash
make check-policy           # Check policy compliance
make enforce-coverage       # Enforce coverage thresholds
make calculate-merge-score  # Calculate merge score
```

#### Coverage & Metrics
```bash
make coverage-trend    # Generate trend report
make coverage-badge    # Generate badge and update README
```

#### Notifications
```bash
make notify-slack-enhanced  # Send enhanced Slack notification
```

#### Complete Pipeline
```bash
make verify-all         # Run complete enforcement pipeline
make governance-report  # Generate comprehensive report
```

### Python Scripts

#### Policy Loader
```bash
python scripts/utils/policy_loader.py [OPTIONS]

Options:
  --policy PATH              Path to merge_policy.yml
  --check-coverage FLOAT     Check coverage threshold
  --check-tests             Check test pass rate
  --check-lint              Check linting violations
  --check-all               Run all checks
  --calculate-score         Calculate merge score
  --json                    Output as JSON
```

#### Coverage Enforcement
```bash
python scripts/hooks/enforce_coverage.py [OPTIONS]

Options:
  --coverage-file PATH   Path to coverage file
  --format {json,xml}    Coverage file format
  --policy PATH          Path to merge_policy.yml
  --verbose              Verbose output
```

#### Coverage Trend
```bash
python scripts/metrics/coverage_trend.py [OPTIONS]

Options:
  --add FLOAT           Add coverage data point
  --commit SHA          Git commit SHA
  --sparkline           Output sparkline only
  --report              Generate full report
  --history-file PATH   Path to history file
  --history-size INT    Max history size
```

#### Coverage Badge
```bash
python scripts/metrics/coverage_badge.py [OPTIONS]

Options:
  --coverage FLOAT      Coverage percentage
  --output PATH         Output path for badge
  --update-readme       Update README.md with badge
```

#### Slack Notifier
```bash
python scripts/notify_slack_enhanced.py

Environment Variables Required:
  SLACK_WEBHOOK_URL
  PR_AUTHOR, PR_NUMBER, PR_TITLE
  COVERAGE, MERGE_SCORE
  TESTS_PASSED, TESTS_TOTAL
  LINT_VIOLATIONS
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Coverage File Not Found

**Error:**
```
❌ No coverage data found
```

**Solution:**
```bash
# Run tests with coverage first
pytest --cov --cov-report=json --cov-report=xml
```

#### 2. Policy File Not Found

**Error:**
```
FileNotFoundError: Policy file not found: merge_policy.yml
```

**Solution:**
```bash
# Ensure merge_policy.yml exists in repo root
ls -la merge_policy.yml

# Or specify path
python scripts/utils/policy_loader.py --policy /path/to/policy.yml
```

#### 3. Git Hooks Not Running

**Error:**
Hooks don't execute on commit/push

**Solution:**
```bash
# Reinstall hooks
make uninstall-governance-hooks
make install-governance-hooks

# Verify installation
ls -la .git/hooks/pre-commit .git/hooks/post-push

# Check permissions
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-push
```

#### 4. Slack Notifications Failing

**Error:**
```
❌ Failed to send Slack notification
```

**Solution:**
```bash
# Verify webhook URL is set
echo $SLACK_WEBHOOK_URL

# Test webhook manually
curl -X POST $SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

# Check for special characters in environment variables
# Ensure PR_TITLE doesn't contain unescaped quotes
```

#### 5. Coverage Below Threshold

**Error:**
```
❌ FAIL: Coverage 82.5% is below minimum threshold 85%
```

**Solution:**
```bash
# Add tests to increase coverage
# Check coverage report for untested files
pytest --cov --cov-report=html
open htmlcov/index.html

# Temporarily lower threshold (not recommended)
# Edit merge_policy.yml:
coverage:
  minimum: 80  # Lower from 85
```

### Debug Mode

Enable verbose output for debugging:

```bash
# Policy loader
python scripts/utils/policy_loader.py --check-all --verbose

# Coverage enforcement
python scripts/hooks/enforce_coverage.py --verbose

# Slack notifier
DEBUG=true python scripts/notify_slack_enhanced.py
```

---

## 🎯 Best Practices

### For Developers

1. **Install hooks early**: Run `make install-governance-hooks` after cloning
2. **Run checks locally**: Use `make verify-all` before pushing
3. **Monitor trends**: Check `make coverage-trend` regularly
4. **Fix issues promptly**: Don't bypass hooks unless absolutely necessary
5. **Keep policy updated**: Review `merge_policy.yml` quarterly

### For Teams

1. **Enforce standards**: Set `fail_on_violation: true` in policy
2. **Review thresholds**: Adjust coverage/linting thresholds based on project maturity
3. **Use Slack**: Configure notifications for team visibility
4. **Track metrics**: Generate `make governance-report` weekly
5. **Document exceptions**: Create wiki page for bypass procedures

### For CI/CD

1. **Required checks**: Make all workflow jobs required for merge
2. **Secrets management**: Store `SLACK_WEBHOOK_URL` in repository secrets
3. **Caching**: Cache Python dependencies in workflows
4. **Parallel execution**: Run independent jobs in parallel
5. **Notification hygiene**: Limit notifications to important events only

---

## 📚 Additional Resources

### Documentation

- [Governance Policy Reference](merge_policy.yml) - Full policy configuration
- [CI/CD Workflow](.github/workflows/merge-gate.yml) - Merge gate implementation
- [Test Suite](tests/test_policy_loader.py) - Policy loader tests

### Scripts

- **Policy Loader**: `scripts/utils/policy_loader.py`
- **Coverage Enforcement**: `scripts/hooks/enforce_coverage.py`
- **Coverage Trend**: `scripts/metrics/coverage_trend.py`
- **Coverage Badge**: `scripts/metrics/coverage_badge.py`
- **Slack Notifier**: `scripts/notify_slack_enhanced.py`
- **Git Hooks**: `scripts/hooks/{pre_commit,post_push,install_hooks}.py`

### Git Hooks

- **Pre-Commit**: `.git/hooks/pre-commit` (auto-generated)
- **Post-Push**: `.git/hooks/post-push` (auto-generated)

---

## 🎉 Success Criteria

Your governance system is working when:

- ✅ Pre-commit hooks run automatically on `git commit`
- ✅ Coverage enforcement blocks low-coverage PRs
- ✅ Merge score appears in PR comments
- ✅ Slack notifications mention PR authors
- ✅ Coverage badge updates automatically
- ✅ Policy violations fail CI checks
- ✅ All tests pass with >85% coverage

---

## 🆘 Support

### Getting Help

1. **Check this guide** - Most questions are answered here
2. **Run diagnostics**: `make governance-report`
3. **Check logs**: Review CI workflow logs in GitHub Actions
4. **Test locally**: Run `make verify-all` to reproduce issues

### Reporting Issues

When reporting issues, include:

- Error message and stack trace
- Output of `python scripts/utils/policy_loader.py`
- Contents of `merge_policy.yml`
- CI workflow logs (if applicable)
- Environment details (OS, Python version)

---

## 📝 Change Log

### Version 1.0.0 (Current)

**Features:**
- ✅ Comprehensive policy enforcement system
- ✅ Coverage tracking with trends and badges
- ✅ Merge readiness scoring
- ✅ Enhanced Slack notifications with PR author mentions
- ✅ Git hooks for local quality gates
- ✅ Full CI/CD workflow integration
- ✅ Extensive test coverage (100% for policy modules)

**Components:**
- Policy loader and enforcer
- Coverage enforcement script
- Git hooks (pre-commit, post-push)
- Coverage metrics (trends, badges)
- Enhanced Slack notifier
- CI/CD merge gate workflow
- Comprehensive test suite
- Makefile integration

---

## 🚀 Future Enhancements

Planned features for future versions:

- 🔄 Auto-remediation (auto-fix code issues)
- 🔒 Security scanning integration (Bandit, Safety)
- 📦 Dependency management (version checking, updates)
- 📊 Advanced metrics dashboard
- 🤖 AI-powered code review suggestions
- 🌍 Multi-repository governance
- 📈 Historical trend analysis
- 🎨 Custom badge designs

---

**Need more help?** Check out the [main README](README.md) or open an issue!

---

*Last Updated: October 6, 2025*
*Version: 1.0.0*
*Maintained by: Platform Engineering Team*
