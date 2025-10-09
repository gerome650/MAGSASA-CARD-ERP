# Release Plan

- Source branch: release/workflows-2025-10-05-09-30
- Commit message: chore(release): bump runtime versions and prepare release
- Dependency gate: audit → (auto-fix if needed) → re-audit

## Planned Actions
1. Run dependency audit and attempt auto-fix if needed
2. Run bump-versions (interactive unless DRY_RUN=true)
3. Generate artifacts: .python-version, .tool-versions, Dockerfile tag, pyproject constraints, CHANGELOG.md
4. Create PR to main with auto-merge enabled


## Dependency Gate Results
- Status: **PASSED**
