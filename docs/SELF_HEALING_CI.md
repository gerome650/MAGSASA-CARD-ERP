# 🧠 Self-Healing CI Intelligence Agent

## Stage 7.1: Production-Grade Intelligent CI/CD System

This document describes the Self-Healing CI Intelligence Agent implemented in Stage 7.1 of the MAGSASA-CARD ERP DevOps maturity roadmap. This system provides automated failure analysis, intelligent auto-fixing, historical learning, and proactive insights.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Usage Guide](#usage-guide)
5. [Workflow Integration](#workflow-integration)
6. [Data Model](#data-model)
7. [Interpreting Reports](#interpreting-reports)
8. [Extending the System](#extending-the-system)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Self-Healing CI Intelligence Agent?

The Self-Healing CI Intelligence Agent is an autonomous system that:

- **🔍 Analyzes** CI/CD failures automatically with pattern recognition
- **🤖 Auto-Fixes** common issues based on historical success rates
- **📊 Learns** from every failure and fix attempt
- **📈 Reports** weekly intelligence with actionable insights
- **🎯 Prioritizes** fixes using adaptive strategies
- **📉 Tracks** MTTR (Mean Time To Recovery) and trends

### Key Benefits

- **70%+ auto-resolution** of transient CI issues
- **Reduced MTTR** through intelligent prioritization
- **Historical learning** improves fix success rates over time
- **Proactive insights** prevent recurring issues
- **Zero manual intervention** for common failures

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Healing CI System                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │   Failure    │──────▶│   Auto-Fix   │──────▶│  GitHub │ │
│  │   Analyzer   │      │   Engine     │      │   PR     │ │
│  └──────────────┘      └──────────────┘      └──────────┘ │
│         │                      │                           │
│         │                      │                           │
│         ▼                      ▼                           │
│  ┌──────────────────────────────────┐                     │
│  │   Historical Database (SQLite)   │                     │
│  │   - Failures                     │                     │
│  │   - Fix Attempts                 │                     │
│  │   - Success Rates                │                     │
│  │   - MTTR Metrics                 │                     │
│  └──────────────────────────────────┘                     │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐      ┌──────────────┐                  │
│  │ Intelligence │──────▶│   Weekly     │                  │
│  │   Reporter   │      │   Reports    │                  │
│  └──────────────┘      └──────────────┘                  │
│         │                      │                           │
│         │                      ▼                           │
│         │              ┌──────────────┐                   │
│         └──────────────▶│   GitHub     │                  │
│                        │   Issues     │                   │
│                        └──────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Integration

The system integrates into CI/CD workflows through:

1. **Failure Detection** - Triggered on job failure
2. **Automatic Analysis** - Analyzes logs and categorizes issues
3. **Intelligent Fixing** - Applies prioritized fixes
4. **Learning Loop** - Records results for future use
5. **Weekly Reporting** - Generates insights and recommendations

---

## Components

### 1. Failure Analyzer (`scripts/analyze_ci_failure.py`)

**Purpose:** Intelligently analyze CI failures and categorize issues.

**Features:**
- Pattern-based failure detection
- Confidence scoring
- Historical frequency tracking
- Trend analysis (rising/improving/stable)
- MTTR calculation
- Error signature generation

**Supported Failure Categories:**
- `dependency` - Missing or incompatible packages
- `test_assertion` - Test failures
- `network_timeout` - Connection issues
- `missing_file` - File not found errors
- `schema_validation` - Configuration errors
- `permission` - Access control issues
- `disk_space` - Storage problems

**Usage:**

```bash
# Analyze latest CI run
python scripts/analyze_ci_failure.py --analyze-latest

# Analyze specific workflow run
python scripts/analyze_ci_failure.py \
  --workflow-run-id 12345678 \
  --json-output analysis.json \
  --markdown-output analysis.md

# Analyze from log file
python scripts/analyze_ci_failure.py \
  --job-logs ci-logs.txt \
  --job-name "test" \
  --branch "main"
```

**Output:** JSON and Markdown reports with:
- Failure categories
- Root causes
- Recommended fixes
- Confidence scores
- Historical statistics
- Trend indicators

### 2. Auto-Fix Engine (`scripts/auto_fix_ci_failures.py`)

**Purpose:** Automatically fix common CI failures with adaptive strategies.

**Features:**
- Historical success rate tracking
- Adaptive prioritization
- Multiple fix strategies
- Structured commit metadata
- Auto PR creation

**Supported Fixes:**
- Installing missing dependencies
- Creating missing files
- Fixing permissions
- Retry configuration updates

**Usage:**

```bash
# Fix from analysis
python scripts/auto_fix_ci_failures.py \
  --analysis-file analysis.json \
  --create-pr \
  --base-branch main

# Direct dependency fix
python scripts/auto_fix_ci_failures.py \
  --package numpy \
  --create-pr
```

**Fix Prioritization:**
The engine calculates priority scores based on:
- **Confidence** (0-100 points)
- **Historical Success Rate** (0-50 points)
- **Severity** (high=+30, medium=+15, low=0)

Higher priority fixes are attempted first.

### 3. Intelligence Report Generator (`scripts/generate_ci_intelligence_report.py`)

**Purpose:** Generate comprehensive weekly intelligence reports.

**Features:**
- Executive summary with KPIs
- Top 5 failure categories
- Auto-fix performance metrics
- MTTR trends
- Daily breakdown
- Key learnings
- Actionable recommendations

**Usage:**

```bash
# Generate weekly report (7 days)
python scripts/generate_ci_intelligence_report.py \
  --output reports/CI_WEEKLY_INTELLIGENCE.md

# Custom period
python scripts/generate_ci_intelligence_report.py \
  --days 14 \
  --output reports/CI_BIWEEKLY_REPORT.md
```

**Report Sections:**
1. **Executive Summary** - High-level KPIs
2. **Top Failure Categories** - Most common issues
3. **Key Learnings** - Insights from data
4. **Auto-Fix Highlights** - Success metrics
5. **Daily Breakdown** - Day-by-day analysis
6. **MTTR Trends** - Resolution time analysis
7. **Recommendations** - Actionable improvements

### 4. Developer CLI (`scripts/ci_agent_cli.py`)

**Purpose:** Command-line interface for developers to interact with the CI Intelligence Agent.

**Features:**
- Analyze latest runs
- Generate reports on demand
- Show failure trends
- View statistics
- Check recent fixes

**Usage:**

```bash
# Show overall statistics
python scripts/ci_agent_cli.py --stats

# Show failure trends
python scripts/ci_agent_cli.py --show-trends --days 7

# Analyze latest CI run
python scripts/ci_agent_cli.py --analyze-latest

# Generate report
python scripts/ci_agent_cli.py --generate-report

# Show recent fix attempts
python scripts/ci_agent_cli.py --recent-fixes
```

**Example Output:**

```
📈 Failure Trends (Last 7 days)

╔════════════╦══════════════╦═══════════════════╗
║ Category   ║ Occurrences  ║ Trend             ║
╠════════════╬══════════════╬═══════════════════╣
║ Dependency ║ 6            ║ 🔥 Rising         ║
║ Network    ║ 4            ║ 📊 Stable         ║
║ Tests      ║ 2            ║ 📉 Improving      ║
╚════════════╩══════════════╩═══════════════════╝
```

---

## Usage Guide

### For Developers

#### When CI Fails

1. **Automatic Analysis** - The system automatically analyzes failures
2. **Check PR Comments** - View analysis in PR comments
3. **Review Auto-Fix PRs** - Approve auto-generated fixes if appropriate
4. **Manual Intervention** - Fix non-auto-fixable issues

#### Using the CLI

```bash
# Quick status check
./scripts/ci_agent_cli.py --stats

# Investigate trends
./scripts/ci_agent_cli.py --show-trends

# Generate ad-hoc report
./scripts/ci_agent_cli.py --generate-report --days 7
```

### For DevOps/SRE

#### Weekly Review Process

1. **Check Weekly Report** - Review GitHub issue with intelligence report
2. **Identify Trends** - Look for rising failure categories
3. **Optimize Strategies** - Review low success rate fixes
4. **Implement Recommendations** - Act on suggested improvements
5. **Monitor MTTR** - Track resolution time improvements

#### Accessing Historical Data

```bash
# Query the database directly
sqlite3 ci_failure_history.db

# Example queries
sqlite> SELECT category, COUNT(*) FROM failures GROUP BY category;
sqlite> SELECT * FROM fix_attempts ORDER BY timestamp DESC LIMIT 10;
```

---

## Workflow Integration

### Automatic Failure Analysis

Workflows automatically trigger analysis on failure:

```yaml
analyze-failure:
  name: Analyze CI Failure
  runs-on: ubuntu-latest
  if: failure()
  needs: [test]
  steps:
    - name: Analyze failure
      run: python scripts/analyze_ci_failure.py --analyze-latest
```

### Auto-Fix on Failure

Auto-fix is triggered when issues are detected:

```yaml
auto-fix:
  name: Attempt Auto-Fix
  needs: [analyze-failure]
  if: needs.analyze-failure.outputs.auto_fixable == 'true'
  steps:
    - name: Apply fixes
      run: python scripts/auto_fix_ci_failures.py --analysis-file analysis.json --create-pr
```

### Weekly Reporting

Reports are generated automatically every Sunday:

```yaml
# .github/workflows/ci-intelligence-report.yml
on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at 00:00 UTC
```

---

## Data Model

### Database Schema

#### `failures` Table

```sql
CREATE TABLE failures (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    job_name TEXT,
    branch TEXT,
    category TEXT NOT NULL,
    error_signature TEXT NOT NULL,
    severity TEXT,
    root_cause TEXT,
    confidence REAL,
    created_at TEXT
);
```

#### `fix_attempts` Table

```sql
CREATE TABLE fix_attempts (
    id INTEGER PRIMARY KEY,
    failure_id INTEGER,
    timestamp TEXT NOT NULL,
    fix_strategy TEXT NOT NULL,
    fix_command TEXT,
    success INTEGER NOT NULL,
    resolution_time_minutes REAL,
    created_at TEXT,
    FOREIGN KEY (failure_id) REFERENCES failures(id)
);
```

### Error Signatures

Error signatures are MD5 hashes of normalized root causes, used to:
- Track recurring issues
- Calculate frequency
- Determine trends
- Link failures to fixes

**Example:**
```
Category: dependency
Root Cause: Missing dependency: numpy
Normalized: dependency:missing dependency: numpy
Signature: a1b2c3d4e5f6g7h8
```

---

## Interpreting Reports

### Executive Summary Metrics

#### Auto-Fix Success Rate
```
🛠️ Auto-fix success rate: 87% (↑ +5%)
```
- **Target:** >80%
- **Good:** Rising trend
- **Action if <70%:** Review and enhance fix strategies

#### MTTR (Mean Time To Recovery)
```
📉 MTTR: 3.4 min (↓ -18%)
```
- **Target:** <5 minutes
- **Good:** Decreasing trend
- **Action if >10min:** Investigate slow fixes

#### Top Recurring Issue
```
🔁 Top recurring issue: Dependency drift (numpy) – 6 occurrences
```
- **Target:** <3 occurrences
- **Action if recurring:** Implement preventive measures

### Trend Indicators

| Emoji | Trend      | Meaning                           |
|-------|------------|-----------------------------------|
| 🔥    | Rising     | Issue frequency increasing        |
| 📉    | Improving  | Issue frequency decreasing        |
| 📊    | Stable     | Issue frequency unchanged         |

### Recommendations Priority

1. **High Priority** - Rising trends, low success rates
2. **Medium Priority** - Stable but frequent issues
3. **Low Priority** - Improving trends, preventive measures

---

## Extending the System

### Adding New Failure Patterns

Edit `scripts/analyze_ci_failure.py`:

```python
self.failure_patterns = {
    'your_category': {
        'patterns': [
            r'YourErrorPattern',
            r'AnotherPattern.*'
        ],
        'severity': 'high',
        'auto_fixable': True
    }
}
```

### Adding New Fix Strategies

Edit `scripts/auto_fix_ci_failures.py`:

```python
def _fix_your_issue(self, analysis: Dict[str, Any]) -> bool:
    """Fix your custom issue."""
    # Implement fix logic
    self.fixes_applied.append({
        'type': 'your_category',
        'description': 'Fixed issue',
        'strategy': 'your_strategy',
        'success_rate': analysis.get('_success_rate', 0.0)
    })
    return True
```

### Custom Report Sections

Edit `scripts/generate_ci_intelligence_report.py`:

```python
def _generate_custom_section(self, since_date: str) -> str:
    """Generate custom report section."""
    # Query database
    # Analyze data
    # Return markdown
    return markdown_content
```

---

## Troubleshooting

### Database Issues

**Problem:** "Database not found"
```bash
# Solution: Initialize database
python -c "
from scripts.analyze_ci_failure import HistoricalDatabase
db = HistoricalDatabase('ci_failure_history.db')
db.close()
"
```

**Problem:** "Database locked"
```bash
# Solution: Close connections
rm -f ci_failure_history.db-journal
```

### Analysis Not Running

**Check:**
1. Workflow permissions (needs: write)
2. GitHub CLI authentication
3. Python dependencies installed
4. Logs accessible

### Auto-Fix Not Creating PRs

**Check:**
1. GitHub token has permissions
2. Branch protection allows bot commits
3. Analysis found auto-fixable issues
4. Fix strategies are implemented

### Reports Not Generating

**Check:**
1. Database has data
2. Time period has failures
3. Python dependencies installed
4. ci-reports branch exists

---

## Best Practices

### 1. Regular Reviews
- Review weekly reports every Monday
- Track MTTR trends monthly
- Update fix strategies quarterly

### 2. Data Hygiene
- Archive old reports (>90 days)
- Clean up test data
- Back up database monthly

### 3. Strategy Optimization
- Monitor success rates
- Remove ineffective strategies
- Add new patterns as needed

### 4. Team Communication
- Share insights in team meetings
- Document manual fixes for automation
- Celebrate improvements

---

## Metrics and KPIs

### Success Criteria

| Metric                  | Target    | Excellent |
|-------------------------|-----------|-----------|
| Auto-Fix Success Rate   | >70%      | >85%      |
| MTTR                    | <10min    | <5min     |
| Recurring Issues        | <5/week   | <2/week   |
| Manual Interventions    | <30%      | <15%      |

### Monitoring

```bash
# Weekly check
./scripts/ci_agent_cli.py --stats

# Trend analysis
./scripts/ci_agent_cli.py --show-trends --days 30

# Generate monthly report
./scripts/generate_ci_intelligence_report.py --days 30 \
  --output reports/MONTHLY_$(date +%Y-%m).md
```

---

## Support and Maintenance

### Getting Help

1. **Documentation:** This file and inline code comments
2. **CLI Help:** `./scripts/ci_agent_cli.py --help`
3. **Issues:** Create GitHub issue with `ci-intelligence` label

### Maintenance Tasks

#### Weekly
- Review intelligence report
- Check auto-fix success rates
- Monitor MTTR trends

#### Monthly
- Back up database
- Archive old reports
- Update fix strategies

#### Quarterly
- Review and optimize patterns
- Clean up historical data
- Update documentation

---

## Changelog

### v2.0 (Stage 7.1) - Current
- ✨ Historical tracking with SQLite
- ✨ Adaptive fix prioritization
- ✨ Weekly intelligence reports
- ✨ Developer CLI interface
- ✨ Trend analysis
- ✨ MTTR tracking

### v1.0 (Stage 6.x)
- Initial failure analysis
- Basic auto-fix capabilities
- Manual reporting

---

## License and Credits

**Part of:** MAGSASA-CARD ERP DevOps Maturity Roadmap
**Stage:** 7.1 - Self-Healing CI Intelligence Agent
**Built with:** Python, SQLite, GitHub Actions
**Maintained by:** DevOps Team

---

## Quick Reference

### Common Commands

```bash
# Analysis
./scripts/ci_agent_cli.py --analyze-latest

# Stats
./scripts/ci_agent_cli.py --stats

# Trends
./scripts/ci_agent_cli.py --show-trends --days 7

# Report
./scripts/ci_agent_cli.py --generate-report

# Manual analysis
./scripts/analyze_ci_failure.py --analyze-latest

# Manual fix
./scripts/auto_fix_ci_failures.py --package numpy --create-pr

# Generate report
./scripts/generate_ci_intelligence_report.py --days 7 \
  --output reports/WEEKLY.md
```

### File Locations

- **Scripts:** `scripts/`
- **Database:** `ci_failure_history.db`
- **Reports:** `reports/`
- **Workflows:** `.github/workflows/ci-intelligence-report.yml`
- **Documentation:** `docs/SELF_HEALING_CI.md`

---

**🎉 You're all set!** The Self-Healing CI Intelligence Agent is now fully operational and will continuously learn and improve your CI/CD pipeline reliability.

