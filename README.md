# Stage 6.6 — Continuous Chaos, Auto-Remediation, DR, and CI/CD Enforcement
**Scope**
- Continuous chaos automation (cron + CI)
- Auto-remediation engine (rules + guardrails)
- Disaster recovery (DR) simulations + runbook generation
- CI/CD enforcement (block on SLO regressions / chaos failures)
**Local usage**
make setup
make lint
make validate
make opa-test
**Docs protocol (repo-first)**
- docs/ (ADRs, roadmap)
- ops/runbooks/ (generated)
- configs/ (scenarios, SLOs, rules, DR plans)
