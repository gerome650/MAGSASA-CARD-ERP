# 🚀 CI/CD Governance System - Quick Start

## Essential Commands

### Daily Development
```bash
# Before committing
make pre-commit-check          # Run all pre-commit checks

# Before pushing
make verify-all                # Complete verification pipeline

# Check coverage trend
make coverage-trend            # See coverage sparkline

# Auto-fix issues
make fix-all-enhanced          # Auto-fix lint and format
```

### Policy Management
```bash
# Validate policy
make validate-policy           # Check merge_policy.yml

# Test policy loader
make test-policy-loader        # Run policy tests
```

### CI/CD Operations
```bash
# Enhanced CI pipeline
make ci-enhanced               # Full CI with auto-fix

# Release checks (stricter)
make release-check             # For release branches

# Local pre-push simulation
make pre-push-local            # Simulate pre-push hooks
```

---

## Key Files

| File | Purpose |
|------|---------|
| `merge_policy.yml` | Central governance configuration |
| `scripts/utils/policy_loader.py` | Policy parsing and validation |
| `scripts/hooks/enforce_coverage.py` | Coverage enforcement |
| `scripts/hooks/pre_commit.py` | Pre-commit automation |
| `scripts/hooks/post_push.py` | Post-push automation |
| `scripts/metrics/coverage_trend.py` | Coverage trend analysis |
| `.github/workflows/merge-gate.yml` | GitHub merge gate |
| `tests/test_policy_loader.py` | Policy loader tests |

---

## Coverage Thresholds

| Metric | Value |
|--------|-------|
| Minimum | 85% |
| Warning | 82% |
| Fail | 80% |

---

## Merge Requirements

| Check | Requirement |
|-------|-------------|
| Coverage | ≥ 85% |
| Tests | 0 failures |
| Linting | 0 errors |
| Security | No vulnerabilities |
| Merge Readiness | ≥ 90% |

---

## Environment Variables

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export GITHUB_TOKEN="ghp_..."
```

---

## Workflow

1. **Make changes** ✏️
2. **Run `make pre-commit-check`** 🔍
3. **Fix any issues** 🔧
4. **Commit when green** ✅
5. **Push to trigger CI** 🚀

---

## Troubleshooting

### Coverage too low?
```bash
make coverage-report           # Generate HTML report
# Open htmlcov/index.html
```

### Lint errors?
```bash
make fix-all-enhanced          # Auto-fix everything
```

### Policy errors?
```bash
python scripts/utils/policy_loader.py --verbose
```

---

## Sparkline Legend

Coverage trend visualization:
```
▁▂▃▄▅▆▇█  → Increasing coverage (good)
█▇▆▅▄▃▂▁  → Decreasing coverage (bad)
▄▄▄▄▄▄▄▄  → Stable coverage
```

---

## Status Badges

| Symbol | Meaning |
|--------|---------|
| 🟢 | Healthy (≥ 85%) |
| 🟠 | Warning (80-85%) |
| 🔴 | Critical (< 80%) |

---

## Quick Links

- [Full Documentation](./CI_GOVERNANCE_IMPLEMENTATION_COMPLETE.md)
- [Policy Configuration](./merge_policy.yml)
- [Makefile Reference](./Makefile)

---

**💡 Pro Tip:** Run `make verify-all` before every push to ensure all checks pass!

