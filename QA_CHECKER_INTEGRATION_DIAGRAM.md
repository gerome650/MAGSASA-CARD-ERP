# 🧪 QA Consistency Checker - System Integration Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GitHub Pull Request                                │
│                     (modifies observability files)                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│              🧑‍⚖️ PR Governance Validation Workflow                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │  Job 1           │  │  Job 2           │  │  Job 3           │         │
│  │  Spec Reference  │  │  Duplicate Tests │  │  Dir Structure   │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │  Job 4           │  │  Job 5           │  │  Job 6           │         │
│  │  Secrets Scan    │  │  Coverage        │  │  Ruff Linting    │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    🧪 NEW: Job 9                                      │ │
│  │            QA Observability & Governance Consistency                  │ │
│  │                                                                       │ │
│  │  Watches:                                                             │ │
│  │  • specs/observer_guardrails.yaml                                     │ │
│  │  • specs/render_integration.md                                        │ │
│  │  • specs/slack_integration.md                                         │ │
│  │  • specs/mcp-architecture.md                                          │ │
│  │  • .github/workflows/pr-governance-check.yml                          │ │
│  │                                                                       │ │
│  │  Runs:                                                                │ │
│  │  scripts/qa/obs_governance_consistency.py                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌──────────────────┐                                                      │
│  │  Job 7           │  ◄── Depends on all above jobs (including Job 9)    │
│  │  Governance      │                                                      │
│  │  Summary         │                                                      │
│  └──────────────────┘                                                      │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                      │
│  │  Job 8           │                                                      │
│  │  Render Metrics  │                                                      │
│  │  Collector       │                                                      │
│  └──────────────────┘                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## QA Checker Detailed Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    scripts/qa/obs_governance_consistency.py                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Get PR Base/Head SHAs  │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │ Detect Changed Files   │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │ Match Against          │
                    │ WATCH_FILES List       │
                    └────────┬───────────────┘
                             │
                 ┌───────────┴───────────┐
                 │   No Match            │   Match Found
                 ▼                       ▼
        ┌─────────────────┐     ┌──────────────────────┐
        │ Skip Checks     │     │ Run All Validations  │
        │ (Exit Success)  │     └──────────┬───────────┘
        └─────────────────┘                │
                                           │
                              ┌────────────┴────────────┐
                              │                         │
                    ┌─────────▼────────┐    ┌──────────▼──────────┐
                    │  1. YAML         │    │  4. Observer        │
                    │     Validity     │    │     Charter Sync    │
                    └──────────────────┘    └─────────────────────┘
                              │                         │
                    ┌─────────▼────────┐    ┌──────────▼──────────┐
                    │  2. Threshold    │    │  5. Guardrails      │
                    │     Consistency  │    │     Alignment       │
                    └──────────────────┘    └─────────────────────┘
                              │                         │
                    ┌─────────▼────────┐                │
                    │  3. Secrets      │                │
                    │     Presence     │                │
                    └──────────────────┘                │
                              │                         │
                              └────────────┬────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │ Collect Errors &        │
                              │ Warnings                │
                              └────────────┬────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
          ┌─────────▼─────────┐                        ┌─────────▼─────────┐
          │ Generate JSON     │                        │ Generate Markdown │
          │ (stdout)          │                        │ (qa_summary.md)   │
          └───────────────────┘                        └───────────────────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                              ┌────────────▼────────────┐
                              │ Exit Code:              │
                              │  0 = Pass (warnings OK) │
                              │  1 = Fail (errors)      │
                              └─────────────────────────┘
```

## Check Categories Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          5 Check Categories                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 1. YAML Validity ✅                                              │
├──────────────────────────────────────────────────────────────────┤
│ • Parse specs/observer_guardrails.yaml                           │
│ • Verify required keys exist                                     │
│ • Validate structure                                             │
│                                                                  │
│ Status: ERROR if missing or invalid                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 2. Threshold Consistency 🎯                                      │
├──────────────────────────────────────────────────────────────────┤
│ Check 6 Thresholds Across 3 Files:                              │
│                                                                  │
│ ┌────────────────┬──────────┬─────────────────────────┐         │
│ │ Threshold      │ Expected │ Files Checked           │         │
│ ├────────────────┼──────────┼─────────────────────────┤         │
│ │ uptime_warn    │ 99.0%    │ guardrails, render, wf  │         │
│ │ uptime_fail    │ 98.0%    │ guardrails, render, wf  │         │
│ │ latency_warn   │ 2500ms   │ guardrails, render      │         │
│ │ latency_fail   │ 4000ms   │ guardrails, render, wf  │         │
│ │ drift_warn     │ 2%       │ guardrails              │         │
│ │ drift_fail     │ 5%       │ guardrails, wf          │         │
│ └────────────────┴──────────┴─────────────────────────┘         │
│                                                                  │
│ Status: ERROR if mismatch, WARNING if missing                    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 3. Secrets Presence 🔐                                           │
├──────────────────────────────────────────────────────────────────┤
│ Verify 3 Required Secrets:                                       │
│ • secrets.RENDER_API_KEY                                         │
│ • secrets.RENDER_SERVICE_ID                                      │
│ • secrets.SLACK_GOVERNANCE_WEBHOOK                               │
│                                                                  │
│ Check:                                                           │
│ • Referenced in pr-governance-check.yml                          │
│ • Documented in relevant spec files                              │
│                                                                  │
│ Status: WARNING if undocumented                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 4. Observer Charter Sync 📋                                      │
├──────────────────────────────────────────────────────────────────┤
│ Validate specs/mcp-architecture.md contains:                     │
│                                                                  │
│ Required Elements:                                               │
│  1. Alert Loop (section/diagram)                                 │
│  2. Render (component)                                           │
│  3. Governance (component)                                       │
│  4. Slack (component)                                            │
│  5. Observer (component)                                         │
│                                                                  │
│ Status: WARNING if missing elements                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ 5. Guardrails Alignment 🛡️                                       │
├──────────────────────────────────────────────────────────────────┤
│ Verify in specs/observer_guardrails.yaml:                        │
│                                                                  │
│ • audit_trail_retention_days ≥ 180                               │
│ • min_coverage_percent ≥ 85                                      │
│                                                                  │
│ Status: WARNING if below threshold                               │
└──────────────────────────────────────────────────────────────────┘
```

