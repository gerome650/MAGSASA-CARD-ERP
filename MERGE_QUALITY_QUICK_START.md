# ⚡ Merge Quality System - Quick Start Guide

> Get up and running in 5 minutes

---

## 🚀 Installation (1 minute)

```bash
# Clone and setup
cd MAGSASA-CARD-ERP
make setup

# Verify installation
make validate-all
```

✅ **Expected:** All validations pass

---

## 🎯 First Run (2 minutes)

### Test the System

```bash
# 1. Calculate a merge score
python scripts/update_merge_scores.py \
  --team-goal 90.0 \
  --branch test-branch \
  --commit test123 \
  --actor testuser

# 2. Build Slack message
python scripts/slack_merge_digest.py \
  --payload merge_slack_payload.json \
  --repo test/repo \
  --branch test-branch \
  --commit test123 \
  --actor testuser \
  --output slack_test.json

# 3. Validate Slack message
python scripts/validate_slack_payload.py slack_test.json
```

✅ **Expected:** "Payload is valid!"

---

## 🧪 Run Tests (1 minute)

```bash
# Run all tests
pytest tests/test_merge_score_calculation.py tests/test_validate_payload_structure.py -v
```

✅ **Expected:** 43/43 tests pass

---

## 🔗 Configure Slack (1 minute)

### Option 1: Environment Variable
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Option 2: GitHub Secret
```
1. Go to: Repository Settings → Secrets → New secret
2. Name: SLACK_WEBHOOK_URL
3. Value: Your webhook URL
4. Save
```

---

## 📊 Check Current State

```bash
# View merge quality history
cat merge_quality_state.json | jq .

# View last 3 PR scores
cat merge_quality_state.json | jq '.history[-3:] | .[] | {score, branch: .pr_metadata.branch}'

# View current streak
cat merge_quality_state.json | jq '.streak_below_goal'
```

---

## 🎨 Example Commands

### Calculate Merge Score
```bash
python scripts/update_merge_scores.py \
  --pytest-json pytest-report.json \
  --coverage-xml coverage.xml \
  --ruff-json lint-report.json \
  --team-goal 90.0 \
  --branch feature/my-feature \
  --commit $(git rev-parse HEAD) \
  --actor $(git config user.name)
```

### Build and Send Slack Message
```bash
python scripts/slack_merge_digest.py \
  --payload merge_slack_payload.json \
  --repo your-org/your-repo \
  --branch $(git branch --show-current) \
  --commit $(git rev-parse HEAD) \
  --actor $(git config user.name) \
  --webhook-url "$SLACK_WEBHOOK_URL" \
  --send
```

### Validate Payload
```bash
python scripts/validate_slack_payload.py slack_message.json --suggest-fixes
```

### Schema Diff Report
```bash
python scripts/schema_diff_reporter.py slack_message.json --schema slack_payload_schema.json
```

---

## 🛠️ Makefile Shortcuts

```bash
make validate-payload   # Validate Slack payload
make validate-all       # Complete validation suite
make fix-all           # Auto-fix code issues
make ci                # Full CI pipeline
make validate-schema   # Detailed schema validation
```

---

## 📈 Understanding the Output

### Merge Score Calculation
```
Merge Score: 92.0%          ← Total weighted score
Team Goal: 90.0%            ← Your configured goal
Streak Below Goal: 0        ← Consecutive failures
Slack payload saved to: merge_slack_payload.json
```

### Status Indicators

| Score | Status | Emoji | Action |
|-------|--------|-------|--------|
| ≥90% | ✅ **ON TRACK** | Green | Continue! |
| 80-89% | 🟠 **BELOW GOAL** | Yellow | Improve |
| 2 strikes | ⚠️ **EARLY WARNING** | Orange | Fix now! |
| 3+ strikes | 🔥 **AUTO-FAIL** | Red | Merge blocked |

---

## 🔍 Troubleshooting

### Payload Validation Fails
```bash
# Regenerate payload
make fix-all

# Check structure
cat merge_slack_payload.json | jq .
```

### Tests Fail
```bash
# Run with verbose output
pytest tests/ -vv --tb=short

# Run specific test
pytest tests/test_merge_score_calculation.py::TestMergeScoreCalculator::test_calculate_score_perfect -v
```

### Slack Not Sending
```bash
# Test webhook manually
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Test"}' \
  "$SLACK_WEBHOOK_URL"

# Check CI logs
# Look for "Send Slack Notification" step
```

---

## 📚 Documentation

- 📖 **Full Documentation:** [`MERGE_QUALITY_SYSTEM_README.md`](MERGE_QUALITY_SYSTEM_README.md)
- ✅ **Checklist:** [`MERGE_QUALITY_CHECKLIST.md`](MERGE_QUALITY_CHECKLIST.md)
- 🎯 **Implementation Summary:** [`MERGE_QUALITY_IMPLEMENTATION_SUMMARY.md`](MERGE_QUALITY_IMPLEMENTATION_SUMMARY.md)

---

## 🎯 Next Steps

1. ✅ Install and verify
2. ✅ Configure Slack webhook
3. ✅ Push first PR
4. ✅ Monitor results
5. ✅ Adjust team goal if needed

---

## 🆘 Get Help

- 📧 Open an issue
- 📚 Read full documentation
- 🧪 Run tests for diagnostics

---

**Ready to Go!** 🚀

Your Merge Quality Early-Warning System is now operational!

