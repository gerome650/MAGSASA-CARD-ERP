#!/usr/bin/env bash
set -euo pipefail

# Inputs (optional)
REPORT_PATH="${1:-.github/reports/dependency-audit-$(date +%F).md}"
PROJECT_NAME="${2:-${GITHUB_REPOSITORY:-local-repo}}"

mkdir -p "$(dirname "$REPORT_PATH")"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

echo "🔍 Running dependency audit..."
summary_lines=()
vuln_count=0
exit_code=0

write_header() {
  cat >"$REPORT_PATH" <<EOF
# 🔐 Dependency Audit Report

Repository: \`$PROJECT_NAME\`  
Generated: $(date -u +"%Y-%m-%d %H:%M:%SZ")

---
EOF
}

append_section() {
  printf "\n%s\n\n" "$1" >> "$REPORT_PATH"
}

write_header

# 1) Try poetry export + safety
if have_cmd poetry && have_cmd safety; then
  echo "• Using poetry + safety"
  tmp_req="$(mktemp)"
  poetry export -f requirements.txt --with dev --without-hashes -o "$tmp_req" || true
  if [ -s "$tmp_req" ]; then
    append_section "## 🧪 Safety (via poetry export)"
    if safety check --stdin --full-report < "$tmp_req" | tee -a "$REPORT_PATH"; then
      summary_lines+=("• Safety: ✅ no known vulnerabilities")
    else
      summary_lines+=("• Safety: ❌ vulnerabilities detected")
      vuln_count=$((vuln_count+1))
      exit_code=1
    fi
  else
    summary_lines+=("• Safety: ⚠️ poetry export returned empty requirements; skipped")
  fi
  rm -f "$tmp_req"
else
  summary_lines+=("• Safety: ⚠️ poetry & safety not both available; skipping")
fi

# 2) Try pip-audit as a fallback
if have_cmd pip-audit; then
  append_section "## 🧪 pip-audit"
  if pip-audit | tee -a "$REPORT_PATH"; then
    summary_lines+=("• pip-audit: ✅ no known vulnerabilities")
  else
    summary_lines+=("• pip-audit: ❌ vulnerabilities detected")
    vuln_count=$((vuln_count+1))
    exit_code=1
  fi
else
  summary_lines+=("• pip-audit: ⚠️ not installed; skipping")
fi

# 3) npm audit if Node project exists
if [ -f package.json ] && command -v npm >/dev/null 2>&1; then
  append_section "## 🧪 npm audit"
  if npm audit --audit-level=high | tee -a "$REPORT_PATH"; then
    summary_lines+=("• npm audit: ✅ clean (no high+)")
  else
    summary_lines+=("• npm audit: ❌ issues found (≥high)")
    vuln_count=$((vuln_count+1))
    exit_code=1
  fi
fi

append_section "## 📊 Summary"
{
  for line in "${summary_lines[@]}"; do
    echo "- $line"
  done
  echo
  if [ "$vuln_count" -gt 0 ]; then
    echo "**Result:** ❌ vulnerabilities detected"
  else
    echo "**Result:** ✅ no blocking vulnerabilities"
  fi
} >> "$REPORT_PATH"

echo "Report written to: $REPORT_PATH"
exit "$exit_code"