## Output Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            QA Check Outputs                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┐      ┌──────────────────────────────────┐
│  JSON (stdout)                 │      │  Markdown (qa_summary.md)        │
│  ────────────────              │      │  ─────────────────────           │
│  {                             │      │  ## 🧪 QA Consistency Report     │
│    "status": "pass|fail",      │      │                                  │
│    "errors": [                 │      │  **Status:** ✅ PASSED           │
│      {                         │      │                                  │
│        "check": "...",         │      │  **Summary:**                    │
│        "status": "error",      │      │  - Errors: 0                     │
│        "message": "...",       │      │  - Warnings: 0                   │
│        "remediation": "..."    │      │  - Files Checked: 2              │
│      }                         │      │                                  │
│    ],                          │      │  ### Check Results               │
│    "warnings": [...],          │      │                                  │
│    "files_checked": [...]      │      │  | Check | Status | Message |    │
│  }                             │      │  |-------|--------|---------|    │
└────────────┬───────────────────┘      │  | ...   | ✅     | ...     |    │
             │                          └──────────┬───────────────────────┘
             │                                     │
             └────────────┬────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────────┐
         │  GitHub Actions Step: qa_check         │
         │  ────────────────────────────           │
         │  • Captures exit code                  │
         │  • Sets output: qa_failed=true/false   │
         │  • Continues on error                  │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  Sticky PR Comment                     │
         │  (marocchino/sticky-pull-request...)   │
         │  ────────────────────────────           │
         │  Header: "QA Consistency Report"       │
         │  Path: qa_summary.md                   │
         │                                        │
         │  • Updates same comment on each run    │
         │  • Always runs (even on failure)       │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │  Final Job Step                        │
         │  ────────────────────                  │
         │  if: qa_failed == 'true'               │
         │    exit 1  (fail the job)              │
         └────────────────────────────────────────┘
```

## Governance Summary Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Job 7: Governance Summary                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  needs:                                                                     │
│    - spec-reference-check                                                   │
│    - duplicate-test-check                                                   │
│    - directory-structure-check                                              │
│    - secrets-scanning                                                       │
│    - coverage-enforcement                                                   │
│    - ruff-linting                                                           │
│    - qa-observability-consistency  ◄── NEW                                  │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Generates Summary Table:                                             │ │
│  │                                                                       │ │
│  │  | Check                | Result |                                    │ │
│  │  |----------------------|--------|                                    │ │
│  │  | 📋 Spec Reference    | ✅     |                                    │ │
│  │  | 🔍 Duplicate Tests   | ✅     |                                    │ │
│  │  | 📁 Directory Struct  | ✅     |                                    │ │
│  │  | 🔐 Secrets Scanning  | ✅     |                                    │ │
│  │  | 📊 Coverage          | ✅     |                                    │ │
│  │  | 🧹 Ruff Linting      | ✅     |                                    │ │
│  │  | 🧪 QA Consistency    | ✅     |  ◄── NEW                           │ │
│  │                                                                       │ │
│  │  Score: 7/7 checks passed                                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Posts PR Comment with all results                                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Configuration Files                                  │
└─────────────────────────────────────────────────────────────────────────────┘

specs/observer_guardrails.yaml ◄────┐
                                    │
specs/render_integration.md ◄───────┤
                                    │     Consistency
specs/slack_integration.md ◄────────┼────► Enforced By
                                    │     QA Checker
specs/mcp-architecture.md ◄─────────┤
                                    │
.github/workflows/                  │
  pr-governance-check.yml ◄─────────┘

        │
        │  Runs
        ▼

scripts/qa/
  obs_governance_consistency.py ─────► Validates All Above

        │
        │  Documents
        ▼

docs/
  QA_OBSERVABILITY_CONSISTENCY.md
```

## Developer Experience Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Developer Workflow                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Developer                   CI System                    GitHub PR
   │                           │                            │
   │ 1. Modify config file     │                            │
   │ ────────────────────────► │                            │
   │                           │                            │
   │                           │ 2. Trigger workflow        │
   │                           │ ───────────────────────────► │
   │                           │                            │
   │                           │ 3. Run QA checks           │
   │                           │ ◄────────────────          │
   │                           │                            │
   │                           │ 4. Generate report         │
   │                           │ ────────────►              │
   │                           │                            │
   │                           │ 5. Post PR comment         │
   │ ◄─────────────────────────────────────────────────────── │
   │ (See results in PR)       │                            │
   │                           │                            │
   │ 6. Fix issues based on    │                            │
   │    remediation steps      │                            │
   │ ────────────────────────► │                            │
   │                           │                            │
   │                           │ 7. Re-run checks           │
   │                           │ ───────────────────────────► │
   │                           │                            │
   │                           │ 8. All checks pass! ✅     │
   │ ◄─────────────────────────────────────────────────────── │
   │                           │                            │
   │ 9. Merge PR               │                            │
   │ ────────────────────────────────────────────────────────► │
   │                           │                            │
```

---

**Legend:**
- ► Flow direction
- ◄─ Dependency/reference
- ✅ Success state
- ❌ Failure state
- 🧪 New component
- ⚠️  Warning/info

**System Status:** ✅ Fully Integrated & Operational

