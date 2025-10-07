# Pull Request Checklist

## 📋 Overview
<!-- Provide a brief summary of what this PR accomplishes -->

**Type of Change:**
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to change)
- [ ] 📝 Documentation update
- [ ] 🏗️ Infrastructure/DevOps change
- [ ] 🔒 Security enhancement
- [ ] 🎨 UI/UX improvement

**Related Issues:** 
<!-- Link to related issues: Fixes #123, Related to #456 -->

---

## ✅ Pre-Submission Checklist

### Code Quality
- [ ] Code follows project style guidelines (Black, Ruff)
- [ ] All linter checks pass locally (`make lint` or `ruff check .`)
- [ ] Code is properly formatted (`black .`)
- [ ] No unused imports or variables
- [ ] Type hints added where applicable

### Testing & Coverage
- [ ] New tests added for new features/fixes
- [ ] All existing tests pass (`make test` or `pytest`)
- [ ] Code coverage meets or exceeds threshold (see `CI_QUICK_REFERENCE.md`)
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed in local environment

### Security & Compliance
- [ ] No hardcoded secrets, tokens, or API keys
- [ ] Environment variables properly documented in `env.template`
- [ ] Authentication/authorization checked where applicable
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] Input validation implemented for user-facing endpoints
- [ ] Security scan results reviewed (if applicable)

### Documentation
- [ ] Code comments added for complex logic
- [ ] API documentation updated (if endpoints changed)
- [ ] README updated (if user-facing changes)
- [ ] CHANGELOG.md updated with changes
- [ ] Migration guide provided (if breaking changes)

### CI/CD & Governance
- [ ] All CI checks pass (see `.github/workflows/`)
- [ ] Branch name follows convention (e.g., `feat/`, `fix/`, `governance/`)
- [ ] Commit messages follow conventional commits format
- [ ] No commits directly to `main` branch
- [ ] Pre-commit hooks passed without issues

---

## 🔍 Audit Trail (For Investors/Auditors)

### What Changed
<!-- List the key changes in bullet points -->
- 
- 
- 

### Why This Change Is Needed
<!-- Explain the business or technical rationale -->

### Risk Assessment
**Risk Level:** <!-- Low / Medium / High -->

**Mitigation Steps:**
<!-- Explain how risks are mitigated -->
- 
- 

### Compliance Impact
- [ ] No impact on regulatory compliance
- [ ] Changes reviewed against compliance requirements (see `GOVERNANCE_AND_COMPLIANCE.md`)
- [ ] Data privacy requirements met (GDPR/local regulations)
- [ ] Audit logging maintained/enhanced

### Performance Impact
- [ ] No performance impact expected
- [ ] Performance testing completed (results: <!-- link or summary -->)
- [ ] Database migration tested with production-like data volume
- [ ] Load testing passed (see `loadtest.yml`)

---

## 🚀 Deployment Readiness

### Database Migrations
- [ ] No database changes
- [ ] Migration scripts included (`migrations/`)
- [ ] Migration tested on staging environment
- [ ] Rollback plan documented

### Configuration Changes
- [ ] No configuration changes
- [ ] New environment variables documented
- [ ] Configuration changes tested in staging
- [ ] Secrets properly managed (via secrets manager, not in code)

### Rollback Plan
<!-- Describe how to rollback if this change causes issues in production -->

---

## 📊 Testing Evidence

### Test Results
<!-- Paste or link to test results -->
```
# Example:
pytest tests/ -v --cov
Coverage: 85%
Tests Passed: 124/124
```

### Manual Testing Checklist
- [ ] Tested in local development environment
- [ ] Tested with sample/seed data
- [ ] Tested error handling scenarios
- [ ] Tested edge cases
- [ ] UI tested on multiple browsers/devices (if applicable)

---

## 📚 Reference Documentation
<!-- Link to relevant documentation -->
- Architecture: 
- Implementation Guide: 
- Related PRs: 

### Governance & Compliance References
- CI/CD Documentation: `CI_CD_DOCUMENTATION_INDEX.md`
- Governance Framework: `GOVERNANCE_AND_COMPLIANCE.md`
- Merge Quality Standards: `MERGE_QUALITY_SYSTEM_README.md`
- Release Process: `GITOPS_RELEASE_AUTOMATION_COMPLETE.md`
- Testing Standards: `FINAL_TEST_SUITE_SUMMARY.md`

---

## 👥 Review Requirements

**Required Reviewers:**
<!-- Tag specific people/teams if needed -->
- [ ] Code review by: 
- [ ] Security review by: (if security-related)
- [ ] Compliance review by: (if compliance-related)

**Estimated Review Time:** <!-- e.g., 1 hour, 2 days -->

---

## 📝 Additional Notes
<!-- Any additional context, screenshots, or information for reviewers -->

---

## 🎯 Post-Merge Checklist
<!-- To be completed AFTER merging -->
- [ ] Deployed to staging environment
- [ ] Smoke tests passed in staging
- [ ] Monitoring/alerts configured (if applicable)
- [ ] Stakeholders notified
- [ ] Documentation site updated (if applicable)
- [ ] Release notes drafted (if part of a release)

---

<details>
<summary>📋 CI/CD Pipeline Status (Auto-populated by CI)</summary>

<!-- This section will be auto-populated by CI/CD workflows -->
- **Build Status:** Pending ⏳
- **Test Coverage:** Pending ⏳
- **Security Scan:** Pending ⏳
- **Linter:** Pending ⏳
- **Type Check:** Pending ⏳

Check the Actions tab for real-time status updates.
</details>

---

**By submitting this PR, I confirm:**
- [ ] I have reviewed my own code
- [ ] I have tested the changes thoroughly
- [ ] I have updated all relevant documentation
- [ ] This PR is ready for review
- [ ] I understand this will trigger automated CI/CD governance checks

---

*Template Version: 1.0 | Last Updated: 2025-10-07*
*For questions about this template, see: `MERGE_QUALITY_SYSTEM_README.md`*
