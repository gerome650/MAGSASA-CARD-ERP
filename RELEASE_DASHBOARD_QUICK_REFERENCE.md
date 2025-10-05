# 🚀 Release Dashboard - Quick Reference Card

**One-page cheat sheet for everyday use**

---

## ⚡ Quick Commands

```bash
# Preview changes (safe)
python scripts/update_release_dashboard.py --dry-run

# Update dashboard
python scripts/update_release_dashboard.py --verbose

# Full automation (commit + notify + PR comment)
python scripts/update_release_dashboard.py --commit --notify --pr-comment --verbose

# CI gate (fail if < 90%)
python scripts/update_release_dashboard.py --check-only

# Post PR comment only
python scripts/update_release_dashboard.py --pr-comment
```

---

## 🎯 CLI Flags

| Flag | Purpose | Example |
|------|---------|---------|
| `--dry-run` | Preview without changes | Safe testing |
| `--check-only` | Exit 1 if < 90% | CI gating |
| `--commit` | Auto-commit to git | Automation |
| `--notify` | Send Slack alert | Team awareness |
| `--pr-comment` | Post PR comment | PR visibility |
| `--strict` | Fail if notify/comment fails | Compliance |
| `--verbose` | Show detailed logs | Debugging |
| `--no-cache` | Skip JSON caching | Testing |
| `--branch <name>` | Target branch | Custom branch |

---

## 🔑 Environment Variables

```bash
# Required
export GH_TOKEN="ghp_your_github_personal_access_token"

# Optional
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK"
```

---

## 📊 Score Thresholds

| Score | Status | Color | Action |
|-------|--------|-------|--------|
| ≥ 95% | 🟢 Ready | Green | Ship it! |
| 90-94% | 🟡 Nearly Ready | Yellow | Final checks |
| 85-89% | 🟡 Minor Blockers | Yellow | On track |
| 70-84% | 🟠 In Progress | Orange | Several blockers |
| < 70% | 🔴 Not Ready | Red | Major blockers |

---

## 🏗️ File Structure

```
scripts/
├── update_release_dashboard.py   # Main CLI
└── release_dashboard/             # Modules
    ├── fetch.py                   # GitHub API
    ├── update.py                  # Markdown updater
    ├── notify.py                  # Slack alerts
    ├── scoring.py                 # Score calculator
    ├── cache.py                   # JSON caching
    └── pr_commenter.py            # PR comments

.github/workflows/
└── update-readiness.yml           # Automation

v0.7.0-release-checklist.md        # Target file
```

---

## 🎨 Scoring Formula

```
Total = Core Gates (50%) 
      + Optional Gates (20%) 
      + Deployment (20%) 
      + Sign-off (10%)
```

**Example:**
- Core: 7/8 = 87.5% × 0.50 = 43.75%
- Optional: 7/8 = 87.5% × 0.20 = 17.50%
- Deployment: 6/8 = 75% × 0.20 = 15.00%
- Sign-off: 11/14 = 78.6% × 0.10 = 7.86%

**Total: 84.11%**

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Could not import modules" | Run from repo root: `cd /path/to/MAGSASA-CARD-ERP` |
| "Invalid GitHub token" | Check: `echo $GH_TOKEN` and verify at github.com/settings/tokens |
| "No workflow runs found" | Verify workflows exist: `ls .github/workflows/` |
| Slack not working | Test webhook: `curl -X POST --data '{"text":"test"}' $SLACK_WEBHOOK_URL` |
| PR comment not posting | Check `GITHUB_REF` env var in CI |

---

## 📚 Documentation Links

- **Quick Start:** `QUICK_START_DASHBOARD.md`
- **Full Guide:** `scripts/README_RELEASE_UPDATER.md`
- **PR Commenter:** `PR_AUTO_COMMENTER_IMPLEMENTATION_COMPLETE.md`
- **Architecture:** `RELEASE_DASHBOARD_AUTOMATION_COMPLETE.md`
- **Verification:** `IMPLEMENTATION_VERIFICATION_SUMMARY.md`

---

## 🤖 GitHub Actions Triggers

- ✅ Push to `main` or `develop`
- ✅ Daily at 09:00 UTC
- ✅ Pull request opened/updated
- ✅ Manual dispatch

**Manual Trigger:**
Actions → Update Release Dashboard → Run workflow

---

## 💡 Common Workflows

### Developer: Preview Before Committing
```bash
python scripts/update_release_dashboard.py --dry-run --verbose
```

### CI: Gate Release
```bash
python scripts/update_release_dashboard.py --check-only
# Exits 1 if < 90%, blocking merge
```

### Team Lead: Full Update
```bash
python scripts/update_release_dashboard.py \
  --commit \
  --notify \
  --pr-comment \
  --verbose
```

### PR Review: Check Status
Just open the PR - comment appears automatically! 🎉

---

## 🎯 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Failure (readiness < 90% in check-only, or error) |
| `130` | User cancelled (Ctrl+C) |

---

## 📞 Quick Help

```bash
# Get help
python scripts/update_release_dashboard.py --help

# Check version
python scripts/update_release_dashboard.py --version

# Verbose mode for debugging
python scripts/update_release_dashboard.py --verbose --dry-run
```

---

## ⚠️ Important Notes

1. **Always run from repository root**
2. **GH_TOKEN must have `repo` scope**
3. **PR comments need `pull-requests: write` permission**
4. **Comment markers are sacred - don't delete them!**
5. **Use `--dry-run` first if unsure**

---

## 🎨 Badge Examples

![Ready](https://img.shields.io/badge/Readiness-95%25-green.svg?style=for-the-badge)  
![Nearly Ready](https://img.shields.io/badge/Readiness-92%25-yellow.svg?style=for-the-badge)  
![Risky](https://img.shields.io/badge/Readiness-85%25-orange.svg?style=for-the-badge)  
![Blocked](https://img.shields.io/badge/Readiness-75%25-red.svg?style=for-the-badge)

---

## 🚀 Pro Tips

1. **Bookmark this file** for quick access
2. **Add alias** to your shell: `alias release-dashboard="python scripts/update_release_dashboard.py"`
3. **Use `--verbose`** when debugging
4. **Check `.cache/readiness.json`** for historical data
5. **Run `--dry-run` first** in production environments

---

**Need more details? Check the full documentation!**

📖 [`scripts/README_RELEASE_UPDATER.md`](./scripts/README_RELEASE_UPDATER.md)

---

*Last Updated: October 5, 2025*  
*Quick Reference v1.0.0*

