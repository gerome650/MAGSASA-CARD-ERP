# 🎯 CI/CD Cheat Sheet - MAGSASA-CARD-ERP

---

## 🚀 Daily Development Commands

```bash
┌─────────────────────────────────────────────────────────┐
│  BEFORE YOU CODE                                        │
├─────────────────────────────────────────────────────────┤
│  make setup              # First-time setup             │
│  git pull origin main    # Get latest changes           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  WHILE CODING                                           │
├─────────────────────────────────────────────────────────┤
│  make format             # Auto-format (Black + Ruff)   │
│  make lint               # Check style                  │
│  make quick-test         # Fast test run                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  BEFORE COMMIT                                          │
├─────────────────────────────────────────────────────────┤
│  make preflight-quick    # Quick validation             │
│  make test               # Full test with coverage      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  BEFORE PUSH                                            │
├─────────────────────────────────────────────────────────┤
│  make security-scan      # Security audit               │
│  make verify-ci          # Final verification           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  CHECK CI HEALTH                                        │
├─────────────────────────────────────────────────────────┤
│  make ci-health          # Generate report              │
│  cat reports/ci_health.md # View report                 │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 CI Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                     TRIGGER                             │
│              (Push or Pull Request)                     │
└────────────────────┬────────────────────────────────────┘
                     │
     ┌───────────────┴───────────────┐
     │   PARALLEL EXECUTION (Fast)    │
     ├────────────────────────────────┤
     │  ✓ lint-and-format  (15 min)  │
     │  ✓ test             (30 min)  │
     │  ✓ security-scan    (15 min)  │
     └───────────────┬────────────────┘
                     │
     ┌───────────────┴───────────────┐
     │   VALIDATION & INTEGRATION     │
     ├────────────────────────────────┤
     │  ✓ mcp-dry-run      (20 min)  │
     │  ✓ readiness-gate   (10 min)  │
     │  ✓ pr-comment       (5 min)   │
     └───────────────┬────────────────┘
                     │
     ┌───────────────┴───────────────┐
     │   BUILD & FINAL VERIFICATION   │
     ├────────────────────────────────┤
     │  ✓ build            (15 min)  │
     │  ✓ verify_pipeline  (10 min)  │
     └───────────────┬────────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │  READINESS CHECK  │
          ├──────────────────┤
          │   ≥90%?          │
          └────┬─────────┬───┘
               │         │
           ✅ YES    ❌ NO
               │         │
               │    (BLOCK MERGE)
               │
     ┌─────────┴──────────────────┐
     │  POST-MERGE (Main Only)    │
     ├────────────────────────────┤
     │  ✓ staging-smoke-test      │
     │  ✓ (optional) auto-tag     │
     └────────────────────────────┘
```

---

## 🎯 Readiness Score Matrix

```
┌──────────┬─────────────────┬────────────────────────┐
│  Score   │  Status         │  Action                │
├──────────┼─────────────────┼────────────────────────┤
│  ≥95%    │  🟢 EXCELLENT   │  Auto-tag + Deploy     │
│  90-94%  │  🟡 GOOD        │  Merge + Stage         │
│  80-89%  │  🟠 WARNING     │  Review + Fix          │
│  <80%    │  🔴 CRITICAL    │  Block + Fix Now       │
└──────────┴─────────────────┴────────────────────────┘
```

---

## 🛡️ Security Checklist

```bash
┌─────────────────────────────────────────────────────────┐
│  SECURITY SCANNING                                      │
├─────────────────────────────────────────────────────────┤
│  make security-scan                                     │
│                                                         │
│  Runs:                                                  │
│  ✓ Bandit (Python code security)                       │
│  ✓ pip-audit (vulnerability scanning)                  │
│  ✓ pip check (dependency conflicts)                    │
│                                                         │
│  Config: .bandit                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Retry & Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│  AUTOMATIC RETRIES                                      │
├─────────────────────────────────────────────────────────┤
│  • Job Level:   3 attempts with 5s delay               │
│  • Test Level:  2 retries with 1s delay                │
│  • Installs:    3 attempts with backoff                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  CACHING (30-50% SPEED BOOST)                           │
├─────────────────────────────────────────────────────────┤
│  • UV packages:  ~/.cache/uv                            │
│  • Pip packages: ~/.cache/pip                           │
│  • Build files:  dist/, build/                          │
└─────────────────────────────────────────────────────────┘
```

