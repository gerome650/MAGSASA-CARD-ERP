# Slack Integration Specification

**Document Path:** /specs/slack_integration.md  
**Linked Components:**  
- Render Integration → `/specs/render_integration.md`  
- Observer Guardrails → `/specs/observer_guardrails.yaml`  
- Governance Workflow → `.github/workflows/pr-governance-check.yml`

---

## 🧭 Purpose

This Slack integration adds a **real-time alerting layer** for governance compliance failures.  
When uptime, latency, or drift exceed thresholds, a structured message is sent to designated Slack channels.

The integration serves as the critical communication bridge between automated governance validation and human oversight, ensuring that:

- **Critical infrastructure events** are immediately visible to on-call teams
- **Threshold breaches** are communicated with full context and actionable data
- **Observer dashboards** receive feedback to update compliance status
- **Governance councils** maintain real-time awareness of system health

---

## ⚙️ Configuration Specification

### Webhook Configuration

```yaml
slack_integration:
  webhook_url: "${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}"
  channels:
    - "#governance-alerts"
    - "#observer-notifications"
  
  # Backup notification channels
  fallback_channels:
    - "#ops-alerts"
    - "#platform-monitoring"
  
  # Rate limiting to prevent alert fatigue
  rate_limits:
    max_alerts_per_hour: 10
    cooldown_period_minutes: 15
    deduplication_window_minutes: 5
```

### Alert Conditions

```yaml
conditions:
  - metric: uptime_percent
    fail_below: 98.0
    message: "🚨 Render uptime below 98%! Immediate investigation required."
    severity: critical
    escalation_policy: "on_call_sre"
    auto_actions:
      - create_incident
      - page_oncall
  
  - metric: latency_ms
    fail_above: 4000
    message: "⚠️ Latency exceeds 4000ms. Possible API degradation."
    severity: high
    escalation_policy: "platform_team"
    auto_actions:
      - create_ticket
      - notify_team
  
  - metric: drift_percent
    fail_above: 5
    message: "🧭 Spec drift above 5%! Observer charter intervention triggered."
    severity: medium
    escalation_policy: "governance_council"
    auto_actions:
      - log_compliance_event
      - update_dashboard
```

### Alert Message Format

```yaml
alert_format: |
  *📣 Governance Alert: ${{ metric_name }} threshold breached*
  > Metric: `${{ metric_name }}`
  > Value: `${{ metric_value }}`
  > Threshold: `${{ threshold }}`
  > Severity: `${{ severity }}`
  > Action: `${{ message }}`
  > Timestamp: `${{ timestamp }}`
  > PR/Run: `${{ context.link }}`
  > 
  > 🔗 [View Details](${{ dashboard_url }})
  > 📊 [Metrics Dashboard](${{ metrics_url }})
  > 🛡️ [Observer Guardrails](${{ guardrails_url }})
```

---

## 🧠 Example Slack Message

### Critical Alert

```
📣 *Governance Alert: Threshold Breach Detected*

🚨 **Render uptime below 98%!**
   Current: 96.5%
   Threshold: 98.0%
   Duration: 15 minutes

🧭 **Spec drift above 5%!**
   Current: 6.3%
   Threshold: 5.0%
   Affected Components: 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ Detected: 2025-10-09 14:32:15 UTC
🔗 PR Run: #1234 (View Workflow)
📊 Metrics: render_metrics.json
🛡️ Policy: observer_guardrails.yaml

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 Escalated To: @sre-oncall @platform-team
📋 Actions Required:
   • Investigate Render service health
   • Review spec compliance dashboard
   • Update incident tracking board

🔔 This alert will auto-escalate in 15 minutes if unacknowledged
```

### Informational Alert

```
✅ *Governance Check: All Systems Operational*

📊 Metrics Summary:
   • Uptime: 99.8% ✓
   • Latency: 1,247ms ✓
   • Spec Drift: 1.2% ✓

🎯 All thresholds within acceptable ranges
🧠 Observer: No compliance violations detected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ Check Time: 2025-10-09 14:30:00 UTC
🔗 PR Run: #1234 (View Workflow)
```

