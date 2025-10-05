# 🚀 Release Dashboard Updater

Automated CLI tool that updates your `v0.7.0-release-checklist.md` with the latest GitHub Actions and CI/CD data.

## 🎯 Features

- **Real-time CI Data**: Fetches latest workflow runs from GitHub API
- **Smart Scoring**: Calculates weighted release readiness score
- **Automated Updates**: Updates markdown sections using HTML comment markers
- **Git Integration**: Optional automatic commit and push
- **Slack Notifications**: Alert when readiness score drops below 90%
- **Trend Analysis**: Shows CI trends with emoji indicators
- **Dry Run Mode**: Preview changes before applying

## 📦 Installation

The script requires Python 3.11+ and the following dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- `PyGithub>=2.0.0` - GitHub API client
- `requests>=2.31.0` - HTTP requests

## 🔧 Configuration

### Environment Variables

Set these environment variables for full functionality:

```bash
# Required: GitHub Personal Access Token
export GH_TOKEN="ghp_your_token_here"

# Optional: Slack webhook for notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with these permissions:
   - `repo` (full repository access)
   - `actions:read` (read GitHub Actions data)
   - `workflow` (read workflow runs)

## 🚀 Usage

### Basic Usage

```bash
# Update dashboard with latest CI data
python scripts/update_release_dashboard.py

# Enable verbose output
python scripts/update_release_dashboard.py --verbose

# Preview changes without applying
python scripts/update_release_dashboard.py --dry-run
```

### Advanced Usage

```bash
# Auto-commit changes to main branch
python scripts/update_release_dashboard.py --commit --branch main

# Update and send Slack notification if score < 90%
python scripts/update_release_dashboard.py --notify

# Full automation with custom token
python scripts/update_release_dashboard.py \
  --commit \
  --branch develop \
  --token ghp_your_token \
  --notify \
  --verbose
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--commit` | Automatically commit updated file | `false` |
| `--branch <name>` | Target branch for commits | `main` |
| `--token <token>` | GitHub access token | `$GH_TOKEN` |
| `--notify` | Send Slack notification if score < 90% | `false` |
| `--verbose` | Enable detailed logging | `false` |
| `--dry-run` | Preview changes without applying | `false` |

## 📊 What Gets Updated

The script automatically updates these sections in your checklist:

### 1. Release Readiness Score
- **Location**: `<!-- READINESS_SCORE_START -->` to `<!-- READINESS_SCORE_END -->`
- **Updates**: Score percentage, status emoji, breakdown by category
- **Calculation**: Weighted average of Core (50%), Optional (20%), Deployment (20%), Sign-off (10%)

### 2. CI Snapshot Table
- **Location**: `<!-- CI_SNAPSHOT_START -->` to `<!-- CI_SNAPSHOT_END -->`
- **Updates**: Last 10 workflow runs with status, duration, timestamps
- **Features**: Trend indicators (📈📉📊), emoji status, branch info

## 🏗️ Architecture

### Core Components

```python
ReleaseDashboardUpdater
├── GitHub API Integration
│   ├── Workflow runs fetching
│   ├── Job status parsing
│   └── Rate limiting handling
├── Markdown Processing
│   ├── Section marker detection
│   ├── Content replacement
│   └── Format preservation
├── Scoring Engine
│   ├── Weighted calculations
│   ├── Category breakdown
│   └── Trend analysis
└── Git Operations
    ├── Change detection
    ├── Auto-commit
    └── Push to remote
```

### Workflow Integration

The tool integrates with GitHub Actions via `.github/workflows/update-readiness.yml`:

```yaml
# Triggers:
- Push to main/develop branches
- Daily cron job (9 AM UTC)
- Manual workflow dispatch

# Actions:
- Updates dashboard automatically
- Commits changes to repository
- Creates PRs for non-main branches
- Sends Slack notifications
```

## 🎨 Markdown Markers

Use these HTML comment markers in your checklist to enable automated updates:

```markdown
<!-- READINESS_SCORE_START -->
## 📊 Release Readiness Score: 85% 🟢
[Your score content here]
<!-- READINESS_SCORE_END -->

