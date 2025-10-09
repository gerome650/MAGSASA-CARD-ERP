# 🧪 QA Observability & Governance Consistency Checker

## Overview

The QA Observability & Governance Consistency Checker is an automated CI check that runs on pull requests to ensure consistency across observability and governance configuration files.

## What It Does

The checker validates:

### 1. **YAML Validity** ✅
- Parses `specs/observer_guardrails.yaml`
- Validates required keys and structure
- Ensures all critical configuration is present

### 2. **Threshold Consistency** 🎯
Verifies that thresholds are consistent across all files:

| Threshold | Expected Value | Files Checked |
|-----------|----------------|---------------|
| `uptime_warn` | ≥ 99.0% | observer_guardrails.yaml, render_integration.md, pr-governance-check.yml |
| `uptime_fail` | ≥ 98.0% | observer_guardrails.yaml, render_integration.md, pr-governance-check.yml |
| `latency_warn` | ≤ 2500ms | observer_guardrails.yaml, render_integration.md |
| `latency_fail` | ≤ 4000ms | observer_guardrails.yaml, render_integration.md, pr-governance-check.yml |
| `drift_warn` | ≤ 2% | observer_guardrails.yaml |
| `drift_fail` | ≤ 5% | observer_guardrails.yaml, pr-governance-check.yml |

### 3. **Secrets Presence** 🔐
- Verifies required secrets are referenced in workflows
- Checks documentation mentions secrets in relevant spec files
- Required secrets:
  - `RENDER_API_KEY`
  - `RENDER_SERVICE_ID`
  - `SLACK_GOVERNANCE_WEBHOOK`

### 4. **Observer Charter Sync** 📋
- Ensures `specs/mcp-architecture.md` contains the Alert Loop diagram
- Validates the four-hop flow: **Render → Governance → Slack → Observer**

### 5. **Guardrails Alignment** 🛡️
- Audit trail retention ≥ 180 days
- Minimum test coverage ≥ 85%

## When It Runs

The check automatically runs when a PR modifies any of these files:

- `specs/observer_guardrails.yaml`
- `specs/render_integration.md`
- `specs/slack_integration.md`
- `specs/mcp-architecture.md`
- `.github/workflows/pr-governance-check.yml`

## How to Run Locally

### Prerequisites
```bash
# Optional: Install PyYAML for full YAML validation
pip install pyyaml
```

### Run the checker
```bash
# From repository root
python3 scripts/qa/obs_governance_consistency.py

# With explicit SHAs
GITHUB_BASE_SHA=abc123 GITHUB_HEAD_SHA=def456 \
  python3 scripts/qa/obs_governance_consistency.py
```

### Output
- **JSON** (stdout): Machine-readable results
- **Markdown** (`qa_summary.md`): Human-readable report

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed (warnings allowed) |
| 1 | Critical errors found |

## Example Output

### Success ✅
```json
{
  "status": "pass",
  "errors": [],
  "warnings": [],
  "files_checked": [
    "specs/observer_guardrails.yaml",
    "specs/mcp-architecture.md"
  ]
}
```

### Failure ❌
```json
{
  "status": "fail",
  "errors": [
    {
      "check": "Threshold Consistency",
      "status": "error",
      "message": "Threshold latency_warn mismatch: expected 2500, found observer_guardrails.yaml=2000",
      "remediation": "Update all files to use latency_warn=2500"
    }
  ],
  "warnings": [],
  "files_checked": [...]
}
```

## How to Fix Errors

### Threshold Mismatch
1. Identify the mismatched value in the error message
2. Update the relevant file(s) to use the expected threshold
3. Ensure the threshold appears in all required files

### YAML Invalid
1. Check the YAML syntax in `specs/observer_guardrails.yaml`
2. Verify all required keys are present
3. Use `yamllint` or an online validator to debug

### Missing Secrets Documentation
1. Add the secret name to the relevant spec file:
   - Render secrets → `specs/render_integration.md`
   - Slack secrets → `specs/slack_integration.md`
