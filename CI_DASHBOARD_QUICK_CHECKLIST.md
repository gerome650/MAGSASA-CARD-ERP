# 🚦 CI Dashboard Validation Checklist

Use this checklist to track your progress through the CI Dashboard validation and deployment.

---

## 🔧 Phase 1: Apply Fixes

- [x] ✅ **Review Validation Report** (`CI_DASHBOARD_VALIDATION_REPORT.md`)
- [x] ✅ **Apply Automated Fixes** (Poetry → uv, Slack optional)
- [ ] ⏳ **Configure Slack Webhook** (Optional - skip if you don't want notifications)
  - [ ] Create Slack Incoming Webhook at https://api.slack.com/messaging/webhooks
  - [ ] Add `SLACK_WEBHOOK_URL` secret at https://github.com/gerome650/MAGSASA-CARD-ERP/settings/secrets/actions
- [ ] ⏳ **Commit and Push Changes**
  ```bash
  git add .github/workflows/ci-pro-dashboard.yml
  git add CI_DASHBOARD_*.md
  git commit -m "fix: CI Dashboard workflow - replace Poetry with uv, make Slack optional"
  git push origin main
  ```

---

## 🚀 Phase 2: Monitor Pipeline

- [ ] ⏳ **Watch Pipeline Run** at https://github.com/gerome650/MAGSASA-CARD-ERP/actions
- [ ] ⏳ **Verify Job Steps:**
  - [ ] 📥 Checkout: Success
  - [ ] 🐍 Python Setup: Success
  - [ ] 📦 Dependencies Install: Success ✅ (was failing before)
  - [ ] 📏 Ruff Lint: Success (or skipped with errors)
  - [ ] 🧪 Tests + Coverage: Success
  - [ ] 📈 Extract Coverage: Success
  - [ ] ⏱️ Compute Duration: Success
  - [ ] 🧠 Generate Dashboard: Success
  - [ ] 📤 Upload Artifact: Success
  - [ ] 📡 Publish GitHub Pages: Success
  - [ ] 📣 Slack Summary: Success or Skipped

---

## 🌐 Phase 3: Verify Dashboard Deployment

- [ ] ⏳ **Check gh-pages Branch Created**
  ```bash
  git fetch origin
  git branch -a | grep gh-pages
  ```
  Expected: `remotes/origin/gh-pages`

- [ ] ⏳ **Enable GitHub Pages** (if not already)
  - Go to: https://github.com/gerome650/MAGSASA-CARD-ERP/settings/pages
  - Source: `gh-pages` branch, `/ (root)` folder
  - Click Save
  - Wait ~1 minute for deployment

- [ ] ⏳ **Access Dashboard URL**
  - Visit: https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/
  - Expected: Dashboard loads with real data

---

## 📊 Phase 4: Validate Dashboard Content

### KPI Cards (Top Row)
- [ ] ⏳ **Coverage Card**
  - Shows percentage (e.g., "85.3%")
  - Shows delta vs previous run (e.g., "+1.2% vs prev")

- [ ] ⏳ **Pass Rate Card**
  - Shows percentage (e.g., "100.0%")
  - Shows test counts (e.g., "25/25 passed")

- [ ] ⏳ **Lint Issues Card**
  - Shows issue count (e.g., "12")
  - Label: "Ruff total"

- [ ] ⏳ **CI Duration Card**
  - Shows duration (e.g., "3m 45s")
  - Shows commit SHA + branch

### Trend Charts
- [ ] ⏳ **Coverage Trend Chart**
  - Renders (may show single point if first run)
  - X-axis: Dates
  - Y-axis: Percentage

- [ ] ⏳ **Pass Rate Trend Chart**
  - Renders with test pass rate data

- [ ] ⏳ **CI Duration Trend Chart**
  - Shows duration in seconds over time

- [ ] ⏳ **Lint Issues Trend Chart**
  - Shows Ruff issue count over time

### Metadata Panel
- [ ] ⏳ **Latest Run Info**
  - Timestamp displayed
  - "Open on GitHub" link works
  - Actor name shown

### Badges Preview
- [ ] ⏳ **5 Badges Display**
  - Coverage badge (green/yellow/red based on %)
  - Coverage trend badge (shows delta)
  - Test results badge
  - Lint status badge
  - CI duration badge

---

## 🔗 Phase 5: Validate JSON Endpoints

Test each endpoint (use browser or `curl`):

- [ ] ⏳ **`/data/latest.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/latest.json | jq
  ```
  Expected: JSON with `timestamp`, `tests`, `lint`, `coverage_percent`, etc.

- [ ] ⏳ **`/data/history.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/history.json | jq
  ```
  Expected: Array with at least 1 entry

- [ ] ⏳ **`/data/coverage.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/coverage.json | jq
  ```
  Expected: `{"coverage_percent": XX.X}`

- [ ] ⏳ **`/data/tests.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/tests.json | jq
  ```
  Expected: `{"passed": X, "failed": Y, "skipped": Z, "duration": N.N}`

- [ ] ⏳ **`/data/lint.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/lint.json | jq
  ```
  Expected: `{"issues": N}`

- [ ] ⏳ **`/data/meta.json`**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/meta.json | jq
  ```
  Expected: Metadata with `repo`, `commit`, `branch`, `run_url`, etc.

---

## 🏅 Phase 6: Validate Badge Endpoints

Test each badge endpoint:

- [ ] ⏳ **Coverage Badge**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/coverage-badge.json | jq
  ```
  Expected: `{"schemaVersion": 1, "label": "Coverage", "message": "XX.X%", "color": "green"}`

- [ ] ⏳ **Test Results Badge**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/test-results-badge.json | jq
  ```

- [ ] ⏳ **Lint Status Badge**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/lint-status-badge.json | jq
  ```

- [ ] ⏳ **CI Duration Badge**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/ci-duration-badge.json | jq
  ```

- [ ] ⏳ **Coverage Trend Badge**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/coverage-trend-badge.json | jq
  ```

---

## 📱 Phase 7: Test Badge Display

- [ ] ⏳ **Render Badges in Markdown** (test locally first)
  ```markdown
  ![Coverage](https://img.shields.io/endpoint?url=https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/badges/coverage-badge.json)
  ```
  - Copy to a test `.md` file
  - Preview in GitHub or VS Code
  - Verify badges render with correct values

- [ ] ⏳ **Add Badges to README**
  ```bash
  # Edit README.md to add badges section
  vim README.md
  # Or use your preferred editor
  ```

- [ ] ⏳ **Commit Badge Changes**
  ```bash
  git add README.md
  git commit -m "docs: add CI Dashboard badges to README"
  git push origin main
  ```

---

## 📣 Phase 8: Verify Slack Notification (If Configured)

- [ ] ⏳ **Check Slack Channel**
  - Expected message format:
    ```
    📊 CI Dashboard Update — gerome650/MAGSASA-CARD-ERP
    Branch: main
    Commit: [SHA]
    Tests: X/Y passed
    Coverage: XX.X%
    Lint Issues: N
    Duration: Xm XXs
    🔗 View Dashboard | 🔗 View Run
    🚦 Status: success, triggered by gerome650
    ```

- [ ] ⏳ **Verify Links Work**
  - Click "View Dashboard" → Should open dashboard
  - Click "View Run" → Should open GitHub Actions run

- [ ] ⏳ **Check Coverage Delta**
  - Second run onwards, should show "+X.X%" or "-X.X%"

---

## 📈 Phase 9: Verify Historical Tracking

- [ ] ⏳ **Trigger Second Run** (optional, to test trends)
  ```bash
  # Make a trivial change
  echo "\n# CI Dashboard Active" >> README.md
  git add README.md
  git commit -m "test: trigger CI Dashboard second run for trend validation"
  git push origin main
  ```

- [ ] ⏳ **Check history.json Updated**
  ```bash
  curl -s https://gerome650.github.io/MAGSASA-CARD-ERP/ci-dashboard/data/history.json | jq 'length'
  ```
  Expected: `2` (or more)

- [ ] ⏳ **Verify Trend Charts Update**
  - Visit dashboard
  - Charts should now show 2+ data points
  - Lines should connect points

- [ ] ⏳ **Verify Coverage Delta Updates**
  - Coverage trend badge should show "+X.X%" or "-X.X%" vs previous run

---

## 🏷️ Phase 10: Finalize & Tag

- [ ] ⏳ **All Validation Stages Pass** ✅
  - Pipeline: ✅
  - Dashboard: ✅
  - JSON Endpoints: ✅
  - Badge Endpoints: ✅
  - Slack (if configured): ✅
  - Historical Tracking: ✅

- [ ] ⏳ **Create Baseline Tag**
  ```bash
  git tag -a ci-dashboard-v1.0 -m "CI Pro Dashboard - Initial Production Release"
  git push origin ci-dashboard-v1.0
  ```

- [ ] ⏳ **Update Project Documentation**
  - Add CI Dashboard link to main README
  - Update any developer onboarding docs
  - Add to CI/CD documentation index

---

## 🎯 Success Criteria

✅ **You're done when all of these are true:**

1. ✅ Pipeline runs successfully on every push to `main`
2. ✅ Dashboard is accessible at public URL
3. ✅ All 6 JSON endpoints return valid data
4. ✅ All 5 badge endpoints return Shields.io format
5. ✅ Historical data is accumulating (2+ runs recorded)
6. ✅ Slack notifications work (if configured) or skip gracefully (if not)
7. ✅ Badges are added to README and display correctly
8. ✅ Trend charts show meaningful data

---

## 📊 Current Status

| **Phase** | **Status** | **Notes** |
|-----------|------------|-----------|
| 1. Apply Fixes | ✅ Done | Workflow patched, docs created |
| 2. Monitor Pipeline | ⏳ Pending | Waiting for push to main |
| 3. Verify Deployment | ⏳ Pending | Waiting for pipeline success |
| 4. Validate Dashboard | ⏳ Pending | Waiting for Pages deployment |
| 5. Validate JSON | ⏳ Pending | Waiting for data generation |
| 6. Validate Badges | ⏳ Pending | Waiting for badge generation |
| 7. Test Badge Display | ⏳ Pending | Waiting for badges to be live |
| 8. Verify Slack | ⏳ Pending | Optional - skip if not needed |
| 9. Historical Tracking | ⏳ Pending | Needs 2+ runs |
| 10. Finalize & Tag | ⏳ Pending | Final step after validation |

---

## 🆘 Quick Troubleshooting

**Pipeline still failing?**
- Check logs: `gh run view --log`
- See: `CI_DASHBOARD_FIX_SUMMARY.md` → Troubleshooting section

**Dashboard 404?**
- Verify `gh-pages` branch exists: `git branch -a | grep gh-pages`
- Enable Pages: https://github.com/gerome650/MAGSASA-CARD-ERP/settings/pages

**Badges not rendering?**
- Test JSON endpoints first (they must return valid JSON)
- Wait 1-2 minutes for Shields.io CDN cache to refresh

**No trend data?**
- Trends require 2+ runs
- Trigger another run by pushing a small change

---

## 📞 Support

If you encounter issues not covered here:
1. Review full validation report: `CI_DASHBOARD_VALIDATION_REPORT.md`
2. Review fix summary: `CI_DASHBOARD_FIX_SUMMARY.md`
3. Check GitHub Actions logs for detailed error messages
4. Review the workflow file: `.github/workflows/ci-pro-dashboard.yml`

---

**Last Updated:** October 5, 2025  
**Version:** 1.0  
**Status:** Ready for deployment 🚀

