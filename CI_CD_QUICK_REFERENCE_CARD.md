# CI/CD Quick Reference Card 🚀

**Last Updated:** October 5, 2025  
**Status:** ✅ Production-Ready

---

## 🎯 Essential Commands

### Full CI Verification
```bash
make verify-ci
```
**What it does:** Runs complete CI gate (lint → test → security → readiness)  
**When to use:** Before pushing code or creating a PR  
**Exit codes:** 0 = success, 1 = failure

---

### Debug CI Issues
```bash
make ci-debug
```
**What it does:** Runs CI checks step-by-step with detailed output  
**When to use:** When `verify-ci` fails and you need to debug  
**Steps:** Linting → Tests → Security (each isolated)

---

### Individual Checks

#### Linting Only
```bash
make lint
```
**Runs:** ruff, black, mypy  
**Fast:** ~5-10 seconds

#### Tests Only
```bash
make test
```
**Features:**  
- Parallel execution (`-n=auto`)
- Retry flaky tests (2 retries, 1s delay)
- Coverage enforcement (≥65%)
- Detailed reports in `htmlcov/`

#### Security Only
```bash
make security-scan
```
**Runs:** Bandit + pip-audit + dependency check  
**Non-blocking:** Warnings don't fail the build

---

## 🔍 CI Health Monitoring

### Generate Health Report
```bash
make ci-health
```
**Shows:**
- CI pass/fail rates
- Average build duration
- Flaky test detection
- Trend analysis

---

## 💡 Pro Tips

### Quick Format & Test
```bash
make format && make test
```

### Local Pre-Push Check
```bash
make ci-debug  # If issues found, debug here
make verify-ci # Final gate before push
```

### Coverage Report
```bash
make coverage-report
open htmlcov/index.html  # View in browser
```

---

## 🚨 Common Errors & Solutions

### Error: "pytest-xdist not found"
**Solution:**
```bash
uv add --dev pytest-xdist pytest-rerunfailures
```

### Error: "GH_TOKEN not found"
**Local Dev:** ⚠️ Warning only (safe to ignore)  
**CI:** ❌ Required (set in GitHub Actions secrets)

### Error: "Coverage below 65%"
**Quick Fix:**
```bash
# Check which files lack coverage
make coverage-report
open htmlcov/index.html
# Add tests for uncovered lines
```

### Error: "Linting failed"
**Auto-Fix:**
```bash
make format  # Auto-fixes most issues
make lint    # Verify
```

---

## 📊 CI/CD Pipeline Architecture

```
Developer → make verify-ci → GitHub Actions → Deploy
              ↓
         ✅ Linting
         ✅ Tests (65% coverage)
         ✅ Security scans
         ✅ Readiness score
```

---

## 🔐 Security Scanning

### What's Checked
1. **Bandit:** Static analysis for Python security issues
2. **pip-audit:** Known vulnerabilities in dependencies
3. **pip check:** Dependency conflicts

### Severity Levels
- **Medium+:** Reported (non-blocking)
- **High+:** Requires attention
- **Critical:** Must fix before release

---

## 📈 Coverage Requirements

| Target | Threshold | Current |
|--------|-----------|---------|
| Packages | ≥65% | Enforced |
| Individual files | ≥50% | Recommended |
| Critical paths | ≥80% | Best practice |

---

## 🎓 Learning Resources

### Understanding pytest Flags
```bash
-n=auto              # Parallel execution (uses all CPU cores)
--reruns=2           # Retry failed tests up to 2 times
--reruns-delay=1     # Wait 1 second between retries
--cov-fail-under=65  # Fail if coverage < 65%
--maxfail=5          # Stop after 5 failures
-x                   # Stop on first failure (CI mode)
```

### Reading Verification Output
```
✅ PASS  = All checks succeeded
❌ FAIL  = Action required
⚠️  WARN  = Advisory (non-blocking)
```

---

## 🛠️ Makefile Targets

| Command | Purpose | Time |
|---------|---------|------|
| `make help` | Show all commands | 1s |
| `make lint` | Code quality checks | 10s |
| `make test` | Run test suite | 30s |
| `make security-scan` | Security analysis | 15s |
| `make verify-ci` | Full CI gate | 60s |
| `make ci-debug` | Step-by-step debug | 60s |
| `make ci-health` | Generate health report | 5s |
| `make format` | Auto-format code | 5s |
| `make quick-test` | Fast tests (no coverage) | 15s |

---

## 🔄 CI/CD Workflow Best Practices

### Before Committing
```bash
make format           # Auto-format
make lint            # Quick check
```

### Before Pushing
```bash
make verify-ci       # Full gate
```

### Debugging Failures
```bash
make ci-debug        # Step-by-step
# Fix issues
make verify-ci       # Verify fix
```

### Daily Health Check
```bash
make ci-health       # View trends
```

---

## 📝 Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `GH_TOKEN` | GitHub API access | CI: Yes, Local: No |
| `AGS_MCP_ENABLED` | Enable MCP mode | Optional |
| `CI` | Detect CI environment | Auto-set |

---

## 🎯 Success Indicators

### All Green ✅
```
✅ Linting checks passed
✅ Test suite passed
✅ Security scans completed
✅ Readiness score passed
🎉 Release Pipeline Verification PASSED
```

### Needs Attention ❌
```
❌ Linting failed
❌ Tests failed or coverage too low
❌ Security issues found
```

---

## 💼 For CI/CD Engineers

### Pipeline Configuration
- **Test runner:** pytest with xdist + rerunfailures
- **Coverage:** pytest-cov with 65% minimum
- **Linting:** ruff + black + mypy
- **Security:** bandit + pip-audit

### Performance Optimization
- Parallel test execution reduces time by ~60%
- Retry logic handles flaky tests automatically
- Coverage reports cached for faster builds

### Monitoring
- CI health reports track trends
- Automated failure analysis available
- GitHub Actions integration ready

---

## 🚀 Quick Start for New Developers

1. **Setup:**
   ```bash
   make setup
   ```

2. **Verify installation:**
   ```bash
   make lint
   make test
   ```

3. **Before every push:**
   ```bash
   make verify-ci
   ```

4. **If issues found:**
   ```bash
   make ci-debug  # Debug step-by-step
   ```

---

## 📞 Getting Help

- **CI Issues:** Check `CI_CD_HARDENING_COMPLETE.md`
- **Test Failures:** Run `make ci-debug`
- **Coverage Issues:** Run `make coverage-report`
- **Security Alerts:** Check `make security-scan` output

---

**Pro Tip:** Pin this reference card to your terminal or IDE for quick access! 📌

---

**Generated:** October 5, 2025  
**Version:** 1.0.0  
**Maintainer:** DevOps Team

