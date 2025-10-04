# 🧩 Stage Readiness Verification Tool

## Overview

The `verify_stage_readiness.py` script is a comprehensive CLI tool that automatically audits the repository and validates whether Stages 6.7, 6.8, and 6.8.1 have been properly committed, pushed, tested, and are ready for Stage 7.

## 🎯 Purpose

This tool serves as the final gate before Stage 7, ensuring:
- ✅ Observability layer (Stage 6.7) is present and committed  
- ✅ Runtime intelligence layer (Stage 6.8) files exist and are configured  
- ✅ AI Insight Agent + Postmortem Generator (Stage 6.8.1) are present  
- ✅ All relevant tests pass  
- ✅ CI workflows exist and are valid  
- ✅ Git history includes commits for each stage  
- ✅ No uncommitted changes remain  
- ✅ No broken imports or missing dependencies

## 🚀 Usage

### Basic Usage
```bash
python3 scripts/verify_stage_readiness.py
```

### CLI Options

```bash
# Strict mode - fail if coverage < 80%
python3 scripts/verify_stage_readiness.py --strict

# CI mode - exit code 1 if any check fails (for pipelines)
python3 scripts/verify_stage_readiness.py --ci

# Generate JSON report for dashboards
python3 scripts/verify_stage_readiness.py --json-output readiness_report.json

# Combine options
python3 scripts/verify_stage_readiness.py --strict --ci --json-output report.json
```

### Help
```bash
python3 scripts/verify_stage_readiness.py --help
```

## 🔍 Verification Checks

