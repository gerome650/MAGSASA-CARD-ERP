# Slack Integration Specification

**Document Path:** `/specs/slack_integration.md`  
**Linked Components:**  
- Render Integration → `/specs/render_integration.md`  
- Observer Guardrails → `/specs/observer_guardrails.yaml`  
- Governance Workflow → `.github/workflows/pr-governance-check.yml`

---

## 🧭 Purpose

This Slack integration adds a **real-time alerting layer** for governance compliance failures.  
When uptime, latency, or drift exceed thresholds, a structured message is sent to designated Slack channels.

---

## ⚙️ Configuration Specification

```yaml
slack_integration:
  webhook_url: "${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}"
  channels:
    - "#governance-alerts"
    - "#observer-notifications"
  conditions:
    - metric: uptime_percent
      fail_below: 98.0
      message: "🚨 Render uptime below 98%! Immediate investigation required."
    - metric: latency_ms
      fail_above: 4000
      message: "⚠️ Latency exceeds 4000ms. Possible API degradation."
    - metric: drift_percent
      fail_above: 5
      message: "🧭 Spec drift above 5%! Observer charter intervention triggered."
  alert_format: |
    *📣 Governance Alert: ${{ metric_name }} threshold breached*
    > Metric: `${{ metric_name }}`
    > Value: `${{ metric_value }}`
    > Threshold: `${{ threshold }}`
    > Action: `${{ message }}`
```

---

## 🧠 Example Slack Message

```markdown
📣 *Governance Alert: Threshold Breach Detected*
🚨 Render uptime below 98%! Current: 96.5%
🧭 Spec drift above 5%! Current: 6.3%
```

---

## ✅ Success Criteria

* Alerts appear in `#governance-alerts`
* Render breaches trigger Slack messages
* Observer uses these to update compliance dashboards

---

## 📊 Alert Flow

```plaintext
┌──────────────────┐
│  Render Metrics  │
│   Collection     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Threshold       │
│  Evaluation      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Slack Webhook   │
│  Notification    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Observer        │
│  Dashboard       │
└──────────────────┘
```

---

## 🔧 Implementation

### GitHub Actions Integration

The Slack notification step is implemented in `.github/workflows/pr-governance-check.yml` as part of the `render-metrics-collector` job:

```yaml
- name: Send Slack Alerts (on threshold breach)
  if: always()
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_GOVERNANCE_WEBHOOK }}
  run: |
    echo "🔔 Evaluating metrics for Slack alert..."
    UPTIME=$(jq '.system.uptime' render_metrics.json)
    LATENCY=$(jq '.performance.latency_avg' render_metrics.json)
    DRIFT=$(jq '.observer.spec_drift' render_metrics.json)
    
    ALERT=""
    
    if (( $(echo "$UPTIME < 98.0" | bc -l) )); then
      ALERT+="🚨 Render uptime below 98%! Current: $UPTIME%\n"
    fi
    
    if (( $(echo "$LATENCY > 4000" | bc -l) )); then
      ALERT+="⚠️ Latency exceeds 4000ms. Current: ${LATENCY}ms\n"
    fi
    
    if (( $(echo "$DRIFT > 5" | bc -l) )); then
      ALERT+="🧭 Spec drift above 5%! Current: ${DRIFT}%\n"
    fi
    
    if [ -n "$ALERT" ]; then
      echo "📣 Sending Slack alert..."
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\": \"*Governance Alert: Threshold Breach Detected*\n$ALERT\"}" \
        "$SLACK_WEBHOOK"
    else
      echo "✅ No threshold breaches detected."
    fi
```

### Required Secrets

Add the following secret to your GitHub repository:

- `SLACK_GOVERNANCE_WEBHOOK`: Slack webhook URL for governance alerts

---

## 🎯 Metrics Monitored

| Metric | Threshold | Severity | Action |
|--------|-----------|----------|--------|
| **Uptime** | < 98% | Critical | Immediate investigation |
| **Latency** | > 4000ms | High | Performance review |
| **Spec Drift** | > 5% | Medium | Observer intervention |

---

## 📈 Escalation Path

```plaintext
Threshold Breach
       ↓
Slack Alert (#governance-alerts)
       ↓
Observer Dashboard Update
       ↓
[if Critical] → PagerDuty Escalation
       ↓
[if Unresolved] → Governance Council Review
```

---

## 🧪 Testing

To test the Slack integration:

1. Set the `SLACK_GOVERNANCE_WEBHOOK` secret in your repository
2. Create a test PR
3. Manually trigger the governance workflow
4. Verify alert appears in designated Slack channel

---

## 🔄 Retention Policy

- Alerts are logged for **180 days** (per Observer Guardrails retention policy)
- Critical alerts are archived permanently
- Metrics data is retained for **90 days**

---

## 📚 Related Documentation

- [Render Integration Spec](/specs/render_integration.md)
- [Observer Guardrails](/specs/observer_guardrails.yaml)
- [MCP Architecture](/specs/mcp-architecture.md)
- [Governance Workflow](/.github/workflows/pr-governance-check.yml)

---

<!-- Generated via Cursor Governance Automation: Observer Loop Integration v1.0 -->

