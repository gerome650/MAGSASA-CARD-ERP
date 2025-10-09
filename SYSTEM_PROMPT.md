# 🧭 MAGSASA-CARD / AI Studio — System Anchor

This repository is governed by a **Standard Mission Anchor** to ensure consistent architecture, governance, and strategy alignment across all development pods.

## 🚀 Core Dev Flow (Non-Negotiable)

```
🧠 Manus (Builder)
↓
🧑‍⚖️ Cursor (Reviewer)
↓
💻 Terminal (Operator)
↓
☁️ GitHub (Version Control)
↓
🛰️ Render (Deployment + Observability)
```

- All features are spec-first and must follow this pipeline.
- Governance is enforced through PR templates and automated checks.
- **No bypassing the Observer Charter** — all deployments must align with guardrails.

---

## 🧑‍⚖️ Observer Charter Integration

- Observer is the **governance backbone** of the AI Studio.  
- Monitors **uptime**, **drift %**, and **latency**.  
- Feeds results into **PR Governance Summary** and **Slack alerts**.  
- **All pods** (e.g., `KWENTO+`) inherit the same governance structure.

### 📊 Guardrail Baselines
| Metric         | Target / Threshold          | Enforcement Layer             |
|----------------|------------------------------|-------------------------------|
| Uptime         | 99.5%                         | Render + Observer             |
| Latency        | ≤ 2500ms                      | Observer Guardrails           |
| Drift          | ≤ 3%                          | QA Consistency Checker        |
| Coverage       | ≥ 85%                         | Governance CI / QA Scripts    |
| Retention      | 180 days (audit logs)         | Observer Charter              |

---

## 📜 Spec-First Policy

- Every major feature must include a spec in `/specs/`.
- Specs are enforced via governance checks (`pr-governance-check.yml`).
- Changes without corresponding spec updates will be flagged by QA.

---

## 🚨 Alert-Driven Governance

- Observer integrates with **Render Metrics** and **Slack alerts**.  
- Any drift or threshold violation:
  - Triggers QA Consistency Checker
  - Posts alert to `#governance-alerts`
  - Logs in Observer
- Alerts can escalate to governance council levels (tiered response).

---

## 🧩 Multi-Pod AI Studio

- MAGSASA-CARD is the **anchor pod**.  
- All other pods (e.g., KWENTO+) must:
  - Use the same governance template
  - Integrate Observer guardrails
  - Deploy through Render
  - Follow spec-first + pipeline rules.

---

## 🛡️ Re-Anchoring Shortcut

If context or strategy ever drifts:

```
Re-anchor to MAGSASA-CARD plan
```

→ Resets operational context to this anchor (for both Cursor and AI Agents).

---

## 🧭 Key Reference Files

- `specs/mcp-architecture.md` → Observer & Alert Loop Charter  
- `specs/observer_guardrails.yaml` → Governance thresholds  
- `specs/render_integration.md` → Render integration  
- `specs/slack_integration.md` → Slack alerting layer  
- `.github/workflows/pr-governance-check.yml` → CI/CD governance  
- `scripts/qa/obs_governance_consistency.py` → QA drift checks

---

## 👥 Team Reminder

> This is not just a repo.  
> It's the **anchor pod** for the entire AI Studio ecosystem.  
> Every PR, every commit, and every deployment flows through governance.

---

_© 2025 MAGSASA-CARD AI Studio | Governance-Driven Engineering_

