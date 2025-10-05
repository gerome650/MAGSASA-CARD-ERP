# 🚀 CI/CD Quick Start Guide

## 2-Minute Setup

### 1. Install Dependencies
```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync --dev
```

### 2. Run Local Validation
```bash
# Quick validation (lint + format + test)
make preflight-quick

# Full validation (includes security scans)
make verify-ci
```

### 3. Check CI Health
```bash
# Generate CI health report
make ci-health

# View reports
cat reports/ci_health.md
```

## 🔧 Available Commands

### Code Quality
```bash
make lint          # Run all linting (ruff, black, mypy)
make format        # Format code automatically
make test          # Run tests with coverage
make security-scan # Run security scans (Bandit + pip-audit)
```

### CI Verification
```bash
make verify-ci     # Final CI verification gate
make ci-preflight  # Full CI checks before pushing
make ci-health     # Generate CI health report
```

### Development
```bash
make setup         # Complete development setup
make clean         # Clean build artifacts
make build         # Build all packages
```

## 🛡️ Security Scanning

### Local Security Check
```bash
make security-scan
```

This runs:
- **Bandit** - Static security analysis
- **pip-audit** - Dependency vulnerability scanning
- **Safety** - Additional vulnerability checks

### Security Configuration
- `.bandit` - Custom Bandit configuration
- Excludes test files and build directories
- Configurable severity levels

## 📊 CI Health Monitoring

### Daily Reports
- **Automatic** - Generated daily at 09:00 UTC
- **Location** - `reports/ci_health.json` and `reports/ci_health.md`
- **Metrics** - Success rate, duration, failure trends

### Manual Generation
```bash
make ci-health
```

## 🔄 Pre-commit Hooks

### Install Hooks
```bash
make install-hooks
```

### Remove Hooks
```bash
make remove-hooks
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Linting Failures
```bash
make format  # Auto-fix formatting issues
```

#### 2. Test Failures
```bash
make quick-test  # Run tests without coverage for speed
```

#### 3. Security Warnings
```bash
# Check specific issues
bandit -r src/ --severity-level high
```

#### 4. Dependency Issues
```bash
# Update dependencies
uv sync --dev

# Check for vulnerabilities
pip-audit --desc
```

### Getting Help
```bash
make help  # Show all available commands
```

## 📈 Performance Tips

### Faster Development
1. **Use caching** - UV automatically caches dependencies
2. **Parallel tests** - pytest runs tests in parallel by default
3. **Quick validation** - Use `make preflight-quick` for fast feedback

### CI Optimization
1. **Dependency caching** - GitHub Actions caches UV and pip
2. **Concurrency control** - Superseded runs are cancelled
3. **Retry logic** - Failed jobs automatically retry

## 🎯 Release Process

### Pre-Release Checklist
1. ✅ Run `make verify-ci` (must pass)
2. ✅ Check `reports/ci_health.md` (success rate ≥90%)
3. ✅ Security scans pass
4. ✅ All tests pass with coverage ≥80%

### Release Gates
- **Readiness Score** - Must be ≥90%
- **Security Scan** - No high-severity issues
- **Test Coverage** - Must be ≥80%
- **Linting** - All checks must pass

## 📞 Support

### Documentation
- `CI_HARDENING_SUMMARY.md` - Complete implementation details
- `reports/ci_health.md` - Daily health reports
- `.github/workflows/` - Workflow configurations

### Scripts
- `scripts/verify_release_pipeline.py` - Release verification
- `scripts/ci_health_report.py` - Health report generation
- `scripts/` - All automation and utility scripts

---

**Ready to go!** 🚀

Run `make verify-ci` to ensure everything is working correctly.