<!-- CI_SNAPSHOT_START -->
## 📡 Last CI Snapshot
[Your CI data here]
<!-- CI_SNAPSHOT_END -->
```

## 📈 Scoring Algorithm

The readiness score is calculated using weighted categories:

```python
total_score = (
    core_score * 0.50 +      # Core gates (must pass)
    optional_score * 0.20 +  # Optional gates (nice-to-have)
    deployment_score * 0.20 + # Deployment automation
    signoff_score * 0.10     # Final sign-off checklist
) * 100
```

### Score Thresholds

| Score | Status | Emoji | Description |
|-------|--------|-------|-------------|
| 95%+ | Release Ready | 🟢 | All critical items complete |
| 85-94% | Nearly Ready | 🟡 | Minor blockers remain |
| 70-84% | In Progress | 🟠 | Several blockers |
| <70% | Not Ready | 🔴 | Major blockers |

## 🔔 Notifications

### Slack Integration

When `--notify` is used and readiness score < 90%:

```json
{
  "text": "🚨 Release Readiness Alert",
  "attachments": [{
    "color": "warning",
    "fields": [
      {"title": "Score", "value": "85%", "short": true},
      {"title": "Status", "value": "Below 90% threshold", "short": true}
    ]
  }]
}
```

### GitHub Actions Notifications

The workflow automatically:
- Comments on PRs when dashboard is updated
- Sends failure notifications to Slack
- Creates automated PRs for dashboard updates

## 🛠️ Development

### Adding New Metrics

To add new automated metrics:

1. **Update the scoring calculation** in `calculate_readiness_score()`
2. **Add new markdown markers** in your checklist file
3. **Implement update logic** in `update_markdown_sections()`
4. **Test with dry-run mode**

### Extending Workflow Display

Add new workflow mappings in `workflow_display_names`:

```python
self.workflow_display_names = {
    'your-new-workflow.yml': 'Your Display Name',
    # ... existing mappings
}
```

## 🧪 Testing

### Manual Testing

```bash
# Test with dry-run (no changes made)
python scripts/update_release_dashboard.py --dry-run --verbose

# Test with fake token (will fail gracefully)
GH_TOKEN="fake_token" python scripts/update_release_dashboard.py --dry-run

# Test scoring calculation
python -c "
from scripts.update_release_dashboard import ReleaseDashboardUpdater
updater = ReleaseDashboardUpdater(token='fake', verbose=True)
score = updater.calculate_readiness_score()
print(f'Score: {score[\"total_score\"]}%')
"
```

### Integration Testing

The GitHub Actions workflow includes comprehensive testing:
- Dependency installation
- Token validation
- Git operations
- Error handling
- Notification delivery

## 🚨 Troubleshooting

### Common Issues

**"GitHub token required" error:**
```bash
# Set your token
export GH_TOKEN="ghp_your_token_here"
# Or use --token flag
python scripts/update_release_dashboard.py --token ghp_your_token
```

**"No changes to commit" message:**
- This is normal if the dashboard is already up-to-date
- Use `--verbose` to see what data was fetched

**Markers not found:**
- Ensure your checklist has the proper HTML comment markers
- Check for typos in marker names
- The script will add markers if they don't exist

**Slack notification failed:**
- Verify `SLACK_WEBHOOK_URL` environment variable
- Check webhook URL format and permissions
- Use `--verbose` to see error details

### Debug Mode

Enable verbose logging for detailed troubleshooting:

```bash
python scripts/update_release_dashboard.py --verbose --dry-run
```

This shows:
- GitHub API calls and responses
- Markdown processing steps
- Scoring calculations
- Git operations

## 📚 Examples

### Daily Automation

Add to your crontab for daily updates:

```bash
# Update dashboard daily at 9 AM
0 9 * * * cd /path/to/repo && python scripts/update_release_dashboard.py --commit --notify
```

### Pre-Release Check

Before tagging a release:

```bash
# Check current readiness
python scripts/update_release_dashboard.py --verbose

# If score < 95%, investigate blockers
python scripts/update_release_dashboard.py --dry-run | grep -A 10 "Not Ready"
```

### Team Integration

Add to your team's workflow:

```bash
# In your release checklist script
echo "Checking release readiness..."
python scripts/update_release_dashboard.py --notify

if [ $? -eq 0 ]; then
    echo "✅ Dashboard updated successfully"
else
    echo "❌ Dashboard update failed"
    exit 1
fi
```

## 🔮 Future Enhancements

Planned features for future versions:

- **JIRA Integration**: Sync with project management tools
- **Custom Metrics**: User-defined scoring criteria
- **Historical Trends**: Track readiness over time
- **Team Notifications**: Individual owner alerts
- **Dashboard UI**: Web interface for non-technical users
- **API Endpoint**: REST API for external integrations

## 📄 License

This tool is part of the MAGSASA-CARD-ERP project and follows the same license terms.

## 🤝 Contributing

To contribute to this tool:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

---

*Last updated: December 2024*
*Tool version: 1.0.0*
