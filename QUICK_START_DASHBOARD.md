# 🚀 Release Dashboard - Quick Start Guide

**Get started in 2 minutes!**

---

## 1️⃣ Setup (First Time Only)

```bash
# Install dependencies
pip install -r requirements.txt

# Set GitHub token
export GH_TOKEN="ghp_your_github_personal_access_token"

# (Optional) Set Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Get your GitHub token:**
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scope: `repo`
4. Copy and export it

---

## 2️⃣ Basic Usage

### Preview Changes (Safe)
```bash
python scripts/update_release_dashboard.py --dry-run
```

### Update Dashboard (No Commit)
```bash
python scripts/update_release_dashboard.py --verbose
```

### Full Automation (Commit + Notify)
```bash
python scripts/update_release_dashboard.py --commit --notify --verbose
```

### Check Readiness Gate (CI Mode)
```bash
python scripts/update_release_dashboard.py --check-only
# Exits with 1 if readiness < 90%
```

---

## 3️⃣ What It Does

1. **Fetches** latest 10 GitHub Actions workflow runs
2. **Calculates** release readiness score (weighted formula)
3. **Updates** `v0.7.0-release-checklist.md` (between comment markers)
4. **Caches** results to `.cache/readiness.json` for trending
5. **Notifies** Slack if readiness < 90% (optional)
6. **Commits** changes to git (optional)

---

## 4️⃣ CLI Flags Cheat Sheet

```bash
--commit              # Auto-commit and push
--branch main         # Target branch
--notify              # Send Slack alert if < 90%
--verbose             # Show detailed logs
--dry-run             # Preview only (no changes)
--check-only          # Exit 1 if < 90% (for CI)
--no-cache            # Skip JSON caching
```

---

## 5️⃣ GitHub Actions (Automatic)

The system runs automatically:
- ✅ Daily at 09:00 UTC
- ✅ On push to main/develop
- ✅ Manual trigger via GitHub UI

**Manual Trigger:**
1. Go to: Actions → Update Release Dashboard
2. Click "Run workflow"
3. Select branch and options
4. Click "Run workflow"

---

## 6️⃣ Troubleshooting

### Error: "Could not import release_dashboard modules"
```bash
# Must run from repo root
cd /path/to/MAGSASA-CARD-ERP
python scripts/update_release_dashboard.py --dry-run
```

### Error: "Invalid GitHub token"
```bash
# Verify token
echo $GH_TOKEN

# Test it
curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user
```

### Slack notifications not working
```bash
# Check webhook
echo $SLACK_WEBHOOK_URL

# Test it
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test"}' \
  $SLACK_WEBHOOK_URL
```

---

## 7️⃣ Understanding the Score

**Readiness Formula:**
```
Total = Core Gates (50%) + Optional (20%) + Deployment (20%) + Sign-off (10%)
```

**Score Thresholds:**
- **95-100%** 🟢 Release Ready - Ship it!
- **90-94%** 🟢 Nearly Ready - Final checks
- **85-89%** 🟡 Minor Blockers - On track
- **70-84%** 🟠 In Progress - Several blockers
- **< 70%** 🔴 Not Ready - Major blockers

---

## 8️⃣ File Locations

```
scripts/
├── update_release_dashboard.py    # Main CLI
├── release_dashboard/              # Modules
│   ├── fetch.py                    # GitHub API
│   ├── update.py                   # Markdown updater
│   ├── notify.py                   # Slack alerts
│   ├── scoring.py                  # Score calculator
│   └── cache.py                    # JSON caching
└── README_RELEASE_UPDATER.md       # Full documentation

.github/workflows/
└── update-readiness.yml            # Automation workflow

.cache/
└── readiness.json                  # Historical data

v0.7.0-release-checklist.md         # Target file
```

---

## 9️⃣ Example Output

```
🚀 Release Dashboard Updater v1.0.0
   Production-grade automation for release readiness tracking

ℹ️  Fetching GitHub Actions workflow runs...
✅ Retrieved 10 workflow runs
ℹ️  Analyzing CI health...
✅ CI Health: HEALTHY (Success rate: 95.2%)
ℹ️  Calculating release readiness score...
✅ Readiness score: 87.5%

📊 Release Readiness Score
┌────────────────────┬──────────┬─────────┬────────┐
│ Category           │    Score │ Passing │ Weight │
├────────────────────┼──────────┼─────────┼────────┤
│ Core Gates         │    87.5% │    7/8  │    50% │
│ Optional Gates     │    87.5% │    7/8  │    20% │
│ Deployment         │    75.0% │    6/8  │    20% │
│ Sign-off           │    78.6% │   11/14 │    10% │
│ TOTAL              │    87.5% │         │   100% │
└────────────────────┴──────────┴─────────┴────────┘

┌─────────────────────────────────────────┐
│ Status                                  │
│ 🟡 Nearly Ready - Minor blockers remain │
└─────────────────────────────────────────┘

✅ Update Complete
```

---

## 🔟 Need More Help?

**Full Documentation:** `scripts/README_RELEASE_UPDATER.md`  
**Completion Report:** `RELEASE_DASHBOARD_AUTOMATION_COMPLETE.md`  
**GitHub Workflow:** `.github/workflows/update-readiness.yml`  
**Maintainer:** @gerome650  

---

**That's it! You're ready to go! 🎉**