---

## 📈 Monitoring & Reports

```
┌─────────────────────────────────────────────────────────┐
│  DAILY AUTOMATED REPORTS                                │
├─────────────────────────────────────────────────────────┤
│  Schedule:  09:00 UTC daily                             │
│  Location:  reports/ci_health.md                        │
│  Format:    JSON + Markdown                             │
│                                                         │
│  Metrics:                                               │
│  • Success rate (target: ≥95%)                          │
│  • Average duration                                     │
│  • Top failures                                         │
│  • Trend analysis                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PR COMMENTS (Automatic)                                │
├─────────────────────────────────────────────────────────┤
│  Every PR gets:                                         │
│  • Current readiness score                              │
│  • Pass/fail by category                                │
│  • Coverage report                                      │
│  • Merge approval status                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing Commands

```bash
┌─────────────────────────────────────────────────────────┐
│  TEST EXECUTION                                         │
├─────────────────────────────────────────────────────────┤
│  make test              # Full test suite + coverage    │
│  make quick-test        # Fast run, no coverage         │
│                                                         │
│  # Specific tests                                       │
│  pytest tests/test_name.py -v                           │
│                                                         │
│  # With coverage                                        │
│  pytest --cov=packages --cov-report=html                │
│                                                         │
│  # Skip flaky tests                                     │
│  pytest -m "not flaky"                                  │
│                                                         │
│  # Parallel execution                                   │
│  pytest -n=auto                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Artifact Locations

```
┌─────────────────────────────────────────────────────────┐
│  LOCAL FILES                                            │
├─────────────────────────────────────────────────────────┤
│  reports/ci_health.md      - Daily CI health report     │
│  reports/ci_health.json    - Machine-readable data      │
│  htmlcov/index.html        - Coverage report            │
│  coverage.xml              - Codecov upload             │
│  dist/                     - Built packages             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  GITHUB ARTIFACTS                                       │
├─────────────────────────────────────────────────────────┤
│  dist-packages          - 90 days retention             │
│  security-report        - 30 days retention             │
│  verification-report    - 7 days retention              │
│  ci-health-report       - 30 days retention             │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

```bash
┌─────────────────────────────────────────────────────────┐
│  PROBLEM: Tests failing locally                         │
├─────────────────────────────────────────────────────────┤
│  make clean                                             │
│  make setup                                             │
│  make test                                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PROBLEM: Linting errors                                │
├─────────────────────────────────────────────────────────┤
│  make format        # Auto-fix                          │
│  make lint          # Check again                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PROBLEM: Security warnings                             │
├─────────────────────────────────────────────────────────┤
│  make security-scan                                     │
│  pip list --outdated                                    │
│  pip install --upgrade <package>                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PROBLEM: CI failing, not sure why                      │
├─────────────────────────────────────────────────────────┤
│  make verify-ci     # Run same checks locally           │
│  Check: https://github.com/[repo]/actions               │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 PR Workflow

```
1. CREATE BRANCH
   git checkout -b feature/my-feature

2. WRITE CODE
   # Code, code, code...

3. FORMAT & LINT
   make format
   make lint

4. TEST
   make test

5. SECURITY
   make security-scan

6. FINAL CHECK
   make verify-ci

7. COMMIT & PUSH
   git add .
   git commit -m "feat: my awesome feature"
   git push origin feature/my-feature

8. CREATE PR
   # GitHub will auto-run CI
   # Bot will comment with readiness score

9. WAIT FOR CI
   # All jobs must pass
   # Readiness must be ≥90%

10. MERGE
    # If approved, merge to main
    # Staging smoke tests run automatically
```

