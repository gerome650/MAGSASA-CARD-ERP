#!/usr/bin/env python3
"""
QA Observability & Governance Consistency Checker

Validates consistency across observability/governance files in PR diffs.
Checks YAML validity, threshold consistency, secrets references, and doc sync.

Exit codes:
  0 - All checks passed (warnings allowed)
  1 - Critical errors found
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("⚠️  PyYAML not available, using fallback parser", file=sys.stderr)


@dataclass
class CheckResult:
    """Represents a check result with severity and details."""

    name: str
    status: str  # "pass", "warning", "error"
    message: str
    remediation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ThresholdMismatch:
    """Represents a threshold mismatch for diff reporting."""

    metric: str
    expected: float
    found: float
    source_file: str


class ConsistencyChecker:
    """Main checker class for observability/governance consistency."""

    # Target files to watch
    WATCH_FILES = [
        "specs/observer_guardrails.yaml",
        "specs/render_integration.md",
        "specs/slack_integration.md",
        "specs/mcp-architecture.md",
        ".github/workflows/pr-governance-check.yml",
    ]

    # Expected thresholds
    EXPECTED_THRESHOLDS = {
        "uptime_warn": 99.0,
        "uptime_fail": 98.0,
        "latency_warn": 2500,
        "latency_fail": 4000,
        "drift_warn": 2,
        "drift_fail": 5,
    }

    # Required secrets
    REQUIRED_SECRETS = [
        "secrets.RENDER_API_KEY",
        "secrets.RENDER_SERVICE_ID",
        "secrets.SLACK_GOVERNANCE_WEBHOOK",
    ]

    def __init__(
        self,
        base_sha: str | None = None,
        head_sha: str | None = None,
        debug: bool = False,
    ):
        self.base_sha = base_sha
        self.head_sha = head_sha
        self.errors: list[CheckResult] = []
        self.warnings: list[CheckResult] = []
        self.files_checked: list[str] = []
        self.mismatches: list[ThresholdMismatch] = []
        self.workspace = Path.cwd()
        self.debug = debug

    def run(self) -> dict[str, Any]:
        """Execute all checks and return results."""
        print("🧪 Running QA Observability & Governance Consistency Checks...")

        # Determine if we should run checks (based on changed files)
        if not self._should_run_checks():
            print("✅ No relevant files changed, skipping consistency checks")
            return self._generate_output(skip=True)

        # Run all checks
        self._check_yaml_validity()
        self._check_threshold_consistency()
        self._check_secrets_presence()
        self._check_observer_charter_sync()
        self._check_guardrails_alignment()

        # Generate output
        return self._generate_output()

    def _should_run_checks(self) -> bool:
        """Check if any watched files have changed in the PR."""
        changed_files = self._get_changed_files()
        if not changed_files:
            return True  # Run checks if we can't determine changed files

        for watch_file in self.WATCH_FILES:
            if any(watch_file in f for f in changed_files):
                print(f"📝 Detected change in watched file: {watch_file}")
                return True

        return False

    def _get_changed_files(self) -> list[str]:
        """Get list of files changed in the PR."""
        try:
            # Try to use provided SHAs
            if self.base_sha and self.head_sha:
                cmd = [
                    "git",
                    "diff",
                    "--name-only",
                    f"{self.base_sha}...{self.head_sha}",
                ]
            else:
                # Fallback: detect base branch from env or use main
                base_ref = os.getenv("GITHUB_BASE_REF", "main")
                cmd = ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip().split("\n")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not determine changed files: {e}", file=sys.stderr)
            return []

    def _check_yaml_validity(self):
        """Check YAML validity of observer_guardrails.yaml."""
        print("\n🔍 Checking YAML validity...")

        yaml_path = self.workspace / "specs" / "observer_guardrails.yaml"

        if not yaml_path.exists():
            self.errors.append(
                CheckResult(
                    name="YAML Validity",
                    status="error",
                    message="specs/observer_guardrails.yaml not found",
                    remediation="Create specs/observer_guardrails.yaml with required guardrails",
                )
            )
            return

        self.files_checked.append(str(yaml_path))

        try:
            if YAML_AVAILABLE:
                with open(yaml_path) as f:
                    data = yaml.safe_load(f)

                # Validate required keys
                required_keys = [
                    ("observer_guardrails", "runtime_constraints", "latency_ms", "max"),
                    (
                        "observer_guardrails",
                        "runtime_constraints",
                        "uptime_percent",
                        "target",
                    ),
                    (
                        "observer_guardrails",
                        "governance_compliance",
                        "requires_spec_reference",
                    ),
                    (
                        "observer_guardrails",
                        "security_and_privacy",
                        "secrets_scanning_enabled",
                    ),
                ]

                for key_path in required_keys:
                    obj = data
                    for key in key_path:
                        if not isinstance(obj, dict) or key not in obj:
                            self.errors.append(
                                CheckResult(
                                    name="YAML Validity",
                                    status="error",
                                    message=f"Missing required key: {'.'.join(key_path)}",
                                    remediation=f"Add {'.'.join(key_path)} to observer_guardrails.yaml",
                                )
                            )
                            return
                        obj = obj[key]

                print("  ✅ YAML structure is valid")
            else:
                # Fallback: just check file is readable
                with open(yaml_path) as f:
                    content = f.read()
                    if not content.strip():
                        self.errors.append(
                            CheckResult(
                                name="YAML Validity",
                                status="error",
                                message="observer_guardrails.yaml is empty",
                                remediation="Add guardrails configuration to the file",
                            )
                        )
                        return
                print("  ✅ YAML file is readable (full validation skipped)")

        except Exception as e:
            self.errors.append(
                CheckResult(
                    name="YAML Validity",
                    status="error",
                    message=f"Failed to parse YAML: {str(e)}",
                    remediation="Fix YAML syntax errors in observer_guardrails.yaml",
                )
            )

    def _check_threshold_consistency(self):
        """Check threshold consistency across all files."""
        print("\n🔍 Checking threshold consistency...")

        thresholds_found = {
            "uptime_warn": [],
            "uptime_fail": [],
            "latency_warn": [],
            "latency_fail": [],
            "drift_warn": [],
            "drift_fail": [],
        }

        # Check observer_guardrails.yaml
        yaml_path = self.workspace / "specs" / "observer_guardrails.yaml"
        if yaml_path.exists():
            content = yaml_path.read_text()

            # Extract uptime thresholds
            if match := re.search(
                r"uptime.*?warn.*?(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["uptime_warn"].append(
                    ("observer_guardrails.yaml", float(match.group(1)))
                )
            if match := re.search(
                r"uptime.*?fail.*?(\d+(?:\.\d+)?)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["uptime_fail"].append(
                    ("observer_guardrails.yaml", float(match.group(1)))
                )

            # Extract latency thresholds
            if match := re.search(
                r"latency.*?warn.*?(\d+)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["latency_warn"].append(
                    ("observer_guardrails.yaml", int(match.group(1)))
                )
            if match := re.search(
                r"latency.*?fail.*?(\d+)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["latency_fail"].append(
                    ("observer_guardrails.yaml", int(match.group(1)))
                )

            # Extract drift thresholds
            if match := re.search(
                r"drift.*?warn.*?(\d+)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["drift_warn"].append(
                    ("observer_guardrails.yaml", int(match.group(1)))
                )
            if match := re.search(
                r"drift.*?fail.*?(\d+)", content, re.IGNORECASE | re.DOTALL
            ):
                thresholds_found["drift_fail"].append(
                    ("observer_guardrails.yaml", int(match.group(1)))
                )

        # Check render_integration.md
        render_md_path = self.workspace / "specs" / "render_integration.md"
        if render_md_path.exists():
            content = render_md_path.read_text()

            # Look for thresholds in markdown (often in code blocks or tables)
            if match := re.search(r"99(?:\.\d+)?%", content):
                thresholds_found["uptime_warn"].append(("render_integration.md", 99.0))
            if match := re.search(r"98(?:\.\d+)?%", content):
                thresholds_found["uptime_fail"].append(("render_integration.md", 98.0))
            if match := re.search(r"2500\s*ms", content):
                thresholds_found["latency_warn"].append(("render_integration.md", 2500))
            if match := re.search(r"4000\s*ms", content):
                thresholds_found["latency_fail"].append(("render_integration.md", 4000))

        # Check pr-governance-check.yml
        workflow_path = (
            self.workspace / ".github" / "workflows" / "pr-governance-check.yml"
        )
        if workflow_path.exists():
            content = workflow_path.read_text()

            # Look for numeric thresholds in bash comparisons
            if match := re.search(r"UPTIME\s*<\s*98", content):
                thresholds_found["uptime_fail"].append(
                    ("pr-governance-check.yml", 98.0)
                )
            if match := re.search(r"LATENCY\s*>\s*4000", content):
                thresholds_found["latency_fail"].append(
                    ("pr-governance-check.yml", 4000)
                )
            if match := re.search(r"DRIFT\s*>\s*5", content):
                thresholds_found["drift_fail"].append(("pr-governance-check.yml", 5))

        # Verify consistency
        for threshold_name, expected_value in self.EXPECTED_THRESHOLDS.items():
            found_values = thresholds_found[threshold_name]

            if not found_values:
                self.warnings.append(
                    CheckResult(
                        name="Threshold Consistency",
                        status="warning",
                        message=f"Threshold {threshold_name} not found in any file",
                        remediation=f"Add {threshold_name}={expected_value} to relevant files",
                    )
                )
                continue

            # Check if all values match expected
            mismatches = [(f, v) for f, v in found_values if v != expected_value]
            if mismatches:
                mismatch_str = ", ".join([f"{f}={v}" for f, v in mismatches])

                # Track mismatches for diff table
                for file, value in mismatches:
                    self.mismatches.append(
                        ThresholdMismatch(
                            metric=threshold_name,
                            expected=expected_value,
                            found=value,
                            source_file=file,
                        )
                    )

                self.errors.append(
                    CheckResult(
                        name="Threshold Consistency",
                        status="error",
                        message=f"Threshold {threshold_name} mismatch: expected {expected_value}, found {mismatch_str}",
                        remediation=f"Update all files to use {threshold_name}={expected_value}",
                        details={"expected": expected_value, "found": dict(mismatches)},
                    )
                )

                if self.debug:
                    print(f"  🔍 DEBUG: {threshold_name} mismatches: {mismatches}")
            else:
                print(f"  ✅ {threshold_name} = {expected_value} (consistent)")

    def _check_secrets_presence(self):
        """Check secrets references and documentation."""
        print("\n🔍 Checking secrets presence and documentation...")

        workflow_path = (
            self.workspace / ".github" / "workflows" / "pr-governance-check.yml"
        )
        render_doc_path = self.workspace / "specs" / "render_integration.md"
        slack_doc_path = self.workspace / "specs" / "slack_integration.md"

        if not workflow_path.exists():
            self.warnings.append(
                CheckResult(
                    name="Secrets Check",
                    status="warning",
                    message="pr-governance-check.yml not found",
                    remediation="Create workflow file with secrets configuration",
                )
            )
            return

        workflow_content = workflow_path.read_text()
        render_doc_content = (
            render_doc_path.read_text() if render_doc_path.exists() else ""
        )
        slack_doc_content = (
            slack_doc_path.read_text() if slack_doc_path.exists() else ""
        )

        for secret in self.REQUIRED_SECRETS:
            secret_name = secret.split(".")[-1]

            # Check if referenced in workflow
            if secret not in workflow_content:
                self.warnings.append(
                    CheckResult(
                        name="Secrets Check",
                        status="warning",
                        message=f"Secret {secret} not referenced in workflow",
                        remediation=f"Add {secret} reference to pr-governance-check.yml",
                    )
                )
                continue

            # Check if documented
            is_documented = False
            if "RENDER" in secret_name:
                is_documented = secret_name in render_doc_content
                doc_file = "render_integration.md"
            elif "SLACK" in secret_name:
                is_documented = secret_name in slack_doc_content
                doc_file = "slack_integration.md"
            else:
                is_documented = True  # Skip unknown secrets

            if not is_documented:
                self.warnings.append(
                    CheckResult(
                        name="Secrets Documentation",
                        status="warning",
                        message=f"Secret {secret_name} used but not documented in specs/{doc_file}",
                        remediation=f"Document {secret_name} setup in specs/{doc_file}",
                    )
                )
            else:
                print(f"  ✅ {secret_name} referenced and documented")

    def _check_observer_charter_sync(self):
        """Check Observer Charter alignment with MCP architecture."""
        print("\n🔍 Checking Observer Charter sync...")

        mcp_path = self.workspace / "specs" / "mcp-architecture.md"

        if not mcp_path.exists():
            self.warnings.append(
                CheckResult(
                    name="Observer Charter Sync",
                    status="warning",
                    message="specs/mcp-architecture.md not found",
                    remediation="Create MCP architecture documentation",
                )
            )
            return

        self.files_checked.append(str(mcp_path))
        content = mcp_path.read_text()

        # Check for Alert Loop Diagram section
        required_elements = [
            ("Alert Loop", "Alert Loop Diagram or section"),
            ("Render", "Render service reference"),
            ("Governance", "Governance reference"),
            ("Slack", "Slack integration reference"),
            ("Observer", "Observer component reference"),
        ]

        missing_elements = []
        for element, description in required_elements:
            if not re.search(rf"\b{element}\b", content, re.IGNORECASE):
                missing_elements.append(description)

        if missing_elements:
            self.warnings.append(
                CheckResult(
                    name="Observer Charter Sync",
                    status="warning",
                    message=f"MCP architecture missing elements: {', '.join(missing_elements)}",
                    remediation="Update specs/mcp-architecture.md with complete Alert Loop diagram showing: Render → Governance → Slack → Observer",
                )
            )
        else:
            print("  ✅ Observer Charter contains required Alert Loop elements")

    def _check_guardrails_alignment(self):
        """Check guardrails alignment with expected values."""
        print("\n🔍 Checking guardrails alignment...")

        yaml_path = self.workspace / "specs" / "observer_guardrails.yaml"

        if not yaml_path.exists():
            # Already reported in YAML validity check
            return

        content = yaml_path.read_text()

        # Check audit trail retention
        if match := re.search(r"audit_trail_retention_days\s*:\s*(\d+)", content):
            retention_days = int(match.group(1))
            if retention_days < 180:
                self.warnings.append(
                    CheckResult(
                        name="Guardrails Alignment",
                        status="warning",
                        message=f"Audit trail retention ({retention_days} days) below recommended 180 days",
                        remediation="Set audit_trail_retention_days >= 180 in observer_guardrails.yaml",
                    )
                )
            else:
                print(f"  ✅ Audit trail retention = {retention_days} days (>= 180)")
        else:
            self.warnings.append(
                CheckResult(
                    name="Guardrails Alignment",
                    status="warning",
                    message="audit_trail_retention_days not found in guardrails",
                    remediation="Add audit_trail_retention_days >= 180 to observer_guardrails.yaml",
                )
            )

        # Check coverage threshold
        if match := re.search(r"min_coverage_percent\s*:\s*(\d+)", content):
            coverage = int(match.group(1))
            if coverage < 85:
                self.warnings.append(
                    CheckResult(
                        name="Guardrails Alignment",
                        status="warning",
                        message=f"Minimum coverage ({coverage}%) below recommended 85%",
                        remediation="Set min_coverage_percent >= 85 in observer_guardrails.yaml",
                    )
                )
            else:
                print(f"  ✅ Minimum coverage = {coverage}% (>= 85)")
        else:
            self.warnings.append(
                CheckResult(
                    name="Guardrails Alignment",
                    status="warning",
                    message="min_coverage_percent not found in guardrails",
                    remediation="Add min_coverage_percent >= 85 to observer_guardrails.yaml",
                )
            )

    def generate_slack_alert(self) -> str:
        """Generate Slack alert message for QA failures."""
        pr_number = os.getenv("GITHUB_PR_NUMBER", os.getenv("PR_NUMBER", "unknown"))
        repo = os.getenv("GITHUB_REPOSITORY", "unknown/unknown")

        error_count = len(self.errors)
        warning_count = len(self.warnings)

        # Build message
        message = f"🚨 Governance QA Check Failed on PR #{pr_number}\\n"
        message += f"❌ {error_count} Error{'s' if error_count != 1 else ''} | "
        message += f"⚠️ {warning_count} Warning{'s' if warning_count != 1 else ''}\\n"

        # Add top 3 mismatches
        if self.mismatches:
            for _i, mismatch in enumerate(self.mismatches[:3], 1):
                message += f"• {mismatch.metric} expected {mismatch.expected}, found {mismatch.found}\\n"

            if len(self.mismatches) > 3:
                message += f"...and {len(self.mismatches) - 3} more\\n"

        # Add PR link
        message += f"🔗 https://github.com/{repo}/pull/{pr_number}"

        return message

    def save_json_artifact(self):
        """Save machine-readable artifact for drift tracking."""
        pr_number = os.getenv("GITHUB_PR_NUMBER", os.getenv("PR_NUMBER", "unknown"))

        artifact = {
            "pr_number": pr_number,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "metrics_mismatched": [m.metric for m in self.mismatches],
            "mismatches": [
                {
                    "metric": m.metric,
                    "expected": m.expected,
                    "found": m.found,
                    "source_file": m.source_file,
                }
                for m in self.mismatches
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "files_checked": self.files_checked,
        }

        artifact_path = self.workspace / "qa_results.json"
        artifact_path.write_text(json.dumps(artifact, indent=2))
        print(f"💾 JSON artifact saved to: {artifact_path}")

        return artifact

    def _generate_output(self, skip: bool = False) -> dict[str, Any]:
        """Generate JSON output and markdown report."""
        if skip:
            result = {
                "status": "skipped",
                "errors": [],
                "warnings": [],
                "files_checked": [],
            }
        else:
            result = {
                "status": "fail" if self.errors else "pass",
                "errors": [self._result_to_dict(e) for e in self.errors],
                "warnings": [self._result_to_dict(w) for w in self.warnings],
                "files_checked": self.files_checked,
            }

        # Print JSON to stdout
        print("\n" + "=" * 80)
        print(json.dumps(result, indent=2))

        # Generate markdown report
        self._generate_markdown_report(result, skip)

        # Save JSON artifact (always, for drift tracking)
        if not skip:
            self.save_json_artifact()

        return result

    def _result_to_dict(self, result: CheckResult) -> dict[str, Any]:
        """Convert CheckResult to dictionary."""
        return {
            "check": result.name,
            "status": result.status,
            "message": result.message,
            "remediation": result.remediation,
            "details": result.details,
        }

    def _generate_markdown_report(self, result: dict[str, Any], skip: bool = False):
        """Generate markdown report file."""
        md_path = self.workspace / "qa_summary.md"

        if skip:
            content = """## 🧪 QA Consistency Report

