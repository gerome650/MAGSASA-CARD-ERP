# 📋 PR Template Quick Reference

## 🚀 Quick Start

Your repository now has an **automatic PR template** at `.github/PULL_REQUEST_TEMPLATE.md` that will populate every new pull request!

---

## 📝 Creating a PR with the Template

### Option 1: Using GitHub CLI (Fastest)
```bash
# The template will auto-populate
gh pr create --title "Your PR Title" --base main --web
```

### Option 2: Using Web Interface
1. Push your branch: `git push -u origin your-branch-name`
2. Go to GitHub → Click "Compare & pull request"
3. Template automatically loads ✨
4. Fill in the sections and submit

### Option 3: Manual Copy/Paste
If you need to add the template to an existing PR:
```bash
cat .github/PULL_REQUEST_TEMPLATE.md | pbcopy  # macOS
# Or manually copy from .github/PULL_REQUEST_TEMPLATE.md
```

---

## ✅ Key Sections to Always Complete

### For ALL PRs:
1. **Overview** - What changed and why
2. **Type of Change** - Check appropriate boxes
3. **Pre-Submission Checklist** - Verify all items
4. **Testing Evidence** - Paste test results

### For GOVERNANCE/INFRASTRUCTURE PRs:
5. **Audit Trail** - Risk assessment + compliance impact
6. **Deployment Readiness** - Migration + rollback plan
7. **Reference Documentation** - Link relevant docs

### For FEATURE PRs:
8. **Performance Impact** - Test results
9. **Manual Testing Checklist** - UI/UX verification
10. **Additional Notes** - Screenshots, demos

---

## 🎯 Investor/Auditor Quick View

The template includes a dedicated **Audit Trail** section that answers:
- ✅ **What changed** - Clear bullet points
- ✅ **Why it's needed** - Business rationale
- ✅ **Risk level** - Low/Medium/High + mitigation
- ✅ **Compliance impact** - Regulatory alignment
- ✅ **Performance impact** - Test evidence

This makes due diligence **10× faster** for stakeholders!

---

## 🔧 Customization

### Adding Custom Sections
Edit `.github/PULL_REQUEST_TEMPLATE.md` and add your sections:
```markdown
## 🏢 Your Custom Section
- [ ] Custom checkpoint 1
- [ ] Custom checkpoint 2
```

### Creating Multiple Templates
For specialized PR types (hotfix, security, etc.):
```bash
# Create specialized templates
.github/PULL_REQUEST_TEMPLATE/
  ├── hotfix.md
  ├── security.md
  └── feature.md

# Use them with:
gh pr create --template .github/PULL_REQUEST_TEMPLATE/security.md
```

---

## 📊 Template Benefits

| Benefit | Impact |
|---------|--------|
| **Automated Compliance** | Every PR includes governance checkpoints |
| **Faster Reviews** | Reviewers have all context upfront |
| **Audit-Ready** | Complete trail for compliance teams |
| **Risk Mitigation** | Forces risk assessment before merge |
| **Quality Gates** | Ensures testing + documentation standards |
| **Deployment Safety** | Rollback plans required for all changes |

---

## 🔗 Integration with Your CI/CD

The template references your existing governance framework:

```markdown
### Governance & Compliance References
- CI/CD Documentation: `CI_CD_DOCUMENTATION_INDEX.md`
- Governance Framework: `GOVERNANCE_AND_COMPLIANCE.md`
- Merge Quality Standards: `MERGE_QUALITY_SYSTEM_README.md`
- Release Process: `GITOPS_RELEASE_AUTOMATION_COMPLETE.md`
- Testing Standards: `FINAL_TEST_SUITE_SUMMARY.md`
```

Your CI workflows can **validate** these checkpoints automatically!

---

## 🛡️ Safe Push Workflow + Template

```bash
# 1️⃣ Format and fix
black . && ruff --fix .

# 2️⃣ Stage and commit
git add .
git commit -m "feat(governance): your feature description"

# 3️⃣ Create feature branch
git checkout -b feat/your-feature-$(date +%Y%m%d)

# 4️⃣ Push to GitHub
git push -u origin HEAD

# 5️⃣ Create PR with auto-populated template ✨
gh pr create --title "Your Feature" \
  --base main \
  --web  # Template loads automatically!
```

---

## 💡 Pro Tips

1. **Fill it out as you code** - Don't wait until PR time
2. **Use screenshots** - Visual evidence speeds up reviews
3. **Link related PRs** - Shows complete context
4. **Update CHANGELOG** - Makes release notes easier
5. **Tag reviewers early** - Faster feedback loops

---

## 🆘 Troubleshooting

### Template not showing?
```bash
# Verify it exists
ls -la .github/PULL_REQUEST_TEMPLATE.md

# Check it's committed
git status
git add .github/PULL_REQUEST_TEMPLATE.md
git commit -m "chore: add PR template"
git push
```

### Need to skip the template?
```bash
# Use --body flag
gh pr create --title "Quick Fix" --body "Simple description" --base main
```

---

## 📚 Additional Resources

- **Template Source**: `.github/PULL_REQUEST_TEMPLATE.md`
- **Governance Docs**: `GOVERNANCE_AND_COMPLIANCE.md`
- **Merge Quality**: `MERGE_QUALITY_SYSTEM_README.md`
- **CI/CD Guide**: `CI_CD_QUICK_REFERENCE.md`
- **Safe Push Guide**: `QUICK_FIX_GUIDE.md`

---

*Last Updated: 2025-10-07*
*Questions? Check `MERGE_QUALITY_SYSTEM_README.md` or your team's governance lead*

