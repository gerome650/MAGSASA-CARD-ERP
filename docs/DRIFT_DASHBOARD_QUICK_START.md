# 🚀 Drift Dashboard Quick Start

## TL;DR

```bash
# Generate dashboard from governance history
python scripts/qa/gov_drift_dashboard.py

# View reports
open governance-drift-dashboard.html
cat governance-drift-dashboard.md
```

---

## 📊 What It Does

Analyzes `governance-history.json` to create visual reports showing:
- 📈 Uptime trends
- 🐢 Latency performance  
- 🚨 Drift event detection
- 📋 Anomaly summaries

---

## 🎯 Outputs

| File | Description | Use Case |
|------|-------------|----------|
| `governance-drift-dashboard.md` | Markdown report | Documentation, PRs, issues |
| `governance-drift-dashboard.html` | HTML dashboard | Visual browsing, sharing |

---

## 🔧 Installation

```bash
# Install matplotlib (required for charts)
pip install matplotlib

# Or using requirements-dev.txt
pip install -r requirements-dev.txt
```

---

## 📖 Usage Examples

### Basic Usage
```bash
# Run from project root
python scripts/qa/gov_drift_dashboard.py
```

### View Output
```bash
# Open HTML in browser
open governance-drift-dashboard.html  # macOS
xdg-open governance-drift-dashboard.html  # Linux
start governance-drift-dashboard.html  # Windows

# View Markdown
cat governance-drift-dashboard.md
```

### CI Integration
```yaml
# .github/workflows/governance-dashboard.yml
- name: Generate Drift Dashboard
  run: python scripts/qa/gov_drift_dashboard.py

- name: Upload Dashboard
  uses: actions/upload-artifact@v4
  with:
    name: governance-dashboard
    path: |
      governance-drift-dashboard.md
      governance-drift-dashboard.html
```

---

## 📋 What You'll See

### Summary Metrics
- Total heartbeats
- Healthy runs vs drift detected (%)
- Average uptime, latency, error rate
- Min/max ranges

### Charts
1. **Uptime Trend** - Line chart with warning/critical thresholds
2. **Latency Trend** - Line chart with drift event markers
3. **Status Distribution** - Pie chart showing health ratio

### Anomalies Table
- Last 5 drift events
- Timestamp + message for each

### Drift Warning ⚠️
- Appears if drift ratio > 20%
- Includes recommended actions

---

## 🔍 Troubleshooting

### File Not Found
```
❌ Error: History file not found: governance-history.json
💡 Tip: Run the governance-heartbeat workflow to generate history data.
```

**Solution:** Run heartbeat workflow or create sample data:
```bash
# Run heartbeat workflow manually
gh workflow run governance-heartbeat.yml

# Or create sample file (for testing)
echo '[]' > governance-history.json
```

### Charts Not Generated
```
⚠️  matplotlib not available, charts will be skipped
```

**Solution:** Install matplotlib:
```bash
pip install matplotlib
```

### Empty History
```
⚠️  Warning: History file is empty
```

**Solution:** Wait for heartbeat workflow to run or add sample data.

---

## 📊 Sample Output

### Markdown Report
```markdown
# 🎯 Governance Drift Dashboard

## 📊 Summary Metrics
| Metric | Value |
|--------|-------|
| **Total Heartbeats** | 10 |
| **Healthy Runs** | 6 (60.0%) |
| **Drift Detected** | 4 (40.0%) |
...

## ⚠️ DRIFT WARNING
Alert: Drift ratio is 40.0%, which exceeds the 20.0% threshold!
```

### HTML Dashboard
- Modern gradient design (purple theme)
- Interactive metric cards
- Embedded Base64 charts (no external files)
- Responsive layout (mobile-friendly)
- Warning alerts for high drift

---

## 🔗 Related Commands

### View History Data
```bash
# Full history
cat governance-history.json | jq '.'

# Last 5 records
cat governance-history.json | jq '.[-5:]'

# Find drift events
cat governance-history.json | jq '.[] | select(.status == "drift-detected")'
```

### Calculate Metrics
```bash
# Total records
cat governance-history.json | jq '. | length'

# Drift count
cat governance-history.json | jq '[.[] | select(.status == "drift-detected")] | length'

# Average uptime
cat governance-history.json | jq '[.[] | select(.uptime != "unavailable") | .uptime | tonumber] | add / length'
```

---

## 🎨 Customization

### Change Thresholds
Edit the constants in `scripts/qa/gov_drift_dashboard.py`:
```python
UPTIME_WARN = 99.0
UPTIME_FAIL = 98.0
LATENCY_WARN = 2500
LATENCY_FAIL = 4000
DRIFT_WARNING_THRESHOLD = 20.0
```

### Change Output Files
```python
OUTPUT_MD = "governance-drift-dashboard.md"
OUTPUT_HTML = "governance-drift-dashboard.html"
```

---

## 📚 Learn More

- [GOVERNANCE_HISTORY_TRACKING.md](GOVERNANCE_HISTORY_TRACKING.md) - History file format and analysis
- [DRIFT_DASHBOARD_IMPLEMENTATION_SUMMARY.md](../DRIFT_DASHBOARD_IMPLEMENTATION_SUMMARY.md) - Complete technical details
- [GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md](../GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md) - Anomaly detection system

---

## 💡 Tips

1. **Run Regularly** - Generate dashboard after each heartbeat run
2. **CI Artifacts** - Upload dashboards as GitHub Actions artifacts
3. **Share Reports** - Send HTML dashboard to stakeholders via email
4. **Track Trends** - Compare dashboards over time to spot patterns
5. **Automate** - Add to scheduled jobs for automatic reporting

---

## 🆘 Need Help?

```bash
# Check script syntax
python -m py_compile scripts/qa/gov_drift_dashboard.py

# Verbose run (shows detailed output)
python scripts/qa/gov_drift_dashboard.py 2>&1 | tee dashboard.log

# Check dependencies
python -c "import matplotlib; print('✅ matplotlib installed')"
```

---

**Quick Links:**
- 📄 [Full Implementation Summary](../DRIFT_DASHBOARD_IMPLEMENTATION_SUMMARY.md)
- 🔧 [Script Source](../scripts/qa/gov_drift_dashboard.py)
- 📊 [Sample Dashboard](../governance-drift-dashboard.html)

---

*Generated by the MAGSASA-CARD-ERP QA Team*  
*Last Updated: 2025-10-09*

