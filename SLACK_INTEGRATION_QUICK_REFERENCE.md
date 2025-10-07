# 📣 Slack Integration - Quick Reference Card

## 🎯 One-Minute Setup

### 1️⃣ Add GitHub Secret
```bash
# In your repo: Settings → Secrets → Actions → New secret
Name:  SLACK_WEBHOOK_URL
Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2️⃣ Test It
```bash
# Create a failing PR to trigger notification
# OR test locally:
export SLACK_WEBHOOK_URL="your-webhook-url"
python3 test_slack_webhook.py --rich
```

### 3️⃣ Done! ✅
Every PR failure will now post to Slack automatically.

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                  │
│                  (.github/workflows/merge-gate.yml)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌────────────────────────────────────────┐
        │   PR Event Triggers on main/release/*  │
        └────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────────┐
        │  Jobs Run: coverage → quality → security        │
        │              → merge-decision                    │
        └─────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        ┌─────────────┐          ┌─────────────┐
        │  ✅ Success  │          │  ❌ Failure  │
        │  (optional)  │          │  (always)   │
        └─────────────┘          └─────────────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
                ┌──────────────────────────┐
                │ slack-notifications job  │
                │ • Checkout repo          │
                │ • Setup Python           │
                │ • Install requests       │
                │ • Run script --rich      │
                └──────────────────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │  📬 Slack Channel     │
                  │  Notification Posted  │
                  └──────────────────────┘
```

---

## 🚨 When Notifications Fire

### Failure Notifications (Automatic) ❌
Triggers when ANY of these fail:
- 📊 Coverage < 85%
- 🧹 Linting/formatting issues
- 🛡️ Security vulnerabilities
- ⚠️ Any job failure

### Success Notifications (Opt-In) ✅
Only if `SLACK_SUCCESS_NOTIFICATIONS=true` secret is set:
- ✅ All checks passed
- 📈 Coverage ≥ 85%
- 🎉 Ready to merge

---

## 📋 GitHub Secrets Reference

| Secret Name | Required | Purpose | Example |
|-------------|----------|---------|---------|
| `SLACK_WEBHOOK_URL` | ✅ Yes | Slack webhook endpoint | `https://hooks.slack.com/services/XXX/XXX/XXX` |
| `SLACK_SUCCESS_NOTIFICATIONS` | ⚪ Optional | Enable success alerts | `true` or unset (default: disabled) |

---

## 🎨 Notification Preview

### Failure Message (--rich)
```
╔══════════════════════════════════════════════╗
║      🚀 CI Notification Test                 ║
╠══════════════════════════════════════════════╣
║ Status: ✅ Success   │ Environment: Production║
║ Coverage: 92.3% 📊  │ Build Time: 3m 42s ⏱️  ║
╟──────────────────────────────────────────────╢
║ Build Details:                               ║
║ • All tests passed ✓                         ║
║ • Code quality checks passed ✓               ║
║ • Security scan completed ✓                  ║
║ • Deployment ready 🚀                        ║
╟──────────────────────────────────────────────╢
║ 📦 Repository: MAGSASA-CARD-ERP              ║
║ 🌿 Branch: main                              ║
║ 👤 Author: Test User                         ║
╟──────────────────────────────────────────────╢
║ [ View Pull Request 🔗 ] [ View Build Logs ] ║
╚══════════════════════════════════════════════╝
```

---

## 🛠️ Command Reference

### Local Testing
```bash
# Test basic connectivity
python3 test_slack_webhook.py --basic

# Test rich CI-style notification (same as workflow)
python3 test_slack_webhook.py --rich

# Test error handling
python3 test_slack_webhook.py --error
```

### Script Modes
| Mode | Description | Use Case |
|------|-------------|----------|
| `--basic` | Simple text message | Quick connectivity test |
| `--rich` | Full Block Kit message | Production CI notifications |
| `--error` | Invalid payload | Error handling test |

---

## 🐛 Troubleshooting

### ❌ No notifications received?