**Status:** ⏭️ Skipped

No relevant observability/governance files were changed in this PR.

---
*QA Observability & Governance Consistency Check*
"""
        else:
            status_emoji = "✅" if result["status"] == "pass" else "❌"
            error_count = len(result["errors"])
            warning_count = len(result["warnings"])

            content = f"""## 🧪 QA Consistency Report

**Status:** {status_emoji} {"PASSED" if result["status"] == "pass" else "FAILED"}

**Summary:**
- Errors: {error_count}
- Warnings: {warning_count}
- Files Checked: {len(result["files_checked"])}

### Check Results

| Check | Status | Message |
|-------|--------|---------|
"""

            # Add errors
            for error in result["errors"]:
                content += f"| {error['check']} | ❌ Error | {error['message']} |\n"

            # Add warnings
            for warning in result["warnings"]:
                content += (
                    f"| {warning['check']} | ⚠️  Warning | {warning['message']} |\n"
                )

            # If no issues, show success
            if not result["errors"] and not result["warnings"]:
                content += "| All Checks | ✅ Pass | All consistency checks passed |\n"

            # Add Smart Diff Table if there are mismatches
            if self.mismatches:
                content += "\n### 🔍 Threshold Mismatches (Diff Table)\n\n"
                content += "| Metric | Expected | Found | Source File | Status |\n"
                content += "|--------|----------|-------|-------------|--------|\n"

                for mismatch in self.mismatches:
                    content += f"| {mismatch.metric} | {mismatch.expected} | {mismatch.found} | "
                    content += f"{mismatch.source_file} | ❌ |\n"

            # Add remediation section
            if result["errors"] or result["warnings"]:
                content += "\n### 📋 How to Fix\n\n"

                for error in result["errors"]:
                    if error.get("remediation"):
                        content += f"- **{error['check']}:** {error['remediation']}\n"

                for warning in result["warnings"]:
                    if warning.get("remediation"):
                        content += (
                            f"- **{warning['check']}:** {warning['remediation']}\n"
                        )

            content += "\n---\n*QA Observability & Governance Consistency Check*\n"

        md_path.write_text(content)
        print(f"\n📝 Markdown report written to: {md_path}")


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="QA Observability & Governance Consistency Checker"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output with detailed parsing results",
    )
    parser.add_argument(
        "--slack-payload",
        action="store_true",
        help="Output Slack alert message and exit (for CI integration)",
    )
    args = parser.parse_args()

    # Get SHAs from environment
    base_sha = os.getenv("GITHUB_BASE_SHA")
    head_sha = os.getenv("GITHUB_HEAD_SHA")

    # Create checker and run
    checker = ConsistencyChecker(base_sha=base_sha, head_sha=head_sha, debug=args.debug)

    # If --slack-payload mode, run checks and output message
    if args.slack_payload:
        result = checker.run()
        if result["status"] == "fail":
            slack_message = checker.generate_slack_alert()
            # Output as JSON-safe escaped string for shell consumption
            print(slack_message)
            sys.exit(0)
        else:
            # No alert needed if checks passed
            sys.exit(0)

    # Normal mode: run checks and exit with code
    result = checker.run()

    # Exit with appropriate code
    if result["status"] == "fail":
        print("\n❌ QA consistency checks failed!", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✅ QA consistency checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
