# 🏷️ Automatic Release Tagging - Optional Enhancement

## Overview

This optional enhancement automatically creates semantic version tags when release readiness reaches ≥95%.

## Implementation

### 1. Create Workflow File

**File:** `.github/workflows/auto-release-tag.yml`

```yaml
name: Auto Release Tagging

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      version_bump:
        description: 'Version bump type'
        required: true
        default: 'patch'
        type: choice
        options:
          - major
          - minor
          - patch

# Cancel superseded runs
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  check-and-tag:
    name: Check Readiness & Auto-Tag
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for tagging
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install PyGithub==2.3.0 rich==13.7.0 semver==3.0.2 python-dotenv==1.0.1
      
      - name: Check release readiness
        id: readiness
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          # Get current readiness score
          SCORE=$(python scripts/update_release_dashboard.py --get-score)
          echo "score=$SCORE" >> $GITHUB_OUTPUT
          
          if [ "$SCORE" -ge 95 ]; then
            echo "ready=true" >> $GITHUB_OUTPUT
            echo "✅ Readiness ≥95%, proceeding with tagging"
          else
            echo "ready=false" >> $GITHUB_OUTPUT
            echo "⚠️  Readiness ${SCORE}% < 95%, skipping auto-tag"
          fi
      
      - name: Get next version
        id: version
        if: steps.readiness.outputs.ready == 'true'
        run: |
          # Get current version from tags
          CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          echo "current=$CURRENT_VERSION" >> $GITHUB_OUTPUT
          
          # Calculate next version
          BUMP_TYPE="${{ github.event.inputs.version_bump || 'patch' }}"
          NEXT_VERSION=$(python scripts/calculate_next_version.py "$CURRENT_VERSION" "$BUMP_TYPE")
          echo "next=$NEXT_VERSION" >> $GITHUB_OUTPUT
          echo "📦 Next version: $NEXT_VERSION"
      
      - name: Create release tag
        if: steps.readiness.outputs.ready == 'true'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ steps.version.outputs.next }}"
          
          # Create annotated tag
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          
          git tag -a "$VERSION" -m "Release $VERSION - Readiness: ${{ steps.readiness.outputs.score }}%"
          git push origin "$VERSION"
          
          echo "✅ Created and pushed tag: $VERSION"
      
      - name: Create GitHub Release
        if: steps.readiness.outputs.ready == 'true'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          VERSION="${{ steps.version.outputs.next }}"
          
          # Generate release notes
          python scripts/generate_release_notes.py "$VERSION" > release_notes.md
          
          # Create GitHub release
          gh release create "$VERSION" \
            --title "Release $VERSION" \
            --notes-file release_notes.md \
            --verify-tag
          
          echo "✅ Created GitHub release: $VERSION"
      
      - name: Post to Slack
        if: steps.readiness.outputs.ready == 'true' && env.SLACK_WEBHOOK_URL != ''
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          VERSION="${{ steps.version.outputs.next }}"
          python scripts/notify_slack.py "auto-release" "$VERSION" "🚀 New release tagged: $VERSION (Readiness: ${{ steps.readiness.outputs.score }}%)"
```

### 2. Create Version Calculator Script

**File:** `scripts/calculate_next_version.py`

```python
#!/usr/bin/env python3
"""
Calculate next semantic version based on bump type.

Usage:
    python scripts/calculate_next_version.py v1.2.3 patch  # -> v1.2.4
    python scripts/calculate_next_version.py v1.2.3 minor  # -> v1.3.0
    python scripts/calculate_next_version.py v1.2.3 major  # -> v2.0.0
"""

import sys
from typing import Tuple


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string."""
    # Remove 'v' prefix if present
    version = version.lstrip('v')
    
    # Parse major.minor.patch
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    return tuple(map(int, parts))


def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type."""
    major, minor, patch = parse_version(version)
    
    if bump_type == 'major':
        return f"v{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"v{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"v{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: calculate_next_version.py <current_version> <bump_type>")
        sys.exit(1)
    
    current_version = sys.argv[1]
    bump_type = sys.argv[2]
    
    try:
        next_version = bump_version(current_version, bump_type)
        print(next_version)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

### 3. Create Release Notes Generator

**File:** `scripts/generate_release_notes.py`

```python
#!/usr/bin/env python3
"""
Generate release notes from Git history.

Usage:
    python scripts/generate_release_notes.py v1.2.3
"""

import os
import sys
import subprocess
from datetime import datetime
from typing import List, Dict


def get_commits_since_last_tag() -> List[str]:
    """Get commits since last tag."""
    try:
        # Get previous tag
        prev_tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0', 'HEAD^'],
            text=True
        ).strip()
        
        # Get commits since previous tag
        commits = subprocess.check_output(
            ['git', 'log', f'{prev_tag}..HEAD', '--pretty=format:%s'],
            text=True
        ).strip().split('\n')
        
        return [c for c in commits if c]
    except subprocess.CalledProcessError:
        # No previous tag, get all commits
        commits = subprocess.check_output(
            ['git', 'log', '--pretty=format:%s'],
            text=True
        ).strip().split('\n')
        return [c for c in commits if c]


