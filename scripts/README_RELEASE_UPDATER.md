# 🚀 Release Dashboard Updater - Production-Grade Automation

**Version:** 1.0.0  
**Status:** Production-Ready ✅

## 📖 Overview

The **Release Dashboard Updater** is a production-grade automation system that keeps your `v0.7.0-release-checklist.md` file automatically updated with the latest GitHub Actions CI/CD results, readiness scores, and status indicators.

### ✨ Key Features

- **Modular Architecture**: Clean separation of concerns (fetch, update, notify, scoring)
- **Beautiful CLI**: Rich terminal output with colors, tables, and progress indicators
- **JSON Caching**: Track readiness trends over time with `.cache/readiness.json`
- **Smart Notifications**: Slack alerts with detailed failure analysis
- **CI Gating**: Fail builds if readiness falls below threshold (`--check-only`)
- **Dry-Run Mode**: Preview changes without modifying files
- **Auto-Commit**: Optionally commit and push updates automatically

---

## 🏗️ Architecture

The system is organized into modular components:

```
scripts/
├── update_release_dashboard.py  # Main CLI orchestrator
└── release_dashboard/
    ├── __init__.py               # Package initialization
    ├── fetch.py                  # GitHub Actions workflow fetcher
    ├── update.py                 # Markdown file updater
    ├── notify.py                 # Slack notification handler
    ├── scoring.py                # Release readiness calculator
    └── cache.py                  # JSON caching for analytics
```

### Component Responsibilities

| Module | Purpose |
|--------|---------|
| `fetch.py` | Fetches workflow runs from GitHub Actions API |
| `update.py` | Updates markdown sections between comment markers |
| `notify.py` | Sends Slack notifications with failure details |
| `scoring.py` | Calculates weighted readiness scores |
| `cache.py` | Stores historical data for trend analysis |

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **GitHub Personal Access Token** with `repo` scope
3. **(Optional)** Slack webhook URL for notifications

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Export GitHub token
export GH_TOKEN="ghp_your_github_personal_access_token"

# (Optional) Export Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Basic Usage

```bash
# Preview changes (dry-run)
python scripts/update_release_dashboard.py --dry-run

# Update dashboard (no commit)
python scripts/update_release_dashboard.py --verbose

# Full automation: update, commit, and notify
python scripts/update_release_dashboard.py --commit --notify --verbose

# Check readiness gate (CI mode)
python scripts/update_release_dashboard.py --check-only
```

---

## 📋 CLI Reference

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--commit` | Automatically commit and push changes | `false` |
| `--branch <name>` | Target branch for git operations | `main` |
| `--token <token>` | GitHub PAT (overrides `GH_TOKEN` env var) | - |
| `--repo <owner/repo>` | Repository name (auto-detected if not specified) | Auto-detect |
| `--notify` | Send Slack notification if readiness < 90% | `false` |
| `--verbose` / `-v` | Enable detailed logging | `false` |
| `--dry-run` | Preview changes without writing to disk | `false` |
| `--check-only` | Exit 1 if readiness < 90% (for CI gating) | `false` |
| `--no-cache` | Skip caching results to JSON | `false` |

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (readiness >= 90% in check-only mode) |
| `1` | Failure (readiness < 90% in check-only mode, or error occurred) |
| `130` | User cancelled operation (Ctrl+C) |

---

## 💡 Usage Examples

### Example 1: Preview Changes

```bash
python scripts/update_release_dashboard.py --dry-run
```

**Output:**
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

⚠️  DRY RUN MODE - No changes will be made
...
```

### Example 2: Automated Update with Commit

```bash
python scripts/update_release_dashboard.py --commit --notify --verbose
```

**What it does:**
1. Fetches latest CI runs from GitHub Actions
2. Calculates readiness score from checklist
3. Updates `v0.7.0-release-checklist.md`
4. Commits and pushes changes
5. Sends Slack notification if score < 90%

### Example 3: CI Readiness Gate

Use this in your CI pipeline to enforce readiness before releases:

```bash
# This will exit 1 if readiness score is below 90%
python scripts/update_release_dashboard.py --check-only
```

Add to your `.github/workflows/`:

```yaml
- name: Release Readiness Gate
  run: python scripts/update_release_dashboard.py --check-only
```

### Example 4: Manual Update with Custom Branch

```bash
python scripts/update_release_dashboard.py \
  --branch develop \
  --commit \
  --verbose
```

---

## 🎯 How It Works

### 1. **Fetch CI Data**

The `fetch.py` module uses PyGithub to retrieve:
- Last 10 workflow runs across all workflows
- Workflow status (success/failure/cancelled)
- Duration, branch, commit info
- Overall CI health metrics (success rate, failures)

### 2. **Calculate Readiness Score**

The `scoring.py` module parses your `v0.7.0-release-checklist.md` and calculates:

