# 🚀 CI Intelligence Agent - Quick Start Guide

## What is This?

The **CI Intelligence Agent** is an autonomous system that automatically:
- ✅ Detects and analyzes CI failures
- 🤖 Fixes common issues automatically  
- 📊 Learns from every failure
- 📈 Generates weekly intelligence reports
- 🎯 Improves over time

## 5-Minute Setup

### 1. Verify Installation

All components are already installed! Just verify:

```bash
# Check scripts exist
ls scripts/analyze_ci_failure.py
ls scripts/auto_fix_ci_failures.py
ls scripts/generate_ci_intelligence_report.py
ls scripts/ci_agent_cli.py

# Make executable
chmod +x scripts/*.py
```

### 2. Try the CLI

```bash
# Show stats (will initialize database if needed)
python scripts/ci_agent_cli.py --stats

# Show trends
python scripts/ci_agent_cli.py --show-trends
```

### 3. Test Manually

```bash
# Analyze a failure (example with dummy log)
echo "ModuleNotFoundError: No module named 'numpy'" > test-log.txt
python scripts/analyze_ci_failure.py --job-logs test-log.txt --json-output test-analysis.json

# Try auto-fix
python scripts/auto_fix_ci_failures.py --analysis-file test-analysis.json

# Clean up
rm test-log.txt test-analysis.json
```

## How It Works

### Automatic (Zero Config Needed)

1. **CI Fails** → Workflow automatically triggers analysis
2. **Analysis Runs** → Categorizes failure, checks history
3. **Auto-Fix Attempts** → If fixable, creates PR automatically
4. **Learning** → Records result for future use
5. **Weekly Reports** → Every Sunday, generates intelligence report

### Manual Usage

```bash
# Quick health check
python scripts/ci_agent_cli.py --stats

# See what's failing
python scripts/ci_agent_cli.py --show-trends --days 7

# Generate report now
python scripts/ci_agent_cli.py --generate-report

# Check recent fixes
python scripts/ci_agent_cli.py --recent-fixes
```

## Common Use Cases

### 1. Check CI Health

```bash
python scripts/ci_agent_cli.py --stats
```

**Output:**
```
📊 CI Intelligence Statistics

╔══════════════════════════════╦═══════╗
║ Metric                       ║ Value ║
╠══════════════════════════════╬═══════╣
║ Total Failures Tracked       ║ 42    ║
║ Unique Failure Categories    ║ 5     ║
║ Total Fix Attempts           ║ 38    ║
║ Successful Fixes             ║ 33    ║
║ Overall Success Rate         ║ 86.8% ║
╚══════════════════════════════╩═══════╝
```

### 2. Investigate Trends

```bash
python scripts/ci_agent_cli.py --show-trends --days 14
```

**Output:**
```
📈 Failure Trends (Last 14 days)

╔════════════╦══════════════╦═══════════════════╗
║ Category   ║ Occurrences  ║ Trend             ║
╠════════════╬══════════════╬═══════════════════╣
║ Dependency ║ 12           ║ 🔥 Rising         ║
║ Network    ║ 8            ║ 📊 Stable         ║
║ Tests      ║ 4            ║ 📉 Improving      ║
╚════════════╩══════════════╩═══════════════════╝
```

### 3. Generate Ad-Hoc Report

```bash
python scripts/ci_agent_cli.py --generate-report --days 7
```

Generates: `reports/CI_WEEKLY_INTELLIGENCE.md`

### 4. Manual Analysis

```bash
# Analyze latest CI run
python scripts/ci_agent_cli.py --analyze-latest
```

## Weekly Workflow

### For Developers

**Monday Morning:**
1. Check GitHub for weekly intelligence report issue
2. Review any auto-fix PRs from weekend
3. Approve/merge if appropriate

**When CI Fails:**
1. Check PR comments for automatic analysis
2. Wait for auto-fix PR (if applicable)
3. Manual fix only if auto-fix didn't work

### For DevOps/SRE

**Every Monday:**
1. Review weekly intelligence report
2. Check for rising trends
3. Update fix strategies if needed
4. Implement recommendations

## Understanding the Reports

### Key Metrics

#### Auto-Fix Success Rate
```
🛠️ Auto-fix success rate: 87% (↑ +5%)
```
- **Good:** >80%, rising ↑
- **Action needed:** <70% or falling ↓

#### MTTR (Mean Time To Recovery)
```
📉 MTTR: 3.4 min (↓ -18%)
```
- **Good:** <5 minutes, falling ↓
- **Action needed:** >10 minutes or rising ↑

#### Trend Indicators
- 🔥 **Rising** - Issue getting more frequent
- 📉 **Improving** - Issue getting less frequent  
- 📊 **Stable** - Issue frequency unchanged

## Files and Locations