**Check 1: Secret configured?**
```bash
gh secret list | grep SLACK_WEBHOOK_URL
```

**Check 2: Workflow logs**
```
Actions → Latest workflow run → slack-notifications job
```

**Check 3: Test webhook**
```bash
export SLACK_WEBHOOK_URL="your-url"
python3 test_slack_webhook.py --basic
```

**Check 4: Webhook valid?**
- Regenerate at: https://api.slack.com/messaging/webhooks

### ⚠️ Common Errors

| Error | Fix |
|-------|-----|
| `SLACK_WEBHOOK_URL not configured` | Add secret in GitHub Settings |
| `invalid_blocks` | Update Slack app permissions |
| `404 Not Found` | Webhook deleted, generate new one |
| `429 Too Many Requests` | Rate limited, wait and retry |

---

## 📈 Advanced Usage

### Dynamic Content (Future Enhancement)
```bash
# Pass CI data to script
python3 test_slack_webhook.py --rich \
  --pr-number="123" \
  --pr-title="Fix bug" \
  --coverage="87.5"
```

### Conditional Payload Types
```bash
# Use different payloads based on coverage
if [ "$COVERAGE" -lt 80 ]; then
  python3 test_slack_webhook.py --error  # Critical
else
  python3 test_slack_webhook.py --rich   # Normal
fi
```

---

## 📊 Workflow Job Structure

```yaml
slack-notifications:
  name: 📣 Slack Notifications
  runs-on: ubuntu-latest
  needs: [coverage-enforcement, quality-checks, security-scan, merge-decision]
  if: always() && github.event_name == 'pull_request'
  
  steps:
    - Checkout repo
    - Setup Python 3.11
    - Install requests
    - Send notification (if failure/success conditions met)
```

**Key Points:**
- ✅ Runs **after** all other jobs (`needs:`)
- ✅ Runs **even if jobs fail** (`if: always()`)
- ✅ Only on **PR events** (`pull_request`)
- ✅ Times out after **5 minutes**
- ✅ Uses Python **3.11**

---

## 🎯 Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `.github/workflows/merge-gate.yml` | Integrated `test_slack_webhook.py` | 368-448 |

---

## ✅ Status Indicators

| Symbol | Meaning |
|--------|---------|
| ✅ | Feature active and working |
| ⚠️ | Warning or optional feature |
| ❌ | Error or failure state |
| 📊 | Coverage-related |
| 🔔 | Notification-related |
| 🚀 | Deployment/CI-related |

---

## 🚀 Quick Commands Cheat Sheet

```bash
# Setup
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX"

# Test notification
python3 test_slack_webhook.py --rich

# Check webhook response
python3 test_slack_webhook.py --rich | grep "HTTP Status"

# Trigger real notification (create failing PR)
git checkout -b test-slack-notifications
# Make a change that fails coverage
git push origin test-slack-notifications
# Open PR → Watch Slack channel

# View GitHub secrets
gh secret list

# Add secret via CLI
gh secret set SLACK_WEBHOOK_URL

# Enable success notifications
gh secret set SLACK_SUCCESS_NOTIFICATIONS --body "true"
```

---

## 📞 Support Resources

- **Slack API Docs:** https://api.slack.com/messaging/webhooks
- **Block Kit Builder:** https://app.slack.com/block-kit-builder
- **GitHub Actions:** https://docs.github.com/en/actions
- **Script Location:** `test_slack_webhook.py` (root directory)
- **Workflow File:** `.github/workflows/merge-gate.yml`

---

## 🎉 You're All Set!

Your Slack notifications are now **live and active**. Every PR failure will trigger an automatic notification with:

✅ Professional Block Kit formatting  
✅ Rich metadata (PR info, coverage, author)  
✅ Action buttons (View PR, View Logs)  
✅ Graceful error handling  
✅ Zero manual intervention required  

**Next:** Test it by creating a PR that fails coverage! 🚀

---

*Last Updated: October 6, 2025*  
*Integration Version: 1.0*  
*Script: test_slack_webhook.py*


