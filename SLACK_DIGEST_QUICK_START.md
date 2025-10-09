# 🚀 Slack Daily Digest — 5-Minute Quick Start

> Get CI insights in Slack in 5 minutes or less

## ⚡ Prerequisites

- Slack workspace admin access (to create webhook)
- GitHub repository with some workflow runs
- 5 minutes ⏱️

## 📋 Quick Setup (3 Steps)

### Step 1: Create Slack Webhook (2 min)

1. Go to https://api.slack.com/messaging/webhooks
2. Click **Create your Slack app** → **From scratch**
3. App name: `CI Digest Bot` → Choose your workspace → **Create App**
4. Click **Incoming Webhooks** → Toggle **Activate Incoming Webhooks** ON
5. Click **Add New Webhook to Workspace** → Choose channel (e.g., `#ci-alerts`) → **Allow**
6. **Copy the Webhook URL** (looks like `https://hooks.slack.com/services/T00/B00/XX`)

### Step 2: Add Secret to GitHub (1 min)

1. Go to your repo: `https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions`
2. Click **New repository secret**
3. Name: `SLACK_WEBHOOK_URL`
4. Value: Paste the webhook URL from Step 1
5. Click **Add secret**

### Step 3: Test It (2 min)

1. Go to **Actions** tab → **📬 Slack Daily Digest** workflow
2. Click **Run workflow** → **Run workflow** button
3. Wait 10-30 seconds
4. **Check your Slack channel!** 📬

## ✅ Verification

You should see a message like:

```
📬 CI Daily Digest — Last 24 Hours

Total runs:      45        Pass rate:      91.1%
✅ Successes:    41        ❌ Failures:    4
Avg duration:    3.2 min

🏅 Quality Gates
Syntax ✅ · Lint 🧹 · Coverage 📊

📈 7-Day Pass-Rate Trend
spark: ▃▅▆▇▇▆▅

Mon: ✅✅✅✅❌  (87.5%)
Tue: ✅✅✅✅✅✅  (100.0%)
... (full week)

🐢 Top 3 Slowest Workflows (24h)
• CI Pro Dashboard — 8.3 min  (~35.2%)
• Full Test Suite — 6.1 min  (~25.8%)
• Deploy to Staging — 4.2 min  (~17.8%)

[🔎 View Actions]  [📊 View Dashboard]
```

## 🎯 What Happens Next?

- **Automatic daily digests** at **2 PM UTC** (6 AM PST / 9 AM EST)
- Summarizes last 24 hours + 7-day trends
- Zero maintenance required!

## 🛠️ Optional: Test Locally First

Before enabling in GitHub:

```bash
# Export your webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Send test message
python scripts/test_slack_webhook.py

# Expected output:
# OK: 200
```

Check Slack for test message ✅

## 📝 Files Created

| File | What It Does |
|------|--------------|
| `scripts/slack_daily_digest.py` | Fetches CI data & posts to Slack |
| `scripts/test_slack_webhook.py` | Local webhook test helper |
| `.github/workflows/slack_daily_digest.yml` | Runs digest daily at 2 PM UTC |

## 🔧 Common Adjustments

### Change Schedule Time

Edit `.github/workflows/slack_daily_digest.yml`:

```yaml
schedule:
  - cron: "0 9 * * *"  # 9 AM UTC instead of 2 PM
```

Use [crontab.guru](https://crontab.guru) to generate cron expressions.

### Change Slack Channel

1. Create a new webhook in Slack (Step 1 above) for different channel
2. Update `SLACK_WEBHOOK_URL` secret in GitHub

### Add GitHub Pages Badge Links

If your GitHub Pages URL is non-standard:

1. Go to repo **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable**
   - Name: `PAGES_BASE_URL`
   - Value: `https://your-custom-domain.com`
3. Badge links will automatically update

## ❓ Troubleshooting

| Issue | Fix |
|-------|-----|
| "SLACK_WEBHOOK_URL not set" | Add the secret in repo Settings → Secrets → Actions |
| No message in Slack | Check workflow logs in Actions tab; verify webhook URL is correct |
| Workflow fails | Ensure repo has had at least one workflow run in last 7 days |
| Badges show "pending" | Normal if GitHub Pages dashboard isn't set up yet |

## 📚 More Info

- **Full Documentation**: `SLACK_DAILY_DIGEST_README.md`
- **Implementation Details**: `SLACK_DIGEST_IMPLEMENTATION_COMPLETE.md`
- **Slack API Docs**: https://api.slack.com/messaging/webhooks
- **GitHub Actions API**: https://docs.github.com/rest/actions/workflow-runs

## 🎉 Done!

Your daily CI digest is now live! 🚀

**Next Steps:**
- Wait for the first automatic digest (2 PM UTC)
- Share with your team
- Customize the schedule if needed
- Enjoy automated CI insights! 📊

---

**Setup Time**: ⏱️ ~5 minutes  
**Ongoing Maintenance**: 🎊 Zero  
**Cost**: 💰 Free (uses GitHub + Slack free tiers)  
**Dependencies**: 📦 None (stdlib only)

Questions? Check the full README: `SLACK_DAILY_DIGEST_README.md`