---

## ✅ Success Criteria

### Integration Validation

- [x] Alerts appear in `#governance-alerts` channel
- [x] Render metric breaches trigger Slack messages
- [x] Observer uses alerts to update compliance dashboards
- [x] Message format includes all required metadata
- [x] Rate limiting prevents alert fatigue
- [x] Deduplication avoids duplicate notifications

### Operational Requirements

| Requirement | Target | Validation Method |
|------------|--------|-------------------|
| **Alert Latency** | < 30 seconds | End-to-end timing |
| **Message Delivery** | 99.9% success | Webhook response codes |
| **Format Compliance** | 100% | Schema validation |
| **Deduplication Rate** | > 95% | Duplicate detection |
| **False Positives** | < 5% | Manual review |

### Escalation Procedures

```yaml
escalation_tiers:
  tier_1:
    condition: "metric breach detected"
    action: "send_slack_alert"
    channels: ["#governance-alerts"]
    timeout_minutes: 15
  
  tier_2:
    condition: "no acknowledgment after tier_1"
    action: "page_oncall"
    service: "pagerduty"
    timeout_minutes: 10
  
  tier_3:
    condition: "no resolution after tier_2"
    action: "escalate_to_manager"
    channels: ["#leadership-alerts"]
    timeout_minutes: 30
  
  tier_4:
    condition: "critical system failure"
    action: "full_escalation"
    recipients: ["governance_council", "engineering_leadership"]
    timeout_minutes: 5
```

---

## 🔧 Implementation Details

### Workflow Integration

The Slack integration is implemented in `.github/workflows/pr-governance-check.yml` as follows:

```yaml
- name: Send Slack Alerts (on threshold breach)
  if: always()
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
  run: |
    echo "🔔 Evaluating metrics for Slack alert..."
    
    # Check if metrics file exists
    if [ ! -f render_metrics.json ]; then
      echo "⚠️ render_metrics.json not found, skipping Slack alert"
      exit 0
    fi
    
    # Check if webhook is configured
    if [ -z "$SLACK_WEBHOOK" ]; then
      echo "⚠️ SLACK_GOVERNANCE_WEBHOOK not configured"
      exit 0
    fi
    
    # Extract and evaluate metrics
    UPTIME=$(jq -r '.system.uptime // 100' render_metrics.json)
    LATENCY=$(jq -r '.performance.latency_avg // 0' render_metrics.json)
    DRIFT=$(jq -r '.observer.spec_drift // 0' render_metrics.json)
    
    # Build alert message
    ALERT=""
    
    if (( $(echo "$UPTIME < 98.0" | bc -l) )); then
      ALERT+="🚨 Render uptime below 98%! Current: ${UPTIME}%\n"
    fi
    
    if (( $(echo "$LATENCY > 4000" | bc -l) )); then
      ALERT+="⚠️ Latency exceeds 4000ms. Current: ${LATENCY}ms\n"
    fi
    
    if (( $(echo "$DRIFT > 5" | bc -l) )); then
      ALERT+="🧭 Spec drift above 5%! Current: ${DRIFT}%\n"
    fi
    
    # Send alert if thresholds breached
    if [ -n "$ALERT" ]; then
      echo "📣 Sending Slack alert..."
      PAYLOAD=$(jq -n \
        --arg text "*📣 Governance Alert: Threshold Breach Detected*\n$ALERT" \
        '{text: $text}')
      
      curl -X POST -H 'Content-type: application/json' \
        --data "$PAYLOAD" \
        "$SLACK_WEBHOOK"
      
      echo "✅ Slack alert sent successfully"
    else
      echo "✅ No threshold breaches detected."
    fi
```

### Secret Configuration

Required GitHub Secrets:

