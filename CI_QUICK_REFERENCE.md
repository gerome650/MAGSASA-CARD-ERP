# CI/CD Verification Quick Reference

## 🚀 Quick Start

### Run Full CI Verification (Same as CI Pipeline)
```bash
make verify-ci
```

This runs all four checks:
- ✅ Linting (Ruff, Black, MyPy)
- ✅ Tests (with coverage ≥65%)
- ✅ Security (Bandit + pip-audit)
- ✅ Readiness (Release score)

---

## 🐛 Debug Locally

### New: Quick CI Debug
```bash
make ci-debug
```

Runs step-by-step:
1. Linting
2. Tests with coverage
3. Security scan

**Use this for local debugging before pushing!**

---

## 📝 Individual Checks

### Linting Only
```bash
make lint
```

### Tests Only
```bash
make test
```

### Security Scan Only
```bash
make security-scan
```

### Format Code
```bash
make format
```

---

## 🔍 Understanding Results

### ✅ All Checks Pass
```
╭───────────────────────────────────────────────────╮
│ 🎉 Release Pipeline Verification PASSED           │
│ All checks completed successfully.                │
╰───────────────────────────────────────────────────╯
```

**Action:** You're ready to push! ✨

### ❌ Linting Fails
```
❌ Ruff linting failed: [error details]
```

**Action:** Run `make format` to auto-fix, then `make lint` to verify

### ❌ Tests Fail
```
❌ Tests failed: [error details]
⚠️  Missing pytest plugins. Run: uv add --dev pytest-xdist pytest-rerunfailures
```

**Action:** 
1. Check if pytest plugins are missing → install them
2. Review test failures
3. Fix tests and re-run `make test`

### ⚠️ GH_TOKEN Warning
```
⚠️  GH_TOKEN not found — skipping GitHub readiness check (safe in local dev)
```

**Action:** This is normal for local development. CI will check it automatically.

---

## 🎯 Before Pushing Checklist

```bash
# 1. Format your code
make format

# 2. Run local CI debug
make ci-debug

# 3. Run full verification
make verify-ci

# 4. Push with confidence! 🚀
git push
```

---

## 💡 Pro Tips

### Speed Up Local Testing
```bash
# Quick test without coverage
make quick-test

# Quick preflight (no security scan)
make preflight-quick
```

### Coverage Reports
```bash
# Generate detailed coverage report
make coverage-report

# View in browser
open htmlcov/index.html
```

### Help Menu
```bash
# See all available commands
make help
```

---

## 🛠️ Configuration Details

### Test Configuration
- **Parallel execution:** `-n=auto` (uses all CPU cores)
- **Retry flaky tests:** `--reruns=2` with 1s delay
- **Coverage threshold:** 65% minimum
- **Max failures:** Stops after 5 failures

### Linting Configuration
- **Ruff:** Python code quality + imports
- **Black:** Code formatting (88 char line length)
- **MyPy:** Type checking (with ignore for missing imports)

### Security Configuration
- **Bandit:** Medium severity + confidence
- **pip-audit:** Dependency vulnerability scanning

---

## 🔧 Troubleshooting

### "pytest-xdist not found"
```bash
uv add --dev pytest-xdist pytest-rerunfailures
```

### "Coverage too low"
Current threshold is 65%. To see what's not covered:
```bash
make coverage-report
open htmlcov/index.html
```

### "Linting fails but I formatted"
Make sure you're using the latest version:
```bash
uv sync --dev
make format
make lint
```

### "Security scan shows warnings"
Security warnings don't fail the pipeline but should be reviewed:
```bash
make security-scan
# Review warnings and update dependencies if needed
```

---

## 📚 Related Documentation

- **Full Implementation Report:** `CI_VERIFICATION_IMPROVEMENTS.md`
- **Makefile Help:** Run `make help`
- **Verification Script:** `scripts/verify_release_pipeline.py`

---

**Last Updated:** October 5, 2025


