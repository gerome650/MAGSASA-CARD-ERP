# 🛡️ Governance System - Quick Reference Card

> **TL;DR**: One-page cheat sheet for the governance and PR author system

---

## ⚡ Essential Commands

```bash
# 🪝 Install Hooks (Run Once)
make install-governance-hooks

# ✅ Before Committing
make verify-all

# 📊 Check Status
make governance-report

# 🎯 Merge Score
make calculate-merge-score
```

---

## 🎯 Quality Gates

| Gate | Threshold | Command | Fails PR? |
|------|-----------|---------|-----------|
| **Coverage** | ≥85% | `make enforce-coverage` | ✅ Yes |
| **Tests** | 100% pass | `pytest tests/` | ✅ Yes |
| **Linting** | 0 violations | `ruff check .` | ✅ Yes |
| **Merge Score** | ≥80/100 | `make calculate-merge-score` | ✅ Yes |

---

## 📊 Merge Score Breakdown

```
Total Score = Coverage×30% + Tests×30% + Linting×20% + Reviews×15% + Docs×5%
```

| Component | Weight | How to Improve |
|-----------|--------|----------------|
| Coverage | 30% | Add tests, remove dead code |
| Tests | 30% | Fix failing tests |
| Linting | 20% | Run `ruff check --fix .` |
| Reviews | 15% | Get PR reviews |
| Documentation | 5% | Add PR description |

---

## 🪝 Git Hooks

### Pre-Commit Hook (Runs on `git commit`)
1. ✨ Format code (Black)
2. 🧹 Lint code (Ruff)
3. 🔍 Type check (Mypy)
4. 🧪 Run unit tests

**Bypass:** `git commit --no-verify` ⚠️

### Post-Push Hook (Runs on `git push`)
1. 📊 Check coverage
2. 📣 Send Slack notification

---

## 📣 Slack Notifications

### Setup
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### Test
```bash
make notify-slack-enhanced
```

### What Gets Sent?
- 👤 PR author mention (@username)
- 📊 Coverage with sparkline (87.5% ▁▃▄▆█)
- 🎯 Merge score (85/100 ✅)
- ✅ Test results (50/50 passed)
- 🧹 Lint status (0 violations)

---

## 📈 Coverage Commands

```bash
# Track trend
make coverage-trend

# Generate badge
make coverage-badge

# Enforce threshold
make enforce-coverage

# Add manual data point
python scripts/metrics/coverage_trend.py --add 87.5
```

---

## 🚨 Common Issues & Fixes

### Issue: Coverage Too Low
```bash
# View coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# Focus on missing areas
pytest --cov --cov-report=term-missing
```

### Issue: Linting Failures
```bash
# Auto-fix most issues
ruff check --fix .
black .

# Check what's left
ruff check .
```

### Issue: Tests Failing
```bash
# Run verbose tests
pytest tests/ -v --tb=short

# Run specific test
pytest tests/test_specific.py::test_name -v
```

### Issue: Hooks Not Working
```bash
# Reinstall
make uninstall-governance-hooks
make install-governance-hooks

# Verify
ls -la .git/hooks/pre-commit
```

---

## 📋 Pre-Push Checklist

```
□ Run make verify-all
□ Check make governance-report
□ Coverage ≥85%
□ All tests passing
□ Zero lint violations
□ Merge score ≥80
□ PR description added
```

---

## 🔧 Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `merge_policy.yml` | Governance rules | Repo root |
| `.git/hooks/pre-commit` | Pre-commit hook | Auto-generated |
| `.git/hooks/post-push` | Post-push hook | Auto-generated |
| `.coverage_history.json` | Coverage trend data | Repo root |
| `badges/coverage.svg` | Coverage badge | badges/ |

---

## 🎯 Target Metrics

```yaml
Coverage:   85% minimum → 90% warning → 95% target
Tests:      100% pass rate
Linting:    0 violations
Merge Score: 80/100 minimum
```

---

## 📖 Full Documentation

**Comprehensive Guide:** [PR_AUTHOR_INTEGRATION_GUIDE.md](PR_AUTHOR_INTEGRATION_GUIDE.md)

**Policy Reference:** [merge_policy.yml](merge_policy.yml)

**CI Workflow:** [.github/workflows/merge-gate.yml](.github/workflows/merge-gate.yml)

---

## 🆘 Emergency Bypass

**Only use in emergencies (hotfixes, critical bugs):**

```bash
# Skip pre-commit hook
git commit --no-verify

# Disable policy enforcement temporarily
# Edit merge_policy.yml:
enforcement_mode: "warn"  # Change from "strict"
fail_on_violation: false  # Change from true
```

⚠️ **Remember to re-enable after emergency!**

---

## 💡 Pro Tips

1. **Run `make verify-all` before pushing** - Catches issues early
2. **Check `make governance-report` weekly** - Track progress
3. **Keep coverage trending up** - Small improvements add up
4. **Fix lint issues immediately** - Don't let them accumulate
5. **Review policy quarterly** - Adjust thresholds as needed

---

## 🚀 Quick Start (New Team Member)

```bash
# 1. Clone repo
git clone <repo-url>
cd MAGSASA-CARD-ERP

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install hooks
make install-governance-hooks

# 4. Run first check
make verify-all

# 5. Read full guide
cat PR_AUTHOR_INTEGRATION_GUIDE.md
```

---

**Questions?** Read the [full integration guide](PR_AUTHOR_INTEGRATION_GUIDE.md) or open an issue.

---

*Generated: October 6, 2025 | Version: 1.0.0*



