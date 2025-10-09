# 🚨 QA Slack Escalation - Quick Start Guide

## Overview

The QA Observability & Governance Consistency Checker now includes **automatic Slack escalation** when failures are detected. This transforms your governance system from reactive to proactive.

## 🎯 What's New

### 1. **Slack Alerts on Failure** 🔔
- Automatic alerts sent to Slack when QA checks fail
- Includes PR number, error count, and top mismatches
- Direct link to failing PR for immediate action

### 2. **Smart Diff Table** 📊
- Structured table showing expected vs actual values
- Source file identification for quick fixes
- Appears in PR comments and QA summary

### 3. **Drift History Tracking** 💾
- Machine-readable JSON artifacts saved for every run
- 90-day retention for trend analysis
- Foundation for future drift dashboard

## ⚡ Quick Setup

### Step 1: Configure Slack Webhook

1. **Get Webhook URL:**
   ```bash
   # Go to: https://api.slack.com/apps
   # Create or select app → Incoming Webhooks
   # Add webhook to your desired channel
   # Copy webhook URL
   ```

2. **Add to GitHub Secrets:**
   ```
   Repository → Settings → Secrets and Variables → Actions
   New secret: SLACK_GOVERNANCE_WEBHOOK
   Value: https://hooks.slack.com/services/T00/B00/XXX
   ```

3. **Verify:**
   ```bash
   # Check secret is available in workflow
   # View PR Governance Check workflow runs
   # Look for: "SLACK_GOVERNANCE_WEBHOOK configured ✅"
   ```

### Step 2: Test Locally

```bash
# Set environment variables
export GITHUB_PR_NUMBER=123
export GITHUB_REPOSITORY="your-org/your-repo"

# Generate Slack payload
python3 scripts/qa/obs_governance_consistency.py --slack-payload

# Send test alert
export SLACK_WEBHOOK="your-webhook-url"
MESSAGE=$(python3 scripts/qa/obs_governance_consistency.py --slack-payload)

curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\": \"$MESSAGE\"}" \
  "$SLACK_WEBHOOK"
```

### Step 3: Verify in CI

1. Open a PR that modifies governance files
2. Intentionally introduce a threshold mismatch
3. Watch for Slack alert in your configured channel
4. Review diff table in PR comment

## 📋 Example Slack Alert

```
🚨 Governance QA Check Failed on PR #42
❌ 2 Errors | ⚠️ 1 Warning
• latency_warn expected 2500, found 4000
• drift_fail expected 5, found 7
• uptime_fail expected 98.0, found 95.0
🔗 https://github.com/your-org/your-repo/pull/42
```

## 🎨 Example Diff Table

| Metric | Expected | Found | Source File | Status |
|--------|----------|-------|-------------|--------|
| latency_warn | 2500 | 4000 | pr-governance-check.yml | ❌ |
| drift_fail | 5 | 7 | observer_guardrails.yaml | ❌ |

## 🔧 CLI Options

```bash
# Standard run (generates all outputs)
python3 scripts/qa/obs_governance_consistency.py

# Debug mode (detailed parsing info)
python3 scripts/qa/obs_governance_consistency.py --debug

# Slack payload only (for CI integration)
python3 scripts/qa/obs_governance_consistency.py --slack-payload
```

## 📦 Artifacts Generated

Every QA run generates:

1. **qa_summary.md** - Human-readable report
2. **qa_results.json** - Machine-readable artifact
3. **History Archive** - `scripts/qa/history/qa_results_{run_id}.json`

**Artifact Structure:**
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
  "files_checked": [...]
}
```

## 🎯 When Alerts Trigger

| Condition | Slack Alert | PR Comment | Blocks Merge |
|-----------|-------------|------------|--------------|
| ❌ Errors | ✅ YES | ✅ YES | ✅ YES |
| ⚠️ Warnings only | ❌ NO | ✅ YES | ❌ NO |
| ✅ All pass | ❌ NO | ✅ YES | ❌ NO |

**Key Point:** Only **errors** trigger Slack alerts. Warnings are informational.

## 🚀 Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PR Opened with Governance File Changes                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. QA Consistency Checker Runs                              │
│    - Validates YAML                                          │
│    - Checks thresholds                                       │
│    - Verifies secrets                                        │
│    - Generates artifacts                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
                ┌───────┴────────┐
                │                │
        ✅ Pass          ❌ Fail
                │                │
                ▼                ▼
    ┌───────────────┐  ┌──────────────────┐
    │ PR Comment    │  │ Slack Alert      │
    │ Artifacts     │  │ PR Comment       │
    │ Saved         │  │ Diff Table       │
    └───────────────┘  │ Artifacts Saved  │
                       │ Job Fails        │
                       └──────────────────┘
```

## 🛠️ Troubleshooting

### Slack Alert Not Sent

**Check 1: Secret configured?**
```bash
# In workflow logs, look for:
# "⚠️ SLACK_GOVERNANCE_WEBHOOK not configured"
```

**Fix:** Add secret to GitHub repository settings

**Check 2: Webhook URL valid?**
```bash
# Test webhook manually:
curl -X POST -H 'Content-type: application/json' \
  --data '{"text": "Test message"}' \
  "https://hooks.slack.com/services/YOUR/WEBHOOK"
```

**Fix:** Regenerate webhook in Slack app settings

**Check 3: Only errors present?**
- Warnings don't trigger Slack alerts
- Review `qa_results.json` to confirm errors_count > 0

### Diff Table Not Showing

**Check:** Look in sticky PR comment under "QA Consistency Report"
- Diff table only appears when threshold mismatches exist
- Review `qa_summary.md` artifact

### History Not Archiving

**Check:** Workflow step "Archive QA results for drift tracking"
```bash
# Should see: "✅ QA results archived: scripts/qa/history/qa_results_XXXXX.json"
```

**Fix:** Ensure `qa_results.json` is generated by checker

## 📚 Related Docs

- [Full QA Documentation](./QA_OBSERVABILITY_CONSISTENCY.md)
- [QA Integration Diagram](./QA_CHECKER_INTEGRATION_DIAGRAM.md)
- [PR Governance Workflow](../.github/workflows/pr-governance-check.yml)
- [Slack Integration Guide](../specs/slack_integration.md)

## 💡 Pro Tips

1. **Channel Selection:** Use a dedicated `#governance-alerts` channel
2. **Alert Volume:** Only errors trigger alerts, so signal-to-noise is high
3. **Quick Fixes:** Use diff table to identify exact file and line to fix
4. **Debug Mode:** Run locally with `--debug` to troubleshoot threshold detection
5. **Historical Analysis:** Save artifacts for quarterly compliance reviews

## 🎉 Benefits

| Before | After |
|--------|-------|
| Manual log review | Slack notification in 10s |
| "Check failed, why?" | Diff table shows exact mismatch |
| No history | 90-day artifact retention |
| Reactive | Proactive + alert-driven |
| Parse logs to find fix | Click PR link → review diff table → fix |

---

**Quick Start Checklist:**
- [ ] Add `SLACK_GOVERNANCE_WEBHOOK` secret
- [ ] Test Slack integration locally
- [ ] Open test PR with intentional mismatch
- [ ] Verify Slack alert received
- [ ] Review diff table in PR comment
- [ ] Check artifacts uploaded
- [ ] Fix mismatch and verify re-run

**Need Help?** See [Full Documentation](./QA_OBSERVABILITY_CONSISTENCY.md) or contact Platform Team.

---

**Last Updated:** October 9, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready


