# 📬 Slack Daily Digest for GitHub Actions

> **Production-grade CI insights delivered to Slack daily with 7-day trends, quality badges, and performance metrics**

## 🎯 What This Does

Sends a **rich daily summary** to your Slack channel featuring:

- **24-hour CI Summary**: Total runs, pass rate, success/failure counts, average duration
- **7-Day Trend Analysis**: Sparkline visualization + emoji bars showing daily pass rates
- **Quality Gates**: Live badges for Syntax, Lint, and Coverage (from GitHub Pages)
- **Performance Insights**: Top 3 slowest workflows with runtime percentages
- **Interactive Actions**: Quick links to GitHub Actions and your CI Dashboard

## 📁 What Was Created

### 1. `scripts/slack_daily_digest.py`
Main digest script that:
- Fetches 7 days of GitHub Actions workflow runs via REST API
- Aggregates metrics for last 24 hours and 7-day trends
- Generates sparkline visualizations (`▁▂▃▄▅▆▇█`)
- Creates emoji bars per day (`✅✅❌` format)
- Identifies slowest workflows with performance impact
- Posts rich Slack Block Kit message

**Uses only stdlib** (no external dependencies):
- `urllib.request` for HTTP calls
- `datetime`, `statistics`, `collections` for data processing
- Zero pip dependencies!

### 2. `scripts/test_slack_webhook.py`
Local testing helper:
- Sends sample message to verify webhook configuration
- Accepts webhook URL via env var or CLI argument
- Quick validation before enabling in CI

### 3. `.github/workflows/slack_daily_digest.yml`
GitHub Actions workflow:
- **Schedule**: Daily at 2 PM UTC (`0 14 * * *`)
- **Manual trigger**: Supports `workflow_dispatch`
- **Graceful skipping**: Won't fail if webhook not configured
- **Minimal permissions**: Only `actions: read` and `contents: read`

## 🚀 Setup Instructions

### Step 1: Create Slack Incoming Webhook

1. Go to your Slack workspace's **Apps** → Search for **Incoming Webhooks**
2. Click **Add to Slack** → Choose your channel (e.g., `#ci-alerts`, `#engineering`)
3. Copy the webhook URL (format: `https://hooks.slack.com/services/XXX/YYY/ZZZ`)

### Step 2: Configure GitHub Secrets

1. Navigate to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**:
   - **Name**: `SLACK_WEBHOOK_URL`
   - **Value**: Paste your webhook URL from Step 1
   - Click **Add secret**

### Step 3: (Optional) Configure GitHub Pages URL

If your GitHub Pages URL differs from the default:

1. Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable**:
   - **Name**: `PAGES_BASE_URL`
   - **Value**: `https://your-org.github.io/your-repo`
   - Click **Add variable**

If not set, defaults to: `https://<owner>.github.io/<repo>`

### Step 4: Test Locally (Optional)

```bash
# Set your webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"

# Send test message
python scripts/test_slack_webhook.py

# Expected output:
# OK: 200
```

Check your Slack channel for the test message! ✅

### Step 5: Enable the Workflow

The workflow is already created at `.github/workflows/slack_daily_digest.yml`.

**Manual test run:**
1. Go to GitHub → **Actions** → **📬 Slack Daily Digest**
2. Click **Run workflow** → **Run workflow**
3. Wait ~10-30 seconds
4. Check your Slack channel for the digest!

**Automatic daily runs:**
- Will trigger daily at **2 PM UTC** (adjust cron in workflow file if needed)
- Time zones:
  - 2 PM UTC = 7 AM PST / 10 AM EST / 3 PM CET / 10 PM PHT

## 📊 Message Format

Your Slack digest will include:

### Header
```
📬 CI Daily Digest — Last 24 Hours
```

### Summary Section
```
Total runs:        45
Pass rate:         91.1%
✅ Successes:      41
❌ Failures:       4
Avg duration:      3.2 min
```

### Quality Gates
```
🏅 Quality Gates
Syntax ✅ · Lint 🧹 · Coverage 📊
```
*(Links to GitHub Pages badge JSON)*

### 7-Day Trend
```
📈 7-Day Pass-Rate Trend
spark: ▃▅▆▇▇▆▅

Mon: ✅✅✅✅❌  (87.5%)
Tue: ✅✅✅✅✅✅  (100.0%)
Wed: ✅✅✅✅✅  (92.3%)
Thu: ✅✅✅❌❌  (78.9%)
Fri: ✅✅✅✅✅  (95.2%)
Sat: ✅✅✅✅  (88.9%)
Sun: ✅✅✅✅✅  (90.0%)
```

### Performance Insights
```
🐢 Top 3 Slowest Workflows (24h)
• CI Pro Dashboard — 8.3 min  (~35.2%)
• Full Test Suite — 6.1 min  (~25.8%)
• Deploy to Staging — 4.2 min  (~17.8%)
```

### Action Buttons
- 🔎 **View Actions** → GitHub Actions page
- 📊 **View Dashboard** → GitHub Pages dashboard

### Footer
```
Repo: owner/repo-name  ·  Generated: 2025-10-05 14:00 UTC
```

## 🛠️ Customization

### Change Schedule Time

Edit `.github/workflows/slack_daily_digest.yml`:

```yaml
on:
  schedule:
    - cron: "0 9 * * *"  # 9 AM UTC instead of 2 PM
```

Use [crontab.guru](https://crontab.guru/) to generate cron expressions.

### Change Message Title

Edit `scripts/slack_daily_digest.py` line 230:

```python
{"type": "header", "text": {"type": "plain_text", "text": "🚀 Your Custom Title", "emoji": True}},
```

### Add More Metrics

The `aggregate_runs()` function (line 126) processes all workflow data. You can extend it to add:
- Week-over-week pass rate delta
- Most improved workflow
- Flaky test detection
- Cost analysis (workflow minutes)

### Change Badge Links

Edit line 220 in `slack_blocks()` function:

```python
badges_md = [
    f"[Custom Badge]({PAGES_BASE_URL}/path/to/badge.json)",
    # ... add more
]
```

## 🔍 Troubleshooting

### "SLACK_WEBHOOK_URL not set" Message

**Issue**: Workflow runs but skips posting to Slack

**Solution**: 
1. Verify secret is named **exactly** `SLACK_WEBHOOK_URL` (case-sensitive)
2. Check repo → Settings → Secrets → Actions → Look for your secret
3. If missing, add it following Step 2 above

### "ERROR: GITHUB_REPOSITORY not set"

**Issue**: Script can't determine repository

**Solution**: This should auto-populate in GitHub Actions. If testing locally:
```bash
export GITHUB_REPOSITORY="owner/repo-name"
export GITHUB_TOKEN="ghp_yourPersonalAccessToken"
python scripts/slack_daily_digest.py
```

### "HTTPError 404: Not Found" from GitHub API

**Issue**: Can't fetch workflow runs

**Solution**:
1. Verify `GITHUB_TOKEN` has `actions: read` permission
2. Check repository name is correct
3. Ensure workflows have run in the last 7 days

### Badges Show "pending GitHub Pages"

**Issue**: Badge links point to non-existent JSON files

**Solution**:
1. Your CI Dashboard must publish badge JSON to GitHub Pages
2. Files should exist at:
   - `ci-dashboard/syntax-guard.json`
   - `ci-dashboard/lint.json`
   - `ci-dashboard/coverage.json`
3. Verify GitHub Pages is enabled: Repo → Settings → Pages

### No Workflows in "Slowest" Section

**Issue**: Shows "_No data in last 24h_"

**Possible causes**:
- No workflow runs in the last 24 hours
- All runs are still in "pending" status
- Workflow run timestamps are malformed

**Solution**: Wait for workflows to complete, or trigger some manually

## 📈 Advanced Features

### Local Development Testing

```bash
# Set required env vars
export GITHUB_REPOSITORY="owner/repo"
export GITHUB_TOKEN="ghp_yourPAT"  # Create at github.com/settings/tokens
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/YYY/ZZZ"
export PAGES_BASE_URL="https://owner.github.io/repo"

# Run the script
python scripts/slack_daily_digest.py

# Expected output:
# Slack response: 200
```

### Integrate with Other Tools

The script can be adapted to:
- Post to Microsoft Teams (change webhook format)
- Send to Discord (adjust Block Kit to Discord embeds)
- Write to a database (replace Slack call with DB insert)
- Generate HTML reports (swap `slack_blocks()` for HTML template)

### Multiple Slack Channels

To post different summaries to different channels:

1. Create multiple webhook URLs (one per channel)
2. Duplicate the workflow with different names
3. Use different secret names (`SLACK_WEBHOOK_DEV`, `SLACK_WEBHOOK_PROD`)
4. Pass different env vars to each workflow run

## 📝 Example Output Scenarios

### Healthy CI Day
```
✅ 95.0% pass rate
   48 runs, 46 successes, 2 failures
   Sparkline: ▇▇▇█▇▇▇
```

### Degraded Performance
```
⚠️ 72.4% pass rate  (↓ 18.2% from last week)
   58 runs, 42 successes, 16 failures
   Sparkline: ▆▅▄▃▃▂▁
```

### Perfect Week
```
🎉 100.0% pass rate
   35 runs, 35 successes, 0 failures
   Sparkline: ████████
```

## 🎨 Message Appearance

The digest uses **Slack Block Kit** for rich formatting:
- **Headers**: Large, bold section titles
- **Fields**: Two-column layout for metrics
- **Dividers**: Visual separation between sections
- **Markdown**: Bold labels, inline code, links
- **Buttons**: Interactive action buttons
- **Context**: Subtle footer with metadata

Preview your message format at: [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)

## 🔐 Security Notes

- **Webhook URL**: Treat like a password—never commit to git
- **GitHub Token**: Auto-provided in Actions with minimal permissions
- **API Rate Limits**: Script fetches max 1000 workflow runs (should be plenty for 7 days)
- **Timeout Handling**: 30s timeout for GitHub API, 20s for Slack webhook

## ✅ Verification Checklist

After setup, verify:

- [ ] Test webhook works locally (`test_slack_webhook.py`)
- [ ] Secret `SLACK_WEBHOOK_URL` configured in GitHub
- [ ] Workflow appears in Actions tab
- [ ] Manual workflow run succeeds
- [ ] Message appears in correct Slack channel
- [ ] Badges link to correct GitHub Pages URLs (if applicable)
- [ ] "View Actions" button links to your Actions page
- [ ] "View Dashboard" button links to your Pages site
- [ ] Schedule is set for desired time (2 PM UTC default)

## 🎯 Next Steps

1. **Configure Slack webhook** (Step 1-2 above)
2. **Test manually**: Run workflow from Actions tab
3. **Validate message**: Check Slack channel
4. **Adjust schedule**: Edit cron if needed
5. **Add to docs**: Link from your main README

## 📚 Related Documentation

- [GitHub Actions Workflow Runs API](https://docs.github.com/en/rest/actions/workflow-runs)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit](https://api.slack.com/block-kit)
- [GitHub Pages](https://docs.github.com/en/pages)

## 🐛 Issues or Improvements?

If you encounter issues or want to enhance the digest:
1. Check the workflow run logs in GitHub Actions
2. Test locally with debug print statements
3. Verify all env vars are set correctly
4. Review Slack webhook response for errors

---

**Status**: ✅ Ready to use  
**Dependencies**: None (stdlib only)  
**CI Integration**: Automated via GitHub Actions  
**Maintenance**: Zero (self-contained script)

🚀 **Enjoy your daily CI insights in Slack!**