2. Include setup instructions and usage examples

### Observer Charter Sync Issues
1. Ensure `specs/mcp-architecture.md` has an "Alert Loop" section
2. Verify all four components are mentioned: Render, Governance, Slack, Observer
3. Add a diagram or description of the flow

### Guardrails Misalignment
1. Update `specs/observer_guardrails.yaml`:
   ```yaml
   observer_guardrails:
     audit_trail_retention_days: 180  # minimum
     coverage_and_testing:
       min_coverage_percent: 85  # minimum
   ```

## CI Integration

The check is integrated into the PR Governance workflow as Job 9:

```yaml
qa-observability-consistency:
  name: 🧪 QA Observability & Governance Consistency
  runs-on: ubuntu-latest
  if: ${{ github.event_name == 'pull_request' }}
  steps:
    - name: Run consistency checks
      run: python3 scripts/qa/obs_governance_consistency.py
    - name: Post QA summary as sticky PR comment
      uses: marocchino/sticky-pull-request-comment@v2
```

### PR Comment

The checker posts a sticky comment on the PR with:
- ✅/❌ status for each check
- Error and warning messages
- Remediation steps
- Files checked

## Maintenance

### Adding New Checks

To add a new check:

1. Add a new method to the `ConsistencyChecker` class:
   ```python
   def _check_new_validation(self):
       print("\n🔍 Checking new validation...")
       # Your validation logic
       if validation_fails:
           self.errors.append(CheckResult(...))
   ```

2. Call it from the `run()` method:
   ```python
   def run(self):
       # ... existing checks ...
       self._check_new_validation()
   ```

### Updating Thresholds

Update the `EXPECTED_THRESHOLDS` dictionary in the checker:

```python
EXPECTED_THRESHOLDS = {
    "uptime_warn": 99.5,  # Changed from 99.0
    # ...
}
```

### Adding Watched Files

Update the `WATCH_FILES` list:

```python
WATCH_FILES = [
    "specs/observer_guardrails.yaml",
    "specs/new_config_file.yaml",  # New file
    # ...
]
```

## Troubleshooting

### Script fails with import error
```bash
# Install PyYAML
pip install pyyaml

# Or run without it (fallback parser will be used)
python3 scripts/qa/obs_governance_consistency.py
```

### Can't determine changed files
The script falls back to checking all files if git operations fail. This is expected behavior in CI environments without proper git history.

### False positives
If the checker incorrectly flags an issue:
1. Review the error message and remediation
2. Check if the expected threshold is outdated
3. Update the script if needed

## 🚨 Slack Escalation on Failure

### Overview

When QA checks fail, the system automatically escalates alerts to Slack using the configured webhook. This enables proactive governance and immediate team visibility into issues.

### Configuration

**Required Secret:**
```yaml
secrets.SLACK_GOVERNANCE_WEBHOOK
```

**Setup in GitHub:**
1. Go to Repository Settings → Secrets and Variables → Actions
2. Add secret: `SLACK_GOVERNANCE_WEBHOOK`
3. Value: Your Slack webhook URL (e.g., `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX`)

**Get Slack Webhook URL:**
1. Go to https://api.slack.com/apps
2. Create or select your app
3. Navigate to "Incoming Webhooks"
4. Add webhook to your desired channel
5. Copy the webhook URL

### Slack Message Format

When errors are detected, the system sends a structured alert:

```
🚨 Governance QA Check Failed on PR #42
❌ 2 Errors | ⚠️ 1 Warning
• latency_warn expected 2500, found 4000
• drift_fail expected 5, found 7
🔗 https://github.com/your-org/your-repo/pull/42
```

**Message Components:**
- **PR Number**: Automatically extracted from GitHub context
- **Error/Warning Count**: Summary of check results
- **Top 3 Mismatches**: Most critical threshold violations
- **Direct PR Link**: One-click access to the failing PR

### When Alerts Trigger