**Weighted Scoring Formula:**
```
Total Score = (Core Gates × 50%) + (Optional Gates × 20%) 
              + (Deployment × 20%) + (Sign-off × 10%)
```

**Example:**
- Core Gates: 7/8 = 87.5% → 87.5% × 0.50 = 43.75%
- Optional: 7/8 = 87.5% → 87.5% × 0.20 = 17.50%
- Deployment: 6/8 = 75.0% → 75.0% × 0.20 = 15.00%
- Sign-off: 11/14 = 78.6% → 78.6% × 0.10 = 7.86%

**Total: 84.11%**

### 3. **Update Markdown**

The `update.py` module replaces content between comment markers:

```markdown
<!-- CI_SNAPSHOT_START -->
...updated CI snapshot table...
<!-- CI_SNAPSHOT_END -->

<!-- READINESS_SCORE_START -->
...updated readiness score...
<!-- READINESS_SCORE_END -->
```

**Note:** Manual content outside these markers is preserved!

### 4. **Cache Results**

Historical data is stored in `.cache/readiness.json`:

```json
[
  {
    "timestamp": "2024-12-15T09:00:00",
    "score": 87.5,
    "status": "minor_blockers",
    "core_score": 87.5,
    "optional_score": 87.5,
    "deployment_score": 75.0,
    "signoff_score": 78.6,
    "blockers_count": 3
  }
]
```

### 5. **Send Notifications**

If `--notify` is enabled and score < 90%, the `notify.py` module sends a Slack message with:
- Current readiness score
- Top 3 failing workflows with links
- Current blockers
- Action buttons to view checklist and CI runs

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GH_TOKEN` | ✅ Yes | GitHub Personal Access Token with `repo` scope |
| `SLACK_WEBHOOK_URL` | ⚪ Optional | Slack incoming webhook URL for notifications |

### Setting Up GitHub Token

1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens
2. Generate new token (classic) with `repo` scope
3. Export it:
   ```bash
   export GH_TOKEN="ghp_your_token_here"
   ```

### Setting Up Slack Webhook

1. Go to your Slack workspace → Apps → Incoming Webhooks
2. Create a new webhook for your channel
3. Export it:
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

---

## 🤖 GitHub Actions Automation

The system includes a GitHub Actions workflow (`.github/workflows/update-readiness.yml`) that runs automatically.

### Triggers

1. **Push to `main` or `develop`**
2. **Daily schedule** at 09:00 UTC
3. **Manual dispatch** via GitHub UI

### Workflow Steps

```yaml
jobs:
  update-dashboard:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
      - name: Set up Python 3.11
      - name: Install dependencies
      - name: Update Release Dashboard  # Main update step
      - name: Readiness Gate Check       # Optional: fail if < 90%
      - name: Create Pull Request        # If on non-main branch
      - name: Comment on PR              # Add dashboard link to PRs
      - name: Notify on Failure          # Slack alert if workflow fails
```

### Manual Dispatch Parameters

When triggering manually from GitHub Actions UI:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `branch` | Target branch | `main` |
| `commit_changes` | Commit updates | `true` |
| `enforce_gate` | Fail if readiness < 90% | `false` |

---

## 📊 Readiness Score Details

### Scoring Categories

#### Core Gates (50% weight) - Must Pass ✅
These are critical for release:
- Build & Unit Tests
- MCP Validation
- Stage Readiness Check
- Preflight Validation
- **Security Audit** (PENDING)
- Database Migration Tests
- API Contract Tests
- Frontend Build & Lint

#### Optional Gates (20% weight) - Nice to Have 🟡
- Chaos Engineering Tests
- Observability Gate
- Documentation Gate
- PR Automation Tests
- Load Testing
- Rollback Procedure
- Mobile Responsive Tests
- Integration Tests

#### Deployment Automation (20% weight)
- Auto Semantic Release
- Production Deployment Workflow
- CHANGELOG Generation
- Docker Image Build & Push
- Kubernetes Manifests
- Secret Management
- Environment Configuration
- Release Metrics Dashboard

#### Final Sign-Off (10% weight)
- All core gates green
- Critical issues resolved
- Security vulnerabilities patched
- Preflight validation successful
- Release notes drafted
- Breaking changes documented
- Tagging validated on test branch
- Staging environment tested
- Rollback procedure validated
- On-call rotation confirmed
- Customer communication plan
- Performance benchmarks met
- Database backup verified
- Final CTO/QA/PO sign-off

### Score Thresholds

| Score Range | Status | Indicator | Meaning |
|-------------|--------|-----------|---------|
| **95-100%** | 🟢 Release Ready | Green | Ship it! |
| **90-94%** | 🟢 Nearly Ready | Green | Final checks needed |
| **85-89%** | 🟡 Minor Blockers | Yellow | On track, few items remain |
| **70-84%** | 🟠 In Progress | Orange | Several blockers |
| **< 70%** | 🔴 Not Ready | Red | Major blockers |

---

## 🛠️ Troubleshooting

### Issue: "Could not import release_dashboard modules"

**Solution:**
```bash
# Make sure you're running from the repository root
cd /path/to/MAGSASA-CARD-ERP/MAGSASA-CARD-ERP
python scripts/update_release_dashboard.py --dry-run
```

### Issue: "Invalid GitHub token"

**Solution:**
```bash
# Verify your token is valid
echo $GH_TOKEN