```
.
├── scripts/
│   ├── analyze_ci_failure.py          # Failure analyzer
│   ├── auto_fix_ci_failures.py        # Auto-fix engine
│   ├── generate_ci_intelligence_report.py  # Report generator
│   └── ci_agent_cli.py                # Developer CLI
│
├── .github/workflows/
│   ├── ci.yml                         # Enhanced with self-healing
│   └── ci-intelligence-report.yml     # Weekly reports
│
├── reports/
│   └── CI_WEEKLY_INTELLIGENCE.md      # Latest weekly report
│
├── docs/
│   └── SELF_HEALING_CI.md             # Full documentation
│
├── ci_failure_history.db              # Historical data (auto-created)
└── CI_INTELLIGENCE_QUICKSTART.md      # This file
```

## Troubleshooting

### "Database not found"

**Normal!** The database is created automatically on first use.

```bash
# Manually initialize if needed
python -c "
from scripts.analyze_ci_failure import HistoricalDatabase
db = HistoricalDatabase('ci_failure_history.db')
db.close()
print('✅ Database initialized')
"
```

### "No data available"

Run some CI pipelines first! The system needs failures to analyze.

### "Analysis failed"

Check that all dependencies are installed:

```bash
pip install -r requirements.txt
pip install tabulate
```

## Advanced Usage

### Query Database Directly

```bash
sqlite3 ci_failure_history.db

# Show all failure categories
sqlite> SELECT category, COUNT(*) as count 
        FROM failures 
        GROUP BY category 
        ORDER BY count DESC;

# Show recent fixes
sqlite> SELECT * FROM fix_attempts 
        ORDER BY timestamp DESC 
        LIMIT 10;

# Calculate success rate by strategy
sqlite> SELECT 
          fix_strategy,
          COUNT(*) as attempts,
          SUM(success) as successful,
          ROUND(100.0 * SUM(success) / COUNT(*), 1) as success_rate
        FROM fix_attempts
        GROUP BY fix_strategy
        ORDER BY success_rate DESC;
```

### Custom Reporting Period

```bash
# Last 30 days
python scripts/generate_ci_intelligence_report.py \
  --days 30 \
  --output reports/MONTHLY_$(date +%Y-%m).md

# Last quarter (90 days)
python scripts/generate_ci_intelligence_report.py \
  --days 90 \
  --output reports/QUARTERLY_$(date +%Y-Q%q).md
```

### Export Data

```bash
# Export to CSV
sqlite3 ci_failure_history.db << EOF
.headers on
.mode csv
.output failures_export.csv
SELECT * FROM failures;
.quit
EOF

# Export fix attempts
sqlite3 ci_failure_history.db << EOF
.headers on
.mode csv
.output fixes_export.csv
SELECT * FROM fix_attempts;
.quit
EOF
```

## Integration with Other Tools

### Slack Notifications (Example)

Add to workflow:

```yaml
- name: Notify Slack
  if: steps.analyze.outputs.analysis_complete == 'true'
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "CI Intelligence: New failure analyzed",
        "attachments": [{
          "color": "warning",
          "text": "Check GitHub for details"
        }]
      }
```

### Grafana Dashboard (Example)

Export metrics:

```bash
# Create metrics file for Prometheus
python << EOF
import sqlite3
import json
from datetime import datetime, timedelta

db = sqlite3.connect('ci_failure_history.db')
cursor = db.cursor()

# Get metrics
cursor.execute('SELECT COUNT(*) FROM failures WHERE timestamp >= datetime("now", "-7 days")')
failures_week = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM fix_attempts WHERE success = 1 AND timestamp >= datetime("now", "-7 days")')
fixes_week = cursor.fetchone()[0]

metrics = {
    "ci_failures_total": failures_week,
    "ci_fixes_successful": fixes_week,
    "ci_fix_success_rate": fixes_week / max(failures_week, 1),
    "timestamp": datetime.now().isoformat()
}

with open('metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print("✅ Metrics exported to metrics.json")
EOF
```

## Next Steps

1. ✅ **You're already set up!** The system is running automatically
2. 📖 **Read full docs:** `docs/SELF_HEALING_CI.md`
3. 📊 **Check weekly reports:** Every Monday
4. 🎯 **Monitor success rates:** Aim for >80%
5. 🚀 **Iterate and improve:** Add custom patterns as needed

## Quick Reference Card

```bash
# Essential Commands
python scripts/ci_agent_cli.py --stats              # Overall health
python scripts/ci_agent_cli.py --show-trends        # What's trending
python scripts/ci_agent_cli.py --generate-report    # Create report
python scripts/ci_agent_cli.py --recent-fixes       # Recent activity
python scripts/ci_agent_cli.py --analyze-latest     # Analyze now

# Workflows
# - ci.yml: Automatic failure analysis + auto-fix
# - ci-intelligence-report.yml: Weekly reports (Sundays)

# Reports Location
cat reports/CI_WEEKLY_INTELLIGENCE.md

# Database Query
sqlite3 ci_failure_history.db "SELECT * FROM failures LIMIT 5;"

# Help
python scripts/ci_agent_cli.py --help
```

## Support

- **Full Documentation:** `docs/SELF_HEALING_CI.md`
- **Inline Help:** `--help` flag on all scripts
- **GitHub Issues:** Label with `ci-intelligence`

---

**🎉 That's it! You're ready to use the CI Intelligence Agent!**

The system learns and improves automatically. Just let it run and check the weekly reports for insights.

