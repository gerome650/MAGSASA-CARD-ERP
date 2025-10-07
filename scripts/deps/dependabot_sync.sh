#!/usr/bin/env bash
set -euo pipefail

# Best-effort linker: finds open Dependabot alerts and references them in PR comments.
# Requirements: gh CLI authenticated with repo scope, GITHUB_TOKEN available.

PR_NUMBER="${1:-}"
if [ -z "$PR_NUMBER" ]; then
  echo "ℹ️ No PR number provided to dependabot_sync; skipping."
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ℹ️ gh not installed; skipping Dependabot sync."
  exit 0
fi

owner_repo="${GITHUB_REPOSITORY:-}"
if [ -z "$owner_repo" ]; then
  echo "ℹ️ GITHUB_REPOSITORY not set; skipping Dependabot sync."
  exit 0
fi

echo "🔗 Attempting to link Dependabot alerts to PR #$PR_NUMBER"

# Dependabot alerts API may require special permissions. We handle failures gracefully.
alerts_json="$(gh api -H "Accept: application/vnd.github+json" \
  "/repos/$owner_repo/dependabot/alerts?state=open" 2>/dev/null || true)"

if [ -z "$alerts_json" ] || [ "$alerts_json" = "[]" ]; then
  echo "ℹ️ No open Dependabot alerts found or insufficient permissions."
  exit 0
fi

# Build a simple list of advisories
links="$(echo "$alerts_json" | jq -r '.[] | "- **\(.security_advisory.summary)** (pkg: \(.dependency.package.name) — severity: \(.security_advisory.severity))"' 2>/dev/null || true)"
if [ -z "$links" ]; then
  echo "ℹ️ Could not parse alerts; skipping."
  exit 0
fi

body=$(
  cat <<EOF
🔗 **Dependabot Alerts (open)**

$links

_This is an automated best-effort sync. Some alerts may require finer scopes to list._
EOF
)

gh pr comment "$PR_NUMBER" --body "$body" || true
echo "✅ Posted Dependabot alert summary on PR."

