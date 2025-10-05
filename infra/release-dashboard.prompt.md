# 🧠 Release Dashboard Automation - Regeneration Prompt

**Save this prompt to instantly recreate the full system in any repository**

---

## 🎯 System Overview

Create a production-grade release readiness automation system that:
- ✅ Updates release checklists automatically with CI/CD data
- ✅ Calculates weighted readiness scores
- ✅ Posts auto-updating PR comments with live badges
- ✅ Sends Slack notifications on failures
- ✅ Gates CI/CD pipelines based on readiness thresholds

---

## 📦 Core Components to Implement

### 1. Modular Python CLI (`scripts/update_release_dashboard.py`)

**Requirements:**
- Fetch GitHub Actions workflow runs via PyGithub
- Calculate weighted readiness score (Core 50%, Optional 20%, Deployment 20%, Sign-off 10%)
- Update Markdown file sections between comment markers: `<!-- CI_SNAPSHOT_START/END -->` and `<!-- READINESS_SCORE_START/END -->`
- Rich terminal output with colored tables and panels
- JSON caching to `.cache/readiness.json` for trend analysis

**CLI Flags:**
```bash
--dry-run              # Preview changes without writing
--check-only           # Exit 1 if readiness < 90% (CI gate)
--commit               # Auto-commit changes to git
--notify               # Send Slack notifications
--pr-comment           # Post/update PR comment
--strict               # Fail if commenting/notifying fails
--verbose              # Enable detailed logging
--no-cache             # Skip JSON caching
--branch <name>        # Target branch (default: main)
--token <token>        # GitHub PAT (overrides GH_TOKEN env)
--repo <owner/repo>    # Repository name (auto-detected)
```

---

### 2. Modular Architecture (`scripts/release_dashboard/`)

Create separate modules for clean separation of concerns:

#### `fetch.py` - GitHub Workflow Fetcher
- Connect to GitHub API using PyGithub
- Fetch last N workflow runs with status, duration, branch, commit
- Calculate CI health metrics (success rate, failing workflows)
- Auto-detect repository from git remote

#### `scoring.py` - Readiness Score Calculator
- Parse release checklist markdown file
- Count 🟢 PASS, 🟡 PENDING, 🔴 FAIL gates in tables
- Count [x] checked and [ ] unchecked items in checklists
- Apply weighted formula: `Total = Core(50%) + Optional(20%) + Deployment(20%) + Signoff(10%)`
- Adjust score based on CI health
- Identify current blockers

#### `update.py` - Markdown Updater
- Read existing checklist file
- Generate CI snapshot markdown with workflow table
- Generate readiness score section with breakdown
- Update content between comment markers using regex
- Preserve manual content outside markers
- Detect changes before writing

#### `notify.py` - Slack Notifier
- Send rich Slack messages via webhook
- Include score, failing workflows, blockers
- Add action buttons for viewing checklist and CI runs
- Color-code messages based on severity
- Support custom messages

#### `cache.py` - JSON Cache Manager
- Store historical readiness scores
- Support trend analysis (improving/stable/declining)
- Export to CSV for analysis
- Limit history to last 100 entries
- Calculate min/max/average scores

#### `pr_commenter.py` - PR Auto-Commenter
- Authenticate with GitHub using token
- Auto-detect PR context from GitHub Actions environment (`GITHUB_REF`, `GITHUB_EVENT_PATH`)
- Generate comment with:
  - Current readiness score with emoji
  - Top 3 failing workflows with links
  - Dashboard link to checklist file
  - Shields.io badge with dynamic color
  - Last updated timestamp
- Use HTML marker for idempotent updates: `<!-- RELEASE_DASHBOARD_COMMENT_MARKER: DO_NOT_DELETE -->`
- Search for existing comment and update instead of creating duplicates
- Badge colors: 🟢 ≥95% (green), 🟡 90-94.9% (yellow), 🟠 80-89.9% (orange), 🔴 <80% (red)

---

### 3. GitHub Actions Workflow (`.github/workflows/update-readiness.yml`)

**Triggers:**
- `push` to `main` or `develop`
- `pull_request` (opened, synchronize, reopened)
- `schedule` - daily at 09:00 UTC (`0 9 * * *`)
- `workflow_dispatch` with manual input parameters