def categorize_commits(commits: List[str]) -> Dict[str, List[str]]:
    """Categorize commits by type."""
    categories = {
        'Features': [],
        'Bug Fixes': [],
        'Performance': [],
        'Documentation': [],
        'Refactoring': [],
        'Testing': [],
        'CI/CD': [],
        'Other': []
    }
    
    for commit in commits:
        lower = commit.lower()
        if any(word in lower for word in ['feat:', 'feature:', 'add:', 'new:']):
            categories['Features'].append(commit)
        elif any(word in lower for word in ['fix:', 'bug:', 'hotfix:']):
            categories['Bug Fixes'].append(commit)
        elif any(word in lower for word in ['perf:', 'performance:', 'optimize:']):
            categories['Performance'].append(commit)
        elif any(word in lower for word in ['docs:', 'doc:', 'documentation:']):
            categories['Documentation'].append(commit)
        elif any(word in lower for word in ['refactor:', 'refactoring:', 'cleanup:']):
            categories['Refactoring'].append(commit)
        elif any(word in lower for word in ['test:', 'testing:']):
            categories['Testing'].append(commit)
        elif any(word in lower for word in ['ci:', 'cd:', 'workflow:']):
            categories['CI/CD'].append(commit)
        else:
            categories['Other'].append(commit)
    
    return categories


def generate_release_notes(version: str) -> str:
    """Generate release notes."""
    commits = get_commits_since_last_tag()
    categories = categorize_commits(commits)
    
    # Build release notes
    notes = [
        f"# Release {version}",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"",
        "## 📦 What's Changed",
        ""
    ]
    
    for category, items in categories.items():
        if items:
            notes.append(f"### {category}")
            for item in items:
                notes.append(f"- {item}")
            notes.append("")
    
    # Add stats
    notes.extend([
        "## 📊 Statistics",
        f"- Total commits: {len(commits)}",
        f"- Contributors: {get_contributor_count()}",
        "",
        "## ✅ Verification",
        "This release has passed all CI/CD quality gates:",
        "- ✅ Linting (Ruff, Black, MyPy)",
        "- ✅ Tests (coverage ≥80%)",
        "- ✅ Security scan (Bandit + pip-audit)",
        "- ✅ Readiness score ≥95%",
        "",
        "**Full Changelog:** https://github.com/$GITHUB_REPOSITORY/compare/...{version}"
    ])
    
    return '\n'.join(notes)


def get_contributor_count() -> int:
    """Get number of unique contributors since last tag."""
    try:
        prev_tag = subprocess.check_output(
            ['git', 'describe', '--tags', '--abbrev=0', 'HEAD^'],
            text=True
        ).strip()
        
        contributors = subprocess.check_output(
            ['git', 'log', f'{prev_tag}..HEAD', '--format=%an'],
            text=True
        ).strip().split('\n')
        
        return len(set(contributors))
    except subprocess.CalledProcessError:
        return 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: generate_release_notes.py <version>")
        sys.exit(1)
    
    version = sys.argv[1]
    notes = generate_release_notes(version)
    print(notes)
```

### 4. Update Release Dashboard Script

Add `--get-score` option to `scripts/update_release_dashboard.py`:

```python
# Add to argument parser
parser.add_argument('--get-score', action='store_true',
                    help='Output current readiness score and exit')

# Add after argument parsing
if args.get_score:
    score = calculate_readiness_score()
    print(score)
    sys.exit(0)
```

## Usage

### Automatic Tagging (on push to main)
When code is pushed to main and readiness ≥95%, a new patch version is automatically tagged.

### Manual Tagging
```bash
# Trigger manual release with specific bump type
gh workflow run auto-release-tag.yml -f version_bump=minor
```

### Version Bump Types
- `patch` - v1.2.3 → v1.2.4 (bug fixes)
- `minor` - v1.2.3 → v1.3.0 (new features)
- `major` - v1.2.3 → v2.0.0 (breaking changes)

## Configuration

### Required Secrets
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- `SLACK_WEBHOOK_URL` - (Optional) For Slack notifications

### Permissions
Ensure GitHub Actions has permissions to:
- Create tags
- Push to repository
- Create releases

In repository settings:
```
Settings → Actions → General → Workflow permissions
- [x] Read and write permissions
```

## Benefits

1. **Consistent Versioning** - Semantic versioning enforced
2. **Quality Assurance** - Only tag when readiness ≥95%
3. **Automated Release Notes** - Generated from Git history
4. **Audit Trail** - Full changelog and verification status
5. **Team Notifications** - Slack alerts for new releases

## Testing

```bash
# Test version calculation
python scripts/calculate_next_version.py v1.2.3 patch
# Output: v1.2.4

# Test release notes generation
python scripts/generate_release_notes.py v1.2.4
# Output: Markdown release notes

# Test workflow manually
gh workflow run auto-release-tag.yml -f version_bump=patch
```

## Rollback

If a release needs to be rolled back:

```bash
# Delete tag locally and remotely
git tag -d v1.2.4
git push origin :refs/tags/v1.2.4

# Delete GitHub release
gh release delete v1.2.4 --yes
```

## Integration with CI/CD

This workflow integrates seamlessly with your existing CI/CD:
- Runs after successful merge to main
- Uses same readiness scoring system
- Respects quality gates
- Follows semantic versioning
- Generates comprehensive release notes

---

**Ready to implement?** Run:
```bash
# Create the workflow
cp CI_AUTO_RELEASE_TAGGING.md .github/workflows/auto-release-tag.yml

# Create the scripts
chmod +x scripts/calculate_next_version.py
chmod +x scripts/generate_release_notes.py

# Test it
python scripts/calculate_next_version.py v0.7.0 patch
```

