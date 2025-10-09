# 🧭 Governance Branch Protection Rules Checklist

This checklist defines the **multi-layered governance mesh** for the repo.  
Apply these settings under **GitHub → Settings → Branch Protection Rules**.

---

### 🪜 1. General Configuration
- [ ] Protect the `main` branch
- [ ] Require pull requests before merging
- [ ] Disallow direct pushes to `main`
- [ ] Require linear history (optional but recommended)

---

### 🧪 2. Automated Validation Enforcement
- [ ] ✅ Enable **"Require status checks to pass before merging"**
- [ ] Select:
  - `QA Consistency Checker`
  - `PR Governance Validation`
  - `Render Metrics Collector`
- [ ] ✅ Enable **"Require branches to be up to date before merging"**
- [ ] Optionally enforce `test` or `build` checks if CI includes them

---

### 🧑‍⚖️ 3. CODEOWNERS Enforcement
- [ ] ✅ Enable **"Require review from Code Owners"**
- [ ] Governance team must review:
  - `.github/workflows/pr-governance-check.yml`
  - `observer_guardrails.yaml`
  - `render_integration.md`
  - `slack_integration.md`
  - `mcp-architecture.md`
  - `SYSTEM_PROMPT.md`
  - `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Set minimum required approvals to `1` (or more)

---

### 🛡️ 4. Security & Infra Guardrails
- [ ] ✅ Enable "Include administrators"
- [ ] ✅ Enable "Restrict who can push to matching branches"
- [ ] Only allow pushes from:
  - GitHub Actions
  - Authorized maintainers

- [ ] (Optional) Enable "Require signed commits"
- [ ] (Optional) Enable "Require conversation resolution before merging"

---

### 🧠 5. Observer & Alert Loop Alignment
- [ ] Confirm Slack alerts are configured for uptime, drift, and threshold violations
- [ ] Confirm Observer dashboard integration is live
- [ ] Confirm 180-day audit retention for alert logs
- [ ] Confirm escalation loop:

```
Render → Governance CI → Slack Alert → Observer → Governance Team
```

---

### 🪙 6. Periodic Governance Review
- [ ] Review branch protection settings every 90 days
- [ ] Run QA Consistency Checker manually on critical branches
- [ ] Update CODEOWNERS if governance team changes
- [ ] Audit Slack alerts and Observer reports

---

## 🧭 Purpose
This checklist ensures a **triple lock**:
- 🧪 Automated validation  
- 👥 Human governance review  
- 🏗 Infrastructure enforcement

Apply these rules to `main` and optionally mirror them for `dev` or `staging`.

---

✅ Once this file is created, the `README.md` will contain:

```
👉 Branch Protection Checklist: See GOVERNANCE_BRANCH_PROTECTION_CHECKLIST.md
```

This pins governance hardening **next to your SYSTEM_PROMPT anchor** for full visibility.

