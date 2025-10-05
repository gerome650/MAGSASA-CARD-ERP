# 🛡️ GitHub Branch Protection Setup Guide

This guide provides step-by-step instructions for setting up comprehensive branch protection on the `main` branch to enforce quality gates and secure collaborative development.

## 📋 Prerequisites

- Admin access to the GitHub repository
- Understanding of CI/CD workflows
- Knowledge of pull request review processes

## 🎯 Branch Protection Configuration

### Step 1: Access Branch Protection Settings

1. Navigate to your repository: `https://github.com/gerome650/MAGSASA-CARD-ERP`
2. Go to **Settings** → **Branches**
3. Click **Add rule** or **Edit** if a rule already exists

### Step 2: Configure Branch Name Pattern

- **Branch name pattern**: `main`
- **Include administrators**: ✅ Check this box (recommended)

### Step 3: Enable Required Status Checks

**✅ Require a pull request before merging**
- **Required number of reviewers**: `1` (minimum)
- **Dismiss stale PR approvals when new commits are pushed**: ✅
- **Require review from code owners**: ✅ (if CODEOWNERS file exists)

**✅ Require status checks to pass before merging**
- **Require branches to be up to date before merging**: ✅
- **Status checks to require**:
  - `lint-and-typecheck`
  - `test`
  - `security`
  - `build`
  - `integration-test`
  - `title-lint` (from PR workflow)

### Step 4: Additional Protection Rules

**✅ Require linear history**: ✅
**✅ Include administrators**: ✅
**✅ Restrict pushes that create files larger than 100MB**: ✅

### Step 5: Advanced Settings (Optional but Recommended)

**✅ Allow force pushes**: ❌ (unchecked)
**✅ Allow deletions**: ❌ (unchecked)
**✅ Automatically delete head branches**: ✅

## 🔧 API-Based Setup (Alternative)

If you prefer using the GitHub CLI or API, here's the configuration:

```bash
# Install GitHub CLI if not already installed
# brew install gh (macOS) or apt install gh (Ubuntu)

# Authenticate with GitHub
gh auth login

# Set up branch protection via API
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint-and-typecheck","test","security","build","integration-test","title-lint"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

## 📊 Verification Checklist

After setting up branch protection, verify the following:

- [ ] Direct pushes to `main` are blocked
- [ ] Pull requests require at least 1 approval
- [ ] All CI status checks must pass before merge
- [ ] Branches must be up-to-date before merging
- [ ] Force pushes are disabled
- [ ] Branch deletion is disabled
- [ ] Linear history is enforced

## 🧪 Testing Branch Protection

1. **Test Direct Push Blocking**:
   ```bash
   git checkout main
   git checkout -b test-direct-push
   echo "test" >> test-file.txt
   git add test-file.txt
   git commit -m "test: direct push attempt"
   git push origin main
   # Should be blocked
   ```

2. **Test PR Requirements**:
   - Create a PR without proper title format
   - Create a PR with failing CI checks
   - Verify both are blocked from merging

## 🚨 Troubleshooting

### Common Issues

1. **"Status checks not found"**
   - Ensure CI workflows are running successfully
   - Check that status check names match exactly

2. **"Cannot merge PR"**
   - Verify all required status checks are passing
   - Ensure branch is up-to-date with main
   - Check that required reviewers have approved

3. **"Force push blocked"**
   - This is expected behavior
   - Use rebase instead: `git rebase main`

### Emergency Override

If you need to bypass branch protection in an emergency:

1. Go to **Settings** → **Branches**
2. Temporarily disable the rule
3. Perform the necessary operations
4. Re-enable the rule immediately

## 📈 Best Practices

1. **Gradual Rollout**: Start with basic protections and add more over time
2. **Team Training**: Ensure all team members understand the new workflow
3. **Documentation**: Keep this guide updated as requirements change
4. **Monitoring**: Regularly review branch protection logs and metrics
5. **Review Process**: Establish clear guidelines for code review standards

## 🔗 Related Documentation

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [Required Status Checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks)
- [Pull Request Reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews)

## ✅ Completion Status

Once branch protection is configured, your repository will be:

- 🔒 **Secure**: Protected from direct pushes and unsafe merges
- 📦 **Quality-Controlled**: Enforced with CI checks before merging
- 🧑‍💻 **Collaborative**: Ready for team development with proper review process
- 🛡️ **Resilient**: Safe to build MCP-ready features without structural risks

---

**Next Steps**: After completing branch protection setup, proceed with Step 2 — "Dry MCP Simulation" to validate agent stubs and orchestrator flows under feature-flag conditions.