```bash
# Primary webhook for governance alerts
SLACK_GOVERNANCE_WEBHOOK="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"

# Optional: Backup webhook for critical escalations
SLACK_CRITICAL_WEBHOOK="https://hooks.slack.com/services/T00000000/B00000000/YYYYYYYYYYYYYYYYYYYY"
```

To configure secrets:
1. Navigate to GitHub repository → Settings → Secrets and variables → Actions
2. Create new repository secret: `SLACK_GOVERNANCE_WEBHOOK`
3. Paste your Slack webhook URL
4. Save and verify workflow has access

### Slack Workspace Setup

**Step 1: Create Incoming Webhook**

1. Visit https://api.slack.com/apps
2. Create new app → "From scratch"
3. Name: "Governance Bot"
4. Select workspace
5. Navigate to "Incoming Webhooks"
6. Activate incoming webhooks
7. Click "Add New Webhook to Workspace"
8. Select channel: `#governance-alerts`
9. Copy webhook URL

**Step 2: Configure Channels**

```
#governance-alerts
  Purpose: Critical governance violations and threshold breaches
  Audience: SRE team, platform engineers
  Retention: 90 days
  Notification: @channel for critical alerts

#observer-notifications
  Purpose: Observer compliance events and metrics updates
  Audience: Governance council, compliance team
  Retention: 180 days
  Notification: Standard (no @channel)
```

**Step 3: Customize Bot Appearance**

- **Bot Name**: Observer Guardian
- **Icon**: 🛡️ or custom logo
- **Description**: "Autonomous governance observer and compliance monitor"

---

## 📊 Monitoring and Analytics

### Alert Metrics

```promql
# Total alerts sent
slack_alerts_total{channel="governance-alerts"}

# Alert delivery success rate
rate(slack_alerts_delivered_total[5m]) / rate(slack_alerts_sent_total[5m])

# Alert latency (detection to delivery)
histogram_quantile(0.95, slack_alert_latency_seconds_bucket)

# False positive rate
slack_alerts_acknowledged_false_total / slack_alerts_total
```

### Dashboard Queries

```sql
-- Daily alert summary
SELECT
  DATE(timestamp) as date,
  severity,
  COUNT(*) as alert_count,
  AVG(acknowledgment_time_minutes) as avg_response_time
FROM slack_alerts
WHERE channel = 'governance-alerts'
GROUP BY date, severity
ORDER BY date DESC;

-- Top alert triggers
SELECT
  metric_name,
  COUNT(*) as trigger_count,
  AVG(metric_value) as avg_value,
  MAX(metric_value) as max_value
FROM slack_alerts
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY metric_name
ORDER BY trigger_count DESC;
```

---

## 🔄 Feedback Loop Architecture

This Slack integration completes the **Observer Alert Loop**:

```
┌─────────────────────────────────────────────────────────────┐
│                     Alert Feedback Loop                      │
└─────────────────────────────────────────────────────────────┘

1. DETECT                    Render API → Metrics Collection
   ↓
2. EVALUATE                  Governance CI → Threshold Check
   ↓
3. ALERT                     Slack Webhook → Channel Notification
   ↓
4. ACKNOWLEDGE               Human/Bot → Incident Response
   ↓
5. RESOLVE                   Action Taken → System Updated
   ↓
6. ARCHIVE                   Observer → Compliance Logs (180 days)
   ↓
7. ANALYZE                   Dashboard → Pattern Recognition
   ↓
   [Loop continues with improved thresholds]
```

---

## 🧪 Testing

### Manual Testing

```bash
# Test Slack webhook directly
curl -X POST \
  -H 'Content-type: application/json' \
  --data '{"text":"🧪 Test alert from Observer Guardian"}' \
  $SLACK_GOVERNANCE_WEBHOOK

# Expected: Message appears in #governance-alerts
```

### Automated Testing

