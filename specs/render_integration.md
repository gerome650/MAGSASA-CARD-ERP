# Render Integration Specification
**Document Path:** /specs/render_integration.md  
**Linked Components:**  
- Observer Charter → `/specs/mcp-architecture.md`  
- Observer Guardrails → `/specs/observer_guardrails.yaml`  
- Governance Workflow → `.github/workflows/pr-governance-check.yml`

---

## 🧭 Purpose
The Render Integration bridges **live Render telemetry** into **GitHub PR comments**, giving reviewers real-time insight into uptime, latency, and spec drift during governance validation.

---

## ⚙️ Architecture Overview
```plaintext
[Render Service] → [Observer Telemetry Feed] → [Governance Metrics Collector] 
     ↓                            ↓                          ↓
  uptime, latency, drift      API payload (JSON)         PR Comment Composer
```

---

## 📡 API Integration Specification

```yaml
render_integration:
  endpoints:
    base_url: "https://api.render.com/v1"
    metrics_endpoint: "/services/{{ service_id }}/metrics"
    deploy_endpoint: "/services/{{ service_id }}/deploys/latest"
  authentication:
    type: "api_key"
    env_var: "RENDER_API_KEY"
  poll_interval_minutes: 10
  metrics_mapping:
    uptime_percent: "system.uptime"
    latency_ms: "performance.latency_avg"
    drift_percent: "observer.spec_drift"
  thresholds:
    uptime_percent:
      warn_below: 99.0
      fail_below: 98.0
    latency_ms:
      warn_above: 2500
      fail_above: 4000
    drift_percent:
      warn_above: 2
      fail_above: 5
```

---

## 🧠 PR Comment Example

```markdown
## 🧑‍⚖️ Governance Validation Summary

| Metric | Status | Threshold | Live Value |
|--------|--------|------------|-------------|
| Uptime | ✅ | > 99% | 99.8% |
| Latency | ⚠️ | < 2500ms | 2800ms |
| Drift | ✅ | < 2% | 1.5% |

🧠 *Metrics auto-fetched from Render at 2025-10-09 08:21 UTC*
```

---

## 🔐 Security

Use GitHub secrets for:
- `RENDER_API_KEY`
- `RENDER_SERVICE_ID`

Data is read-only, pulled during workflow runtime

---

## ✅ Success Criteria

- PRs show live metrics inside governance comments
- Drift alerts trigger warnings when >2%
- Uptime below 98% marks PR as non-compliant

---

<!-- Generated via Cursor Governance Automation: Render Metrics v1.0 -->

