# 🧪 Merge Quality Early-Warning System

> **A proactive CI/CD quality enforcement system with Slack integration, trend analysis, and auto-fail protection**

[![CI Check](https://img.shields.io/badge/CI-Automated-brightgreen)](../../actions)
[![Merge Quality](https://img.shields.io/badge/Merge%20Quality-90%25%2B-success)](merge_quality_state.json)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Features](#-features)
3. [Architecture](#-architecture)
4. [Quick Start](#-quick-start)
5. [Components](#-components)
6. [Scoring System](#-scoring-system)
7. [Early Warning & Auto-Fail](#-early-warning--auto-fail)
8. [Usage](#-usage)
9. [Makefile Commands](#-makefile-commands)
10. [GitHub Actions Integration](#-github-actions-integration)
11. [Slack Integration](#-slack-integration)
12. [Configuration](#-configuration)
13. [Development](#-development)
14. [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

The **Merge Quality Early-Warning System** is a comprehensive CI/CD quality monitoring solution designed to:

- **Track PR quality trends** over time with rolling 10-PR history
- **Calculate merge readiness scores** (0-100%) based on multiple quality gates
- **Provide early warnings** before quality issues become critical (2/3 strikes)
- **Automatically block merges** when quality drops below acceptable levels (3+ strikes)
- **Send rich Slack notifications** with trends, sparklines, and actionable insights
- **Maintain historical data** for trend analysis and decision-making

### Key Differentiators

✅ **Proactive** - Warns before blocking, not after  
✅ **Trend-Aware** - Uses rolling averages and sparklines  
✅ **Developer-Friendly** - Clear feedback with actionable suggestions  
✅ **Automated** - No manual intervention required  
✅ **Slack-Integrated** - Real-time team notifications

---

## ✨ Features

### Core Features

- **🧠 Merge Score Calculator** - Multi-factor scoring engine (syntax, lint, tests, coverage, security)
- **📊 Trend Analysis** - Rolling 10-PR history with sparkline visualization
- **⚠️ Early Warning System** - 2/3 strikes trigger warning, 3+ strikes auto-fail
- **📱 Slack Integration** - Rich Block Kit messages with buttons and trends
- **✅ Payload Validation** - JSON schema validation for Slack messages
- **🔍 Schema Diff Reporter** - Detailed field-by-field comparison with severity ranking
- **🧪 Test Suite** - Comprehensive test coverage for all components
- **📝 State Tracking** - JSON-based historical data storage

### Quality Gates

| Gate | Weight | Description |
|------|--------|-------------|
| **Syntax** | 25% | Python syntax validation (pass/fail) |
| **Lint** | 20% | Code quality checks (Ruff) |
| **Tests** | 30% | Test results (pass/fail ratio) |
| **Coverage** | 15% | Test coverage percentage |
| **Security** | 10% | Vulnerability scanning |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
│  (CI Check: Pull Request & Push Events)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Quality Gate Execution                    │
│  • Syntax Validation    • Linting (Ruff)                    │
│  • Tests (Pytest)       • Coverage (coverage.py)            │
│  • Security Scans       • Generate Reports (JSON)           │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           Merge Score Calculation Engine                     │
│  scripts/update_merge_scores.py                              │
│  • Reads quality gate outputs                                │
│  • Calculates weighted score (0-100%)                        │
│  • Updates rolling history (last 10 PRs)                     │
│  • Tracks streak below goal                                  │
│  • Generates Slack payload                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           Slack Digest Builder                               │
│  scripts/slack_merge_digest.py                               │
│  • Builds Block Kit message                                  │
│  • Adds sparkline trend visualization                        │
│  • Includes early warning alerts                             │
│  • Formats performance metrics                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           Payload Validation                                 │
│  scripts/validate_slack_payload.py                           │
│  scripts/schema_diff_reporter.py                             │
│  • Validates against JSON schema                             │
│  • Checks Block Kit structure                                │
│  • Reports issues with severity levels                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│           Decision Logic                                     │
│  • Check auto-fail condition (3+ strikes)                    │
│  • Check early warning (2 strikes)                           │
│  • Post PR comment with results                              │
│  • Send Slack notification                                   │
│  • Exit with error if auto-fail                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager (recommended) or `pip`
- `make` utility
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/MAGSASA-CARD-ERP.git
cd MAGSASA-CARD-ERP

# 2. Install dependencies
make setup

# 3. (Optional) Configure Slack webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Verify Installation

```bash
# Run validation suite
make validate-all

# Run tests
make ci
```

---

## 📦 Components

### 1. Merge Score Calculator (`scripts/update_merge_scores.py`)

**Purpose:** Calculate merge readiness scores from CI metrics

**Key Features:**
- Multi-factor scoring (syntax, lint, tests, coverage, security)
- Weighted score calculation (0-100%)
- Rolling history management (last 10 PRs)
- Streak tracking below team goal
- Early warning detection

**Usage:**
```bash
python scripts/update_merge_scores.py \
  --pytest-json pytest-report.json \
  --coverage-xml coverage.xml \
  --ruff-json lint-report.json \
  --syntax-guard-json syntax-guard.json \
  --team-goal 90.0 \
  --branch feature/my-feature \
  --commit abc123 \
  --actor johndoe \
  --output merge_slack_payload.json
```

### 2. Slack Digest Builder (`scripts/slack_merge_digest.py`)

**Purpose:** Build rich Slack Block Kit messages for quality reporting

**Key Features:**
- Block Kit payload construction
- Sparkline trend visualization
- Early warning alerts
- Performance metrics (slowest workflows)
- Repository metadata

**Usage:**
```bash
python scripts/slack_merge_digest.py \
  --payload merge_slack_payload.json \
  --repo your-org/your-repo \
  --branch main \
  --commit abc123 \
  --actor johndoe \
  --run-url https://github.com/your-org/your-repo/actions/runs/123 \
  --dashboard-url https://your-org.github.io/your-repo/ci-dashboard/ \
  --webhook-url $SLACK_WEBHOOK_URL \
  --send
```

### 3. Payload Validator (`scripts/validate_slack_payload.py`)

**Purpose:** Validate Slack payloads against JSON schema

**Key Features:**
- JSON schema validation
- Block Kit structure checks
- Fix suggestions (read-only)
- Example payload generation

**Usage:**
```bash
# Validate payload
python scripts/validate_slack_payload.py slack_message.json --suggest-fixes

# Create example payload
python scripts/validate_slack_payload.py --create-example example_payload.json
```

### 4. Schema Diff Reporter (`scripts/schema_diff_reporter.py`)

**Purpose:** Generate detailed diff reports with severity ranking

**Key Features:**
- Field-by-field comparison
- Severity classification (Critical, High, Medium, Low, Info)
- Detailed suggestions
- JSON and text output formats

**Usage:**
```bash
# Generate diff report
python scripts/schema_diff_reporter.py \
  slack_message.json \
  --schema slack_payload_schema.json

# JSON output
python scripts/schema_diff_reporter.py \
  slack_message.json \
  --schema slack_payload_schema.json \
  --json \
  --output diff_report.json
```

---

## 🎯 Scoring System

### Scoring Formula

```
Total Score = (Syntax × 0.25) + (Lint × 0.20) + (Tests × 0.30) + (Coverage × 0.15) + (Security × 0.10)
```

### Component Scores

#### 1. Syntax Score (25%)
- **100%** - All files pass syntax validation
- **0%** - Any file has syntax errors
- **50%** - No data available

#### 2. Lint Score (20%)
- **100%** - 0 linting issues
- **90-80%** - 1-5 issues
- **80-65%** - 6-20 issues
- **<65%** - 20+ issues

#### 3. Test Score (30%)
- **100%** - All tests pass
- **0%** - All tests fail
- **X%** - (Passed / Total) × 100

#### 4. Coverage Score (15%)
- **100%** - ≥90% coverage
- **90-100%** - 80-89% coverage
- **70-90%** - 70-79% coverage
- **50-70%** - 50-69% coverage
- **<50%** - <50% coverage

#### 5. Security Score (10%)
- **100%** - No vulnerabilities
- **-30** points per critical vulnerability
- **-15** points per high vulnerability
- **-5** points per medium vulnerability

### Example Score Calculation

```python
metrics = {
    'syntax': {'passed': True},           # 100 × 0.25 = 25.0
    'lint': {'issues': 3},                # 84 × 0.20 = 16.8
    'tests': {'passed': 95, 'failed': 5}, # 95 × 0.30 = 28.5
    'coverage': {'coverage_percent': 85}, # 95 × 0.15 = 14.25
    'security': {'critical': 0}           # 100 × 0.10 = 10.0
}

# Total Score = 25.0 + 16.8 + 28.5 + 14.25 + 10.0 = 94.55%
```

---

## ⚠️ Early Warning & Auto-Fail

### 3-Strike System

| Strikes | Status | Action |
|---------|--------|--------|
| **0** | ✅ **Healthy** | No action required |
| **1** | 🟡 **Below Goal** | Informational notice |
| **2** | ⚠️ **Early Warning** | Slack alert, PR comment |
| **3+** | 🔥 **Auto-Fail** | Merge blocked, CI fails |

### Streak Logic

```python
# Pseudo-code
if score >= team_goal:
    streak = 0  # Reset streak
else:
    streak += 1  # Increment streak

if streak >= 2:
    early_warning = True
    
if streak >= 3:
    auto_fail = True
    exit(1)  # Block merge
```

### Reset Conditions

The streak resets to **0** when:
1. A PR achieves a score **≥ team goal** (default: 90%)
2. Manual reset via `merge_quality_state.json` edit

---

## 💻 Usage

### Local Development

```bash
# Run complete CI pipeline locally
make ci

# Individual commands
make validate-payload  # Validate Slack payload
make validate-all      # Syntax + lint + payload
make fix-all          # Auto-fix code issues
make validate-schema  # Detailed schema validation
```

### Manual Score Calculation

```bash
# Run tests and generate reports
pytest --json-report --json-report-file=pytest-report.json \
       --cov=. --cov-report=xml

# Generate lint report
ruff check . --output-format=json > lint-report.json

# Calculate merge score
python scripts/update_merge_scores.py \
  --pytest-json pytest-report.json \
  --coverage-xml coverage.xml \
  --ruff-json lint-report.json \
  --team-goal 90.0 \
  --branch $(git branch --show-current) \
  --commit $(git rev-parse HEAD) \
  --actor $(git config user.name)
```

### Slack Message Testing

```bash
# Build Slack message without sending
python scripts/slack_merge_digest.py \
  --payload merge_slack_payload.json \
  --repo test/repo \
  --branch test-branch \
  --commit abc123 \
  --actor testuser \
  --output slack_message.json

# Validate message
python scripts/validate_slack_payload.py slack_message.json --suggest-fixes
```

---

## 🛠️ Makefile Commands

### Validation Commands

```bash
make validate-payload   # Validate Slack payload against schema
make validate-all       # Run syntax + lint + payload validation
make validate-schema    # Detailed schema validation with diff report
```

### Fix Commands

```bash
make fix-all           # Auto-fix code (ruff --fix, black) + regenerate payload
```

### CI Commands

```bash
make ci                # Complete CI pipeline: fix-all → validate-all → pytest
make ci-preflight      # Run full CI checks before pushing
make coverage-check    # Run tests with coverage enforcement
```

### Helper Commands

```bash
make help              # Show all available commands
make hygiene           # Run format & lint checks (black --check, ruff)
make test              # Run tests with coverage
make lint              # Run linting only
```

---

## 🔄 GitHub Actions Integration

### CI Check Workflow (`.github/workflows/ci-check.yml`)

**Triggers:**
- Pull requests to `main`
- Pushes to `main`

**Steps:**
1. Run syntax validation
2. Run linting (JSON output)
3. Run tests with coverage (JSON & XML)
4. Calculate merge quality score
5. Build Slack message
6. Validate payload structure
7. Send Slack notification
8. Check auto-fail condition
9. Comment on PR with results
10. Upload artifacts

**Environment Variables:**
- `SLACK_WEBHOOK_URL` - Slack webhook URL (secret)

### Daily Digest Workflow (`.github/workflows/slack-daily-digest.yml`)

**Triggers:**
- Daily at 9 AM UTC
- Manual trigger via `workflow_dispatch`

**Steps:**
1. Fetch recent workflow runs (last 24 hours)
2. Calculate CI success rate
3. Load merge quality state
4. Generate trend sparkline
5. Build daily digest message
6. Send to Slack
7. Upload artifacts

---

## 💬 Slack Integration

### Message Format

<img width="600" alt="Slack Message Example" src="https://via.placeholder.com/600x400.png?text=Slack+Message+Example">

### Block Kit Structure

```json
{
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "📊 Merge Quality Report" }
    },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "*Merge Score:*\n`85%` ✅" },
        { "type": "mrkdwn", "text": "*Status:*\nON TRACK" }
      ]
    },
    {
      "type": "section",
      "text": { "type": "mrkdwn", "text": "*📈 Trend:* `▂▃▆▇▇▆▅█`" }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "View Dashboard" },
          "url": "https://example.com/dashboard"
        }
      ]
    }
  ],
  "color": "#56d364"
}
```

### Status Indicators

| Status | Emoji | Color | Condition |
|--------|-------|-------|-----------|
| **ON TRACK** | ✅ | Green (#56d364) | Score ≥ 90% |
| **BELOW GOAL** | 🟠 | Yellow (#ffd33d) | 80% ≤ Score < 90% |
| **EARLY WARNING** | ⚠️ | Orange (#ffd33d) | 2 strikes |
| **AUTO-FAIL** | 🔥 | Red (#ff6a69) | 3+ strikes |

---

## ⚙️ Configuration

### Team Goal

Set in `merge_quality_state.json`:

```json
{
  "team_goal": 90,
  "streak_below_goal": 0,
  "history": []
}
```

Or via CLI:

```bash
python scripts/update_merge_scores.py --team-goal 95.0 ...
```

### Slack Webhook

```bash
# Set as environment variable
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Or in GitHub Secrets
# Repository Settings → Secrets → New repository secret
# Name: SLACK_WEBHOOK_URL
# Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Scoring Weights

Edit `scripts/update_merge_scores.py`:

```python
weights = {
    'syntax': 0.25,    # 25%
    'lint': 0.20,      # 20%
    'tests': 0.30,     # 30%
    'coverage': 0.15,  # 15%
    'security': 0.10   # 10%
}
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_merge_score_calculation.py -v

# Run with coverage
pytest tests/ --cov=scripts --cov-report=html
```

### Adding New Quality Gates

1. **Update `MergeScoreCalculator` class** (`scripts/update_merge_scores.py`):
   ```python
   def _calculate_new_gate_score(self, metrics: dict) -> float:
       # Your scoring logic
       return score
   ```

2. **Add weight to scoring formula**:
   ```python
   weights = {
       'syntax': 0.20,    # Reduced from 0.25
       'lint': 0.20,
       'tests': 0.30,
       'coverage': 0.15,
       'security': 0.10,
       'new_gate': 0.05   # New gate
   }
   ```

3. **Update tests** (`tests/test_merge_score_calculation.py`):
   ```python
   def test_new_gate_score_calculation(self):
       result = self.calculator._calculate_new_gate_score({'param': value})
       self.assertEqual(result, expected_score)
   ```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Payload Validation Fails

**Problem:** `❌ Payload validation failed: Missing required 'blocks' field`

**Solution:**
```bash
# Check payload structure
cat merge_slack_payload.json | jq .

# Regenerate payload
make fix-all

# Validate again
make validate-payload
```

#### 2. Auto-Fail Triggered Unexpectedly

**Problem:** `🔥 Auto-fail triggered: 3+ consecutive PRs below goal!`

**Solution:**
```bash
# Check current state
cat merge_quality_state.json | jq '.streak_below_goal'

# Reset streak manually (if needed)
jq '.streak_below_goal = 0' merge_quality_state.json > tmp.json && mv tmp.json merge_quality_state.json

# Or improve code quality to meet goal
make fix-all
make test
```

#### 3. Slack Notification Not Sent

**Problem:** Slack message not received

**Solution:**
```bash
# Verify webhook URL is set
echo $SLACK_WEBHOOK_URL

# Test webhook manually
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}' \
  $SLACK_WEBHOOK_URL

# Check CI logs for errors
# Look for "Send Slack Notification" step
```

#### 4. Score Calculation Errors

**Problem:** `Error loading pytest JSON: FileNotFoundError`

**Solution:**
```bash
# Ensure reports are generated
pytest --json-report --json-report-file=pytest-report.json
ruff check . --output-format=json > lint-report.json
pytest --cov=. --cov-report=xml

# Verify files exist
ls -la pytest-report.json coverage.xml lint-report.json

# Run score calculation
python scripts/update_merge_scores.py --pytest-json pytest-report.json ...
```

---

## 📊 Example Workflows

### Scenario 1: New Feature Branch

```bash
# 1. Create feature branch
git checkout -b feature/awesome-feature

# 2. Make changes
# ... code changes ...

# 3. Run local CI checks
make ci

# 4. Check merge score
cat merge_slack_payload.json | jq '.merge_score'
# Output: 92.5

# 5. Push changes
git push origin feature/awesome-feature

# 6. Create PR
# → GitHub Actions runs CI check
# → Merge score calculated
# → Slack notification sent
# → PR comment added with results
```

### Scenario 2: Early Warning Recovery

```bash
# Current state: 2 strikes (early warning)
cat merge_quality_state.json | jq '.streak_below_goal'
# Output: 2

# Fix issues to improve score
make fix-all       # Auto-fix code
make test          # Verify tests pass
make ci            # Run full CI pipeline

# Check new score
cat merge_slack_payload.json | jq '.merge_score'
# Output: 91.0 (above goal!)

# Push changes
git push

# → Streak resets to 0
# → Early warning cleared
```

---

## 📚 Additional Resources

- [Slack Block Kit Builder](https://api.slack.com/block-kit/building)
- [JSON Schema Validator](https://www.jsonschemavalidator.net/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make ci`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📝 License

This project is part of the MAGSASA-CARD-ERP system. See [LICENSE](LICENSE) for details.

---

## 📧 Contact

For questions or support, please open an issue or contact the development team.

---

**Built with ❤️ by the AgSense DevOps Team**