### 1. Git State Validation
- **Clean Working Tree**: Ensures no uncommitted changes
- **Branch Check**: Warns if not on expected branch (main, develop, or feature/*)
- **Commit History**: Looks for observability-related commits in recent history

### 2. File Structure Validation

#### Stage 6.7 – Observability Files
- `observability/metrics/metrics_middleware.py`
- `observability/tracing/otel_tracer.py` 
- `observability/logging/structured_logger.py`
- `observability/prometheus.yml`
- `observability/alertmanager.yml`

#### Stage 6.8 – Runtime Intelligence Files
- `observability/alerts/promql_rules.yml`
- `observability/alerts/anomaly_strategies.py`
- `observability/alerts/notifier.py`
- `observability/dashboards/service_dashboard.json`

#### Stage 6.8.1 – AI Agent Files
- `observability/ai_agent/incident_analyzer.py`
- `observability/ai_agent/postmortem_generator.py`
- `observability/ai_agent/integrations/slack_bot.py`
- `observability/ai_agent/main.py`

#### CI Workflow Files
- `.github/workflows/observability.yml`
- `.github/workflows/ci.yml`

### 3. Dependency Validation
- Checks `requirements.txt` for core dependencies:
  - `prometheus-client`
  - `opentelemetry-api`
  - `opentelemetry-sdk`
  - `opentelemetry-instrumentation-flask`
  - `numpy`
  - `scipy`
- Checks `observability/observability_requirements.txt` for ML dependencies

### 4. Test Validation
- Runs `pytest` to execute all tests
- Extracts test count from output
- Checks test coverage (optional, with `--strict` flag)
- Fails if any tests fail

### 5. CI Workflow Validation
- Validates YAML syntax for all workflow files
- Checks that observability workflow references validation scripts
- Ensures CI workflows are properly configured

## 📊 Output Format

### Terminal Output
The script provides color-coded output with emojis for easy reading:

```
🧩 Starting Stage 6.7 → 6.8.1 Readiness Audit
📦 Git State Validation
✅ Clean working tree
ℹ️ On branch: main
✅ Found 3 observability-related commits

📁 File Structure Validation
🔍 Stage 6.7 – Observability Checks
✅ observability/metrics/metrics_middleware.py found
✅ observability/tracing/otel_tracer.py found
...

📊 Summary Report
📋 VERIFICATION SUMMARY
✅ Passed: 4
⚠️ Warnings: 1
❌ Failures: 0
✅ All critical checks passed. Safe to proceed to Stage 7.
🚀 RESULT: READY FOR STAGE 7
```

### JSON Output
When using `--json-output`, the script generates a structured JSON report:

```json
{
  "timestamp": "2025-10-03T17:17:37.794819",
  "checks": {
    "git_status": {
      "passed": true,
      "issues": [],
      "commits_found": 3
    },
    "file_structure": {
      "passed": true,
      "missing_files": []
    },
    "dependencies": {
      "passed": true,
      "missing_deps": [],
      "found_deps": ["prometheus-client", "opentelemetry-api", ...]
    },
    "tests": {
      "passed": true,
      "test_results": {
        "status": "passed",
        "count": 127
      },
      "coverage": 85
    },
    "ci_workflows": {
      "passed": true,
      "workflow_issues": []
    }
  },
  "summary": {
    "passed": 5,
    "warnings": 0,
    "failures": 0
  },
  "ready_for_stage_7": true
}
```

## 🔧 Integration with CI/CD

### GitHub Actions Integration
Add this to your CI pipeline as a required job:

```yaml
name: Stage Readiness Check
on: [push, pull_request]

jobs:
  verify-readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Verify Stage Readiness
        run: python3 scripts/verify_stage_readiness.py --ci
```

### Pre-commit Hook
Add to `.git/hooks/pre-push`:

```bash
#!/bin/bash
python3 scripts/verify_stage_readiness.py --ci
if [ $? -ne 0 ]; then
    echo "❌ Stage readiness check failed. Push blocked."
    exit 1
fi
```

## 🚨 Exit Codes

- **0**: All checks passed, ready for Stage 7
- **1**: Critical issues found, not ready for Stage 7

## 📋 Checklist Before Running

Before running the verification script, ensure:

1. **All observability files are committed**:
   ```bash
   git add observability/
   git add .github/workflows/observability.yml
   git commit -m "feat: implement Stage 6.7-6.8.1 observability stack"
   ```

2. **Tests are passing**:
   ```bash
   pip install pytest pytest-cov
   python3 -m pytest
   ```

3. **Dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   pip install -r observability/observability_requirements.txt
   ```

## 🛠️ Troubleshooting

### Common Issues

#### "pytest not available"
```bash
pip install pytest pytest-cov
```

#### "Uncommitted changes detected"
```bash
git add .
git commit -m "feat: implement observability features"
```

#### "Missing dependencies"
Add missing dependencies to `requirements.txt`:
```bash
echo "numpy>=1.21.0" >> requirements.txt
echo "scipy>=1.7.0" >> requirements.txt
pip install -r requirements.txt
```

#### "No observability-related commits found"
Ensure commits mention observability keywords:
```bash
git commit -m "feat: implement Stage 6.7 observability layer"
git commit -m "feat: add runtime intelligence (Stage 6.8)"
git commit -m "feat: implement AI incident agent (Stage 6.8.1)"
```

## 🎯 Best Practices

1. **Run before every merge to main**
2. **Use in CI pipelines as a gate**
3. **Generate JSON reports for dashboards**
4. **Fix warnings before proceeding to Stage 7**
5. **Keep observability commits descriptive**

## 📈 Future Enhancements

Potential improvements:
- Slack notifications on failure
- Integration with monitoring dashboards
- Historical trend analysis
- Auto-remediation suggestions
- Performance benchmarks validation

## 🔗 Related Files

- `observability/README.md` - Observability setup guide
- `.github/workflows/observability.yml` - CI workflow
- `scripts/check_observability_hooks.py` - Hook validation
- `scripts/validate_alert_rules.py` - Alert rules validation

---

**Note**: This tool is designed to be the final gate before Stage 7. Always ensure all checks pass before proceeding to autonomous operations.
