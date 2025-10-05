# 🚀 CI/CD Quick Reference Card

**Last Updated:** October 5, 2025

---

## ⚡ Quick Commands

```bash
# Setup
make setup                  # Initial setup

# Before Committing
make format                 # Auto-format code
make preflight-quick        # Fast validation (lint + test)

# Before Pushing
make verify-ci              # Full verification gate
make security-scan          # Security audit

# Check CI Health
make ci-health              # Generate health report
cat reports/ci_health.md    # View report
```

---

## 📊 Readiness Thresholds

| Threshold | Action |
|-----------|--------|
| **≥95%** | 🟢 Production-ready, auto-tag eligible |
| **≥90%** | 🟡 Merge approved, deploy to staging |
| **<90%** | 🔴 Merge blocked, fix issues first |
| **<80%** | 🔴 Critical, address immediately |

---

## 🔄 CI Workflow Status

| Job | Timeout | Retry | Required |
|-----|---------|-------|----------|
| lint-and-format | 15 min | ✅ | ✅ |
| test | 30 min | ✅ | ✅ |
| security-scan | 15 min | ✅ | ✅ |
| mcp-dry-run | 20 min | ✅ | ✅ |
| readiness-gate | 10 min | ✅ | ✅ |
| build | 15 min | ✅ | ✅ |
| verify_pipeline | 10 min | ✅ | ✅ |
| pr-comment | 5 min | ❌ | ❌ |

---

## 🛡️ Security Tools

```bash
# Bandit (Python security)
bandit -r packages/ src/

# pip-audit (vulnerabilities)
pip-audit --desc

# Full security scan
make security-scan
```

---

## 📈 Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Main CI pipeline |
| `.github/workflows/ci-health-report.yml` | Daily health reports |
| `.github/workflows/staging-smoke-test.yml` | Post-merge tests |
| `scripts/verify_release_pipeline.py` | Final verification |
| `scripts/ci_health_report.py` | Health analyzer |
| `.bandit` | Security config |
| `pyproject.toml` | pytest config |
| `Makefile` | Shortcuts |

---

## 🎯 PR Checklist

Before submitting a PR:
- [ ] Code formatted (`make format`)
- [ ] Linting passed (`make lint`)
- [ ] Tests passed (`make test`)
- [ ] Security scan clean (`make security-scan`)
- [ ] Full verification passed (`make verify-ci`)
- [ ] PR template completed

---

## 📊 Pytest Configuration

```bash
# Parallel execution
-n=auto

# Retry flaky tests
--reruns=2 --reruns-delay=1

# Stop on 5th failure
--maxfail=5

# Coverage requirement
--cov-fail-under=80
```

---

## 🔔 Notifications

| Event | Channel | Condition |
|-------|---------|-----------|
| Daily Health | Slack | Always (if configured) |
| CI Failure | Slack | Success rate <85% |
| Staging Deploy | Slack | After merge to main |
| PR Readiness | GitHub | Every PR |
| Release Tag | Slack | Auto-tagged (if enabled) |

---

## 🆘 Common Issues

### ❌ Tests failing?
```bash
pytest tests/test_name.py -v --tb=short
```

### ❌ Linting errors?
```bash
make format  # Auto-fix
make lint    # Check
```

### ❌ Security warnings?
```bash
make security-scan
pip list --outdated
```

### ❌ Low readiness?
```bash
make verify-ci
cat reports/verification_report.md
```

---

## 📚 Documentation

- **Quick Start:** `CI_QUICK_START.md`
- **Full Guide:** `CI_HARDENING_SUMMARY.md`
- **Verification:** `ENTERPRISE_CI_CD_VERIFICATION_REPORT.md`
- **Implementation:** `CI_CD_IMPLEMENTATION_COMPLETE.md`
- **Auto-Release:** `CI_AUTO_RELEASE_TAGGING.md`

---

## 🔗 Useful Links

- **CI Logs:** https://github.com/[repo]/actions
- **Reports:** `reports/`
- **Workflow Files:** `.github/workflows/`
- **Scripts:** `scripts/`

---

## 💡 Pro Tips

1. **Use caching** - Dependencies cached automatically
2. **Run locally first** - `make verify-ci` before pushing
3. **Monitor health** - Check `reports/ci_health.md` daily
4. **Fix flaky tests** - Mark with `@pytest.mark.flaky`
5. **Security first** - Run `make security-scan` regularly

---

**Need help?** Run `make help` or see `CI_QUICK_START.md`