**Steps:**
1. Checkout repository (with full history)
2. Setup Python 3.11+
3. Install dependencies from requirements.txt
4. Run updater: `python scripts/update_release_dashboard.py --commit --notify --pr-comment --verbose`
5. Optional: Readiness gate check: `python scripts/update_release_dashboard.py --check-only`
6. Create PR if on non-main branch
7. Notify on failure via Slack

**Required Permissions:**
```yaml
permissions:
  contents: write        # For commits
  actions: read          # For workflow data
  pull-requests: write   # For PR comments
  issues: write          # For PR comments (PRs are issues)
```

---

### 4. Documentation Files

Create 4 comprehensive documentation files:

#### `scripts/README_RELEASE_UPDATER.md`
- Overview and key features
- Architecture diagram with component responsibilities
- Quick start guide with prerequisites
- Complete CLI reference with all flags
- Usage examples (preview, update, gate, PR comment)
- How it works (fetch, score, update, cache, notify)
- Configuration guide (env vars, GitHub token, Slack webhook)
- GitHub Actions automation details
- Readiness score breakdown and formula
- Troubleshooting guide
- Advanced features (JSON analytics, custom weights)
- Security best practices

#### `QUICK_START_DASHBOARD.md`
- 2-minute quick start guide
- Setup instructions (< 5 steps)
- Basic usage commands
- CLI flags cheat sheet
- Troubleshooting top issues
- File locations
- Example output

#### `RELEASE_DASHBOARD_AUTOMATION_COMPLETE.md`
- Project summary and deliverables
- Architecture and code metrics
- Technical highlights
- Before/after comparison
- Success criteria verification
- Impact metrics
- Next steps and enhancements

#### `PR_AUTO_COMMENTER_IMPLEMENTATION_COMPLETE.md`
- PR commenter feature deep dive
- Architecture and key methods
- Usage examples (CLI, Actions, programmatic)
- Comment format examples
- Badge color coding rules
- Configuration and permissions
- How it works (detection, updates, badges)
- Error handling (graceful vs strict)
- Integration examples
- Debugging guide
- Customization options

---

### 5. Dependencies (requirements.txt)

Add to existing requirements.txt:
```
PyGithub>=2.0.0      # GitHub API client for workflow runs
rich>=13.0.0         # Beautiful terminal output
requests>=2.31.0     # HTTP requests for Slack webhooks
```

---

## 🎯 Implementation Checklist

### Python Modules
- [ ] Create `scripts/release_dashboard/` directory
- [ ] Implement `fetch.py` with GitHubWorkflowFetcher class
- [ ] Implement `scoring.py` with ReadinessScorer class
- [ ] Implement `update.py` with MarkdownUpdater class
- [ ] Implement `notify.py` with SlackNotifier class
- [ ] Implement `cache.py` with ReadinessCache class
- [ ] Implement `pr_commenter.py` with PRCommenter class
- [ ] Create `__init__.py` exposing all classes
- [ ] Implement main CLI `update_release_dashboard.py` orchestrating all modules

### GitHub Actions
- [ ] Create `.github/workflows/update-readiness.yml`
- [ ] Configure triggers (push, PR, schedule, manual)
- [ ] Set required permissions
- [ ] Add environment variables
- [ ] Configure input parameters for manual dispatch

### Documentation
- [ ] Create comprehensive README (`scripts/README_RELEASE_UPDATER.md`)
- [ ] Create quick start guide (`QUICK_START_DASHBOARD.md`)
- [ ] Create completion report (`RELEASE_DASHBOARD_AUTOMATION_COMPLETE.md`)
- [ ] Create PR commenter guide (`PR_AUTO_COMMENTER_IMPLEMENTATION_COMPLETE.md`)
- [ ] Add this prompt to `infra/release-dashboard.prompt.md`

### Testing
- [ ] Test locally with `--dry-run`
- [ ] Test readiness gate with `--check-only`
- [ ] Test PR comment on actual PR
- [ ] Test Slack notifications (if webhook configured)
- [ ] Test full automation flow in CI

---

## 🚀 Usage Examples

### Preview Changes
```bash
python scripts/update_release_dashboard.py --dry-run
```

### Update Dashboard
```bash
python scripts/update_release_dashboard.py --verbose
```

### Full Automation
```bash
python scripts/update_release_dashboard.py --commit --notify --pr-comment --verbose
```

