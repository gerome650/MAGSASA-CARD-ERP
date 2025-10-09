# 📜 Governance History Tracking - Quick Reference

## Overview
The governance heartbeat workflow now maintains a persistent audit trail of all anomaly detection runs in `governance-history.json`.

## 📊 History File Format

```json
[
  {
    "timestamp": "2025-10-09T16:42:00Z",
    "uptime": "97.8",
    "latency": "4321",
    "error_rate": "2.3",
    "status": "drift-detected",
    "message": "⚠️ Latency above threshold (4321 ms > 4000 ms)"
  }
]
```

### Fields
- **timestamp**: ISO 8601 UTC timestamp of the heartbeat run
- **uptime**: Uptime percentage (or "unavailable")
- **latency**: Latency in milliseconds (or "unavailable")
- **error_rate**: Error rate percentage (or "unavailable")
- **status**: Either "healthy" or "drift-detected"
- **message**: Human-readable status message

---

## 🔍 Analyzing History Data

### View All History
```bash
cat governance-history.json | jq '.'
```

### Get Latest Record
```bash
cat governance-history.json | jq '.[-1]'
```

### Get Last N Records
```bash
# Last 5 records
cat governance-history.json | jq '.[-5:]'
```

### Find All Drift Events
```bash
cat governance-history.json | jq '.[] | select(.status == "drift-detected")'
```

### Find All Healthy Events
```bash
cat governance-history.json | jq '.[] | select(.status == "healthy")'
```

### Count Events by Status
```bash
echo "Healthy runs: $(cat governance-history.json | jq '[.[] | select(.status == "healthy")] | length')"
echo "Drift detected: $(cat governance-history.json | jq '[.[] | select(.status == "drift-detected")] | length')"
```

### Calculate Drift Percentage
```bash
TOTAL=$(cat governance-history.json | jq '. | length')
DRIFT=$(cat governance-history.json | jq '[.[] | select(.status == "drift-detected")] | length')
echo "scale=2; ($DRIFT * 100) / $TOTAL" | bc
```

### Filter by Date Range
```bash
# Events after a specific date
cat governance-history.json | jq '.[] | select(.timestamp > "2025-10-01T00:00:00Z")'
```

### Find High Latency Events
```bash
cat governance-history.json | jq '.[] | select(.latency != "unavailable" and (.latency | tonumber) > 4000)'
```

### Find Low Uptime Events
```bash
cat governance-history.json | jq '.[] | select(.uptime != "unavailable" and (.uptime | tonumber) < 98.0)'
```

---

## 📈 Advanced Analysis

### Average Uptime (excluding unavailable)
```bash
cat governance-history.json | jq '[.[] | select(.uptime != "unavailable") | .uptime | tonumber] | add / length'
```

### Average Latency (excluding unavailable)
```bash
cat governance-history.json | jq '[.[] | select(.latency != "unavailable") | .latency | tonumber] | add / length'
```

### Average Error Rate (excluding unavailable)
```bash
cat governance-history.json | jq '[.[] | select(.error_rate != "unavailable") | .error_rate | tonumber] | add / length'
```

### Min/Max Latency
```bash
cat governance-history.json | jq '[.[] | select(.latency != "unavailable") | .latency | tonumber] | min, max'
```

### Time Between Drift Events
```bash
cat governance-history.json | jq '[.[] | select(.status == "drift-detected") | .timestamp]'
```

---

## 🔨 Maintenance

### Archive Old Records
```bash
# Keep only last 50 records
cat governance-history.json | jq '.[-50:]' > governance-history.new.json
mv governance-history.new.json governance-history.json
```

### Export to CSV
```bash
cat governance-history.json | jq -r '.[] | [.timestamp, .uptime, .latency, .error_rate, .status] | @csv' > governance-history.csv
```

### Pretty Print for Reports
```bash
cat governance-history.json | jq -r '.[] | "\(.timestamp) | \(.status) | Uptime: \(.uptime)% | Latency: \(.latency)ms | Error: \(.error_rate)%"'
```

---

## 🚨 Alerting Examples

### Check if Last Run Was Drift
```bash
STATUS=$(cat governance-history.json | jq -r '.[-1].status')
if [ "$STATUS" = "drift-detected" ]; then
  echo "⚠️ Last heartbeat detected drift!"
  cat governance-history.json | jq -r '.[-1].message'
fi
```

### Check for Consecutive Drift Events
```bash
LAST_TWO=$(cat governance-history.json | jq -r '.[-2:] | .[].status' | sort -u)
if [ "$LAST_TWO" = "drift-detected" ]; then
  echo "🚨 Multiple consecutive drift events detected!"
fi
```

### Detect Uptime Degradation Trend
```bash
# Compare last 5 runs to previous 5 runs
RECENT_AVG=$(cat governance-history.json | jq '[.[-5:] | .[] | select(.uptime != "unavailable") | .uptime | tonumber] | add / length')
PREVIOUS_AVG=$(cat governance-history.json | jq '[.[-10:-5] | .[] | select(.uptime != "unavailable") | .uptime | tonumber] | add / length')

echo "Recent average uptime: $RECENT_AVG%"
echo "Previous average uptime: $PREVIOUS_AVG%"
```

---

## 📊 Visualization Ideas

### Generate Simple ASCII Chart
```bash
cat governance-history.json | jq -r '.[] | "\(.timestamp) | \(if .status == "healthy" then "✅" else "⚠️" end)"'
```

### Export for Grafana/Prometheus
Convert the JSON to a format suitable for time-series databases:
```bash
cat governance-history.json | jq -r '.[] | "governance_uptime{\(.timestamp)} \(.uptime)\ngovernance_latency{\(.timestamp)} \(.latency)\ngovernance_error_rate{\(.timestamp)} \(.error_rate)"'
```

---

## 🔐 Security Considerations

### The history file contains:
- ✅ Metrics (uptime, latency, error rate)
- ✅ Timestamps
- ✅ Status messages
- ❌ NO sensitive data (API keys, tokens, etc.)

### Safe to:
- Commit to repository
- Share in reports
- Include in documentation
- Analyze with external tools

---

## 🧹 Best Practices

1. **Regular Reviews**: Check the history file monthly to identify trends
2. **Set Alerts**: Create scripts to alert on consecutive drift events
3. **Archive Periodically**: Consider archiving old records after 1 year
4. **Trend Analysis**: Use the data to adjust thresholds over time
5. **Incident Correlation**: Cross-reference drift events with incident logs

---

## 🆘 Troubleshooting

### History file not created?
Check the workflow logs for the "Append anomaly record" step.

### History file has duplicates?
This shouldn't happen, but you can deduplicate:
```bash
cat governance-history.json | jq 'unique_by(.timestamp)' > governance-history.clean.json
```

### History file too large?
Archive old entries:
```bash
# Archive entries older than 1 year
cat governance-history.json | jq --arg date "$(date -u -v-1y +%Y-%m-%dT%H:%M:%SZ)" '[.[] | select(.timestamp > $date)]' > governance-history.json
```

### Git conflicts on history file?
The workflow commits with `[skip ci]` to avoid loops. Conflicts are rare but can be resolved:
```bash
git pull --rebase
# Manually merge if needed
git push
```

---

## 📚 Related Documentation

- [GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md](../GOVERNANCE_HEARTBEAT_ANOMALY_DETECTION.md) - Full feature documentation
- [.github/workflows/governance-heartbeat.yml](../.github/workflows/governance-heartbeat.yml) - Workflow implementation

---

**With governance-history.json, you now have a time-machine for your governance metrics! 🕰️**