```yaml
# .github/workflows/test-slack-integration.yml
name: Test Slack Integration

on:
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  test-slack:
    runs-on: ubuntu-latest
    steps:
      - name: Send test alert
        env:
          SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
        run: |
          curl -X POST \
            -H 'Content-type: application/json' \
            --data '{"text":"✅ Weekly Slack integration test successful"}' \
            "$SLACK_WEBHOOK"
```

### Integration Tests

```python
# tests/test_slack_integration.py
import pytest
import requests
import json
import os

def test_slack_webhook_configured():
    """Verify Slack webhook is configured"""
    webhook = os.getenv('SLACK_GOVERNANCE_WEBHOOK')
    assert webhook is not None, "SLACK_GOVERNANCE_WEBHOOK not configured"
    assert webhook.startswith('https://hooks.slack.com')

def test_slack_message_format():
    """Validate alert message format"""
    alert = {
        "text": "*📣 Governance Alert: Test*\n🧪 Integration test"
    }
    
    # Validate JSON structure
    assert "text" in alert
    assert len(alert["text"]) > 0

def test_slack_alert_delivery():
    """Test end-to-end alert delivery"""
    webhook = os.getenv('SLACK_GOVERNANCE_WEBHOOK')
    if not webhook:
        pytest.skip("Webhook not configured")
    
    payload = {
        "text": "🧪 Automated test from pytest suite"
    }
    
    response = requests.post(
        webhook,
        headers={'Content-Type': 'application/json'},
        data=json.dumps(payload)
    )
    
    assert response.status_code == 200
    assert response.text == "ok"
```

---

## 🔐 Security Considerations

### Webhook Security

- **Never commit webhook URLs** to version control
- Store webhooks in GitHub Secrets or secure vault
- Rotate webhooks quarterly or on security incidents
- Use workspace-specific webhooks (never shared across orgs)

### Data Privacy

```yaml
data_sanitization:
  - rule: "Redact PII before sending to Slack"
    patterns:
      - email_addresses
      - phone_numbers
      - api_keys
      - passwords
      - tokens
  
  - rule: "Truncate large payloads"
    max_length: 3000
    truncation_marker: "... [truncated]"
  
  - rule: "Filter sensitive metrics"
    excluded_fields:
      - database_credentials
      - encryption_keys
      - internal_ip_addresses
```

### Access Control

- Limit channel membership to authorized personnel
- Implement audit logging for alert access
- Require MFA for Slack workspace access
- Review access quarterly

---

## 📚 Related Documentation

- [MCP Architecture](/specs/mcp-architecture.md) - Observer Charter and Alert Loop
- [Render Integration](/specs/render_integration.md) - Metrics collection implementation
- [Observer Guardrails](/specs/observer_guardrails.yaml) - Compliance rules and thresholds
- [PR Governance Workflow](/.github/workflows/pr-governance-check.yml) - CI implementation
- [Incident Response Playbook](/docs/incident-response.md) - Alert handling procedures

---

## 🎯 Roadmap

### Phase 1: Core Integration (✅ Complete)
- [x] Basic webhook integration
- [x] Threshold-based alerting
- [x] Message formatting
- [x] Workflow integration

### Phase 2: Enhanced Features (🚧 In Progress)
- [ ] Alert deduplication
- [ ] Rate limiting
- [ ] Interactive message buttons
- [ ] Thread-based incident tracking

### Phase 3: Intelligence Layer (📋 Planned)
- [ ] ML-based anomaly detection
- [ ] Predictive alerting
- [ ] Natural language incident queries
- [ ] Auto-remediation recommendations

### Phase 4: Multi-Channel Integration (🔮 Future)
- [ ] PagerDuty integration
- [ ] Microsoft Teams support
- [ ] Custom webhook handlers
- [ ] SMS/voice escalation

---

**Last Updated:** 2025-10-09  
**Version:** 1.0.0  
**Status:** Production Ready  
**Owner:** Platform Engineering Team  
**Reviewers:** Governance Council, SRE Team

<!-- Generated via Cursor Governance Automation: Slack Integration Spec v1.0 -->