---

## 🔔 Notification Setup (Optional)

```bash
┌─────────────────────────────────────────────────────────┐
│  SLACK INTEGRATION                                      │
├─────────────────────────────────────────────────────────┤
│  1. Create webhook at:                                  │
│     https://api.slack.com/messaging/webhooks            │
│                                                         │
│  2. Add to GitHub secrets:                              │
│     Settings → Secrets → New secret                     │
│     Name: SLACK_WEBHOOK_URL                             │
│     Value: <your webhook URL>                           │
│                                                         │
│  3. Notifications auto-enabled for:                     │
│     • Daily CI health (09:00 UTC)                       │
│     • Critical failures (success <85%)                  │
│     • Staging deployments                               │
│     • New releases (if auto-tag enabled)                │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Key Metrics to Track

```
┌─────────────────────────────────────────────────────────┐
│  DAILY MONITORING                                       │
├─────────────────────────────────────────────────────────┤
│  ✓ CI Success Rate        → Target: ≥95%               │
│  ✓ Average Build Time     → Target: <8 min             │
│  ✓ Test Coverage          → Target: ≥80%               │
│  ✓ Security Issues        → Target: 0 critical         │
│  ✓ Readiness Score        → Target: ≥95%               │
│  ✓ Flaky Test Rate        → Target: <5%                │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Quick Documentation Links

```
┌──────────────────────────────────────┬──────────────────┐
│  Document                            │  Purpose         │
├──────────────────────────────────────┼──────────────────┤
│  CI_QUICK_START.md                   │  2-min guide     │
│  CI_CD_IMPLEMENTATION_COMPLETE.md    │  Full details    │
│  CI_CD_QUICK_REFERENCE.md            │  Quick ref       │
│  CI_CD_CHEAT_SHEET.md (this file)    │  Cheat sheet     │
│  CI_AUTO_RELEASE_TAGGING.md          │  Auto-tagging    │
└──────────────────────────────────────┴──────────────────┘
```

---

## 💡 Pro Tips

```
1. ⚡ CACHE IS YOUR FRIEND
   First run: ~12 min, Cached: ~6 min

2. 🧪 TEST LOCALLY FIRST
   Catch issues before CI: make verify-ci

3. 📊 CHECK REPORTS DAILY
   Spot trends early: cat reports/ci_health.md

4. 🔒 SECURITY FIRST
   Run scans often: make security-scan

5. 🎯 AIM FOR 95%+
   Excellence is the target, 90% is minimum

6. 🔄 EMBRACE RETRIES
   Flaky tests? They'll retry automatically

7. 📈 MONITOR TRENDS
   Watch success rate, not just latest run

8. 🚀 AUTOMATE EVERYTHING
   Less manual work = more coding time
```

---

## 🆘 Emergency Contacts

```
┌─────────────────────────────────────────────────────────┐
│  IF CI IS BROKEN                                        │
├─────────────────────────────────────────────────────────┤
│  1. Check GitHub Actions: [repo]/actions                │
│  2. View logs for failed job                            │
│  3. Reproduce locally: make verify-ci                   │
│  4. Check recent commits                                │
│  5. Review ci_health.md for patterns                    │
│  6. Escalate if success rate <85%                       │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Remember

```
✓ Format before commit
✓ Test before push
✓ Scan for security
✓ Verify full CI locally
✓ Check reports daily
✓ Aim for ≥95% readiness
✓ Monitor trends, not just snapshots
✓ Trust the automation
```

---

**Print this page for your desk!** 📄

**Need more details?** → `CI_QUICK_START.md`

**Full implementation?** → `CI_CD_IMPLEMENTATION_COMPLETE.md`