Slack alerts are sent when:
- ❌ **Errors detected**: Any threshold mismatch or critical validation failure
- ⚠️ **Warnings only**: NO alert (warnings don't block merge)

### Testing Slack Integration

Test your webhook locally:

```bash
# Generate Slack payload
export GITHUB_PR_NUMBER=123
export GITHUB_REPOSITORY="your-org/your-repo"
python3 scripts/qa/obs_governance_consistency.py --slack-payload

# Send test message
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
MESSAGE=$(python3 scripts/qa/obs_governance_consistency.py --slack-payload)

curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\": \"$MESSAGE\"}" \
  "$SLACK_WEBHOOK"
```

### Workflow Integration

```yaml
- name: 🚨 Slack Escalation on QA Failure
  if: failure() || steps.qa_check.outputs.qa_failed == 'true'
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
  run: |
    MESSAGE=$(python3 scripts/qa/obs_governance_consistency.py --slack-payload)
    PAYLOAD=$(jq -n --arg text "$MESSAGE" '{text: $text}')
    curl -X POST -H 'Content-type: application/json' \
      --data "$PAYLOAD" \
      "$SLACK_WEBHOOK"
```

## 📊 Smart Diff Table

### Overview

The smart diff table provides a structured view of threshold mismatches, making it easy to identify and fix configuration drift.

### Example Diff Table

When mismatches are detected, the system generates:

| Metric | Expected | Found | Source File | Status |
|--------|----------|-------|-------------|--------|
| latency_warn | 2500 | 4000 | .github/workflows/pr-governance-check.yml | ❌ |
| uptime_fail | 98.0 | 95.0 | specs/observer_guardrails.yaml | ❌ |
| drift_warn | 2 | 3 | specs/render_integration.md | ❌ |

### Where to Find It

The diff table appears in:
1. **qa_summary.md** - Full report with all mismatches
2. **PR Comments** - Sticky comment on the pull request
3. **Governance Summary** - Integrated into the final governance report

### Using the Diff Table

**Quick Fix Workflow:**
1. Review the diff table in the PR comment
2. Identify the source file with incorrect value
3. Update the file with the expected value
4. Re-run checks to verify

**Example Fix:**
```bash
# Identified: latency_warn = 4000 in pr-governance-check.yml (expected: 2500)

# Fix:
# Open .github/workflows/pr-governance-check.yml
# Find: LATENCY > 4000
# Replace with: LATENCY > 2500

git add .github/workflows/pr-governance-check.yml
git commit -m "fix: align latency threshold to 2500ms"
git push
```

## 💾 Drift History & Dashboard Prep

### Overview

The QA checker now saves machine-readable artifacts for every run, enabling future drift tracking and historical analysis.

### Artifacts Generated

**1. qa_results.json**
```json
{
  "pr_number": "123",
  "errors_count": 2,
  "warnings_count": 1,
  "metrics_mismatched": ["latency_warn", "drift_fail"],
  "mismatches": [
    {
      "metric": "latency_warn",
      "expected": 2500,
      "found": 4000,
      "source_file": "pr-governance-check.yml"
    }
  ],
  "timestamp": "2025-10-09T12:34:56Z",
  "files_checked": ["specs/observer_guardrails.yaml", "..."]
}
```

### Storage Location

```
scripts/qa/history/
├── qa_results_123456789.json  # GitHub run_id
├── qa_results_123456790.json
└── .gitkeep
```

### Retention

- **Workflow Artifacts**: 90 days (configurable)
- **History Directory**: Stored in repository (optional)
- **Artifact Name**: `qa-results-{github.run_id}`

### Accessing Artifacts

**Via GitHub Actions:**
```bash
# Download latest artifact
gh run download <run-id> -n qa-results-<run-id>

# List all artifacts
gh run list --workflow="pr-governance-check.yml"
```

**Via API:**
```bash
# List artifacts for a workflow run
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/runs/<run-id>/artifacts

# Download artifact
curl -L -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/artifacts/<artifact-id>/zip \
  -o qa-results.zip
```

### Future: Drift Dashboard

The stored artifacts enable future enhancements:

**Planned Features:**
- 📈 Trend analysis: Track threshold drift over time
- 🎯 Compliance scoring: Measure governance adherence
- 📊 Visualization: Drift charts and heatmaps
- 🔔 Proactive alerts: Detect drift patterns before they cause issues
- 📋 Historical reports: Compare QA results across PRs

**Integration Points:**
- Observer dashboard (`ci-dashboard/`)
- Notion AI Studio integration
- Slack daily digest

### CLI Arguments

**New CLI Options:**

```bash
# Run with debug output
python3 scripts/qa/obs_governance_consistency.py --debug

# Generate Slack payload only (no full run)
python3 scripts/qa/obs_governance_consistency.py --slack-payload

# Standard run (generates all outputs)
python3 scripts/qa/obs_governance_consistency.py
```

**--debug Flag:**
- Shows detailed parsing results
- Prints threshold extraction details
- Helps troubleshoot regex patterns

**--slack-payload Flag:**
- Runs checks silently
- Outputs Slack-formatted message
- Used by CI for alert generation

## Before & After Comparison

| Feature | Before | After |
|---------|--------|-------|
| **Failure Visibility** | Manual log-checking | Slack alerts within 10s |
| **Threshold Reporting** | Raw mismatch text | Structured diff table |
| **Historical Tracking** | None | JSON artifacts + 90-day retention |
| **Governance Model** | Reactive | Proactive + alert-driven |
| **Fix Workflow** | Parse logs manually | Review diff table → fix → rerun |
| **Team Awareness** | Check CI periodically | Slack notification on failure |

## Example Scenarios

### Scenario 1: Threshold Mismatch Detected

**1. PR opens with incorrect threshold**
```yaml
# .github/workflows/pr-governance-check.yml
LATENCY > 5000  # Wrong! Should be 4000
```

**2. QA checker runs and detects mismatch**
```
❌ Threshold latency_fail mismatch: expected 4000, found 5000
```

**3. Slack alert sent**
```
🚨 Governance QA Check Failed on PR #42
❌ 1 Error
• latency_fail expected 4000, found 5000
🔗 https://github.com/your-org/your-repo/pull/42
```

**4. Developer sees PR comment with diff table**

| Metric | Expected | Found | Source File | Status |
|--------|----------|-------|-------------|--------|
| latency_fail | 4000 | 5000 | pr-governance-check.yml | ❌ |

**5. Developer fixes and pushes**
```bash
# Update threshold to 4000
git add .github/workflows/pr-governance-check.yml
git commit -m "fix: correct latency threshold to 4000ms"
git push
```

**6. QA re-runs → ✅ All checks pass**

### Scenario 2: All Checks Pass

**1. PR opened with correct thresholds**

**2. QA checker runs**
```
✅ uptime_warn = 99.0 (consistent)
✅ latency_warn = 2500 (consistent)
✅ drift_fail = 5 (consistent)
```

**3. No Slack alert** (warnings don't trigger alerts)

**4. PR comment shows success**
```
## 🧪 QA Consistency Report
**Status:** ✅ PASSED
- Errors: 0
- Warnings: 0
```

**5. Artifacts still saved for history**
```json
{
  "pr_number": "43",
  "errors_count": 0,
  "warnings_count": 0,
  "metrics_mismatched": []
}
```

## See Also

- [PR Governance Workflow](../.github/workflows/pr-governance-check.yml)
- [Observer Guardrails Spec](../specs/observer_guardrails.yaml)
- [Render Integration](../specs/render_integration.md)
- [Slack Integration](../specs/slack_integration.md)
- [MCP Architecture](../specs/mcp-architecture.md)
- [QA Integration Diagram](./QA_CHECKER_INTEGRATION_DIAGRAM.md)

---

**Last Updated:** October 9, 2025  
**Maintainer:** Platform Team  
**Status:** ✅ Active  
**Version:** 2.0 (Slack Escalation + Smart Diff + Drift History)

