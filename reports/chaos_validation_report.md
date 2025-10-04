# Pre-Push Chaos Validation Report

**Generated:** 2025-10-04T12:12:15.599536
**Checks Passed:** 5
**Checks Failed:** 2
**Warnings:** 0

## Summary

❌ **2 check(s) failed.** Please fix before pushing.

## Issues Found

- ❌ Missing dependencies detected
- ❌ Import failed: deploy/chaos_injector.py
- ❌ Import failed: deploy/resilience_validator.py
- ❌ Import failed: deploy/chaos_metrics_exporter.py
- ❌ Chaos injector timeout

## Recommendations

### Critical Actions

1. Fix all critical issues listed above
2. Re-run validation: `python scripts/validate_chaos_local.py`
3. Use `--fix` flag to auto-fix common issues: `python scripts/validate_chaos_local.py --fix`

## Next Steps

- ✅ Commit changes if all checks passed
- 🚀 Push to trigger CI/CD pipeline
- 📊 Monitor chaos validation job in GitHub Actions