### CI Gate
```bash
python scripts/update_release_dashboard.py --check-only
# Exits 1 if readiness < 90%
```

---

## 🎨 Key Features to Highlight

### Rich Terminal Output
Use `rich` library for beautiful terminal output:
- Colored status messages (✅ success, ❌ error, ⚠️ warning, ℹ️ info)
- Tables for score breakdown
- Panels for status display
- Progress indicators

### Idempotent PR Comments
- Use HTML marker `<!-- RELEASE_DASHBOARD_COMMENT_MARKER: DO_NOT_DELETE -->`
- Search for existing comment before creating new one
- Update existing comment atomically

### Dynamic Shields.io Badges
```python
badge_url = f"https://img.shields.io/badge/Readiness-{score}%25-{color}.svg?style=for-the-badge"
```

### Graceful Error Handling
- Default: Log warnings but don't fail
- Strict mode (`--strict`): Fail build on any error
- Helpful error messages with troubleshooting hints

---

## 🔧 Configuration

### Environment Variables
```bash
# Required
export GH_TOKEN="ghp_your_github_personal_access_token"

# Optional
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### GitHub Token Scopes
- `repo` - Full repository access
- `workflow` - Read workflow runs (usually included in `repo`)

---

## 📊 Scoring Formula

```
Total Score = Core Gates (50%) 
            + Optional Gates (20%) 
            + Deployment (20%) 
            + Final Sign-Off (10%)
```

**Example:**
- Core Gates: 7/8 = 87.5% → 87.5% × 0.50 = 43.75%
- Optional Gates: 7/8 = 87.5% → 87.5% × 0.20 = 17.50%
- Deployment: 6/8 = 75.0% → 75.0% × 0.20 = 15.00%
- Sign-Off: 11/14 = 78.6% → 78.6% × 0.10 = 7.86%

**Total: 84.11%**

---

## 🎯 Success Criteria

System should:
- ✅ Run end-to-end with no manual steps
- ✅ Post/update PR comments idempotently
- ✅ Show readiness score, badge, and blockers in PR comments
- ✅ Fail CI if readiness < 90% in `--check-only` mode
- ✅ Include comprehensive documentation
- ✅ Support developer onboarding in < 10 minutes

---

## 🔮 Optional Enhancements

### Auto-Tag Releases (Self-Releasing System)
When readiness hits ≥95%, automatically:
1. Create annotated git tag (e.g., `v0.7.0`)
2. Push tag to trigger release workflow
3. Generate release notes from CHANGELOG
4. Notify team of successful release

**Implementation:**
```python
def auto_tag_release(score: float, version: str):
    if score >= 95.0:
        subprocess.run(['git', 'tag', '-a', version, '-m', f'Release {version}'])
        subprocess.run(['git', 'push', 'origin', version])
```

---

## 📚 References

- **PyGithub Documentation:** https://pygithub.readthedocs.io/
- **Rich Documentation:** https://rich.readthedocs.io/
- **Shields.io:** https://shields.io/
- **GitHub Actions:** https://docs.github.com/en/actions

---

## 💡 Pro Tips

1. **Start with `--dry-run`** to preview changes safely
2. **Use modular architecture** for maintainability
3. **Test locally** before committing to CI
4. **Document everything** - future you will thank you
5. **Add comprehensive error handling** - things will break
6. **Make it beautiful** - developers love good UX
7. **Cache results** - enable trend analysis
8. **Use semantic commit messages** - helps with changelogs

---

## 🎉 Expected Outcome

After implementing this system, you should have:

✅ **Fully automated release dashboard** updating daily  
✅ **PR comments** showing readiness on every pull request  
✅ **CI gating** preventing low-readiness releases  
✅ **Slack notifications** alerting team to issues  
✅ **Historical data** for trend analysis  
✅ **Beautiful CLI** with rich terminal output  
✅ **Production-grade code** with error handling  
✅ **Comprehensive docs** for easy onboarding  

**Total Implementation Time:** 4-6 hours for full system

---

**Save this prompt as `infra/release-dashboard.prompt.md` in your repository. When you need to recreate or adapt the system, simply paste this prompt into Cursor/Claude and watch it build!** 🚀

---

*Prompt Version: 1.0.0*  
*Last Updated: October 5, 2025*  
*Compatible with: Cursor, Claude, GitHub Copilot*