# Test GitHub API access
curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user

# Regenerate token if needed (with 'repo' scope)
```

### Issue: "No recent workflow runs found"

**Possible causes:**
- Repository doesn't have any workflows
- GitHub Actions haven't run yet
- Token doesn't have `actions:read` permission

**Solution:**
```bash
# Check workflows exist
ls -la .github/workflows/

# Run with verbose mode to see detailed errors
python scripts/update_release_dashboard.py --verbose
```

### Issue: Slack notifications not working

**Solution:**
```bash
# Verify webhook URL is set
echo $SLACK_WEBHOOK_URL

# Test webhook manually
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL
```

### Issue: Git commit/push fails

**Possible causes:**
- Not in a git repository
- No write permissions
- Branch protection rules

**Solution:**
```bash
# Check git status
git status

# Verify remote access
git remote -v

# Try manual commit first
git add v0.7.0-release-checklist.md
git commit -m "test"
git push origin main
```

---

## 🎨 Advanced Features

### JSON Cache Analytics

Access historical readiness data programmatically:

```python
from release_dashboard.cache import ReadinessCache

cache = ReadinessCache()
history = cache.load()

# Get trend analysis
trend = cache.get_trend(lookback=10)
print(f"Current: {trend['current']}%")
print(f"Trend: {trend['trend_emoji']} {trend['trend']}")
print(f"Average (last 10): {trend['avg']}%")

# Export to CSV for analysis
cache.export_csv(".cache/readiness_history.csv")
```

### Custom Scoring Weights

Modify weights in `release_dashboard/scoring.py`:

```python
class ReadinessScorer:
    CORE_GATES_WEIGHT = 0.60      # Increase core gates importance
    OPTIONAL_GATES_WEIGHT = 0.15
    DEPLOYMENT_WEIGHT = 0.15
    SIGNOFF_WEIGHT = 0.10
```

### PR Auto-Commenter (Coming Soon)

Planned enhancement: Automatically comment readiness score on every PR.

```yaml
# Future workflow step
- name: Comment Readiness on PR
  uses: actions/github-script@v7
  with:
    script: |
      // Post readiness score as PR comment
```

---

## 🔐 Security Best Practices

1. **Never commit tokens**: Use environment variables or GitHub Secrets
2. **Rotate tokens regularly**: Generate new PAT every 90 days
3. **Limit token scope**: Only grant `repo` access (not `admin:org`)
4. **Use branch protection**: Require PR reviews for main branch
5. **Enable 2FA**: Protect your GitHub account

---

## 📚 Additional Resources

- **Main Checklist**: [`v0.7.0-release-checklist.md`](../v0.7.0-release-checklist.md)
- **CI Preflight Guide**: [`CI_PREFLIGHT_README.md`](../CI_PREFLIGHT_README.md)
- **Chaos Engineering**: [`SELF_HEALING_CHAOS_README.md`](../SELF_HEALING_CHAOS_README.md)
- **Stage Readiness**: [`STAGE_READINESS_VERIFICATION_SUMMARY.md`](../STAGE_READINESS_VERIFICATION_SUMMARY.md)
- **GitHub Actions**: [`.github/workflows/update-readiness.yml`](../.github/workflows/update-readiness.yml)

---

## 🤝 Contributing

Found a bug or have a feature request? Please open an issue!

### Development Setup

```bash
# Clone repository
git clone https://github.com/MAGSASA-CARD-ERP/MAGSASA-CARD-ERP.git
cd MAGSASA-CARD-ERP

# Install dev dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest tests/

# Run linter
ruff check scripts/
```

---

## 📝 Changelog

### Version 1.0.0 (2024-12-15)
- ✨ Initial production release
- ✅ Modular architecture (fetch, update, notify, scoring, cache)
- 🎨 Rich terminal output with colors and tables
- 📊 JSON caching for trend analysis
- 🔔 Enhanced Slack notifications
- 🚪 CI gating with `--check-only` flag
- 📖 Comprehensive documentation

---

## 📞 Support

**Maintainer:** @gerome650  
**Team Channel:** #dev-alerts (Slack)  
**Documentation:** [This README](./README_RELEASE_UPDATER.md)

For urgent issues during release window, contact the on-call engineer via PagerDuty.

---

**Made with ❤️ by the MAGSASA-CARD-ERP Team**

