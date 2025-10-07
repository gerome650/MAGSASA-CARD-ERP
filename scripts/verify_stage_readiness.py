#!/usr/bin/env python3
"""
🧩 POST-STAGE VERIFICATION SCRIPT — 6.7 → 6.8.1 READINESS AUDIT 🛠️

This CLI tool automatically audits the repository and validates whether
Stages 6.7, 6.8, and 6.8.1 have been properly committed, pushed, tested,
and are ready for Stage 7.

Usage:
    python scripts/verify_stage_readiness.py [--strict] [--ci] [--json-output FILE]

Options:
    --strict     Fail if test coverage < 80%
    --ci         Exit with code 1 if any check fails (for CI pipelines)
    --json-output FILE    Write results to JSON file for dashboards
    --help       Show this help message
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    END = "\033[0m"


class StageReadinessVerifier:
    """Main verification class for Stage 6.7 → 6.8.1 readiness."""

    def __init__(self, strict_mode: bool = False, ci_mode: bool = False):
        self.strict_mode = strict_mode
        self.ci_mode = ci_mode
        self.repo_root = Path(__file__).parent.parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {"passed": 0, "warnings": 0, "failures": 0},
            "ready_for_stage_7": False,
        }

        # Required files for each stage
        self.stage_6_7_files = [
            "observability/metrics/metrics_middleware.py",
            "observability/tracing/otel_tracer.py",
            "observability/logging/structured_logger.py",
            "observability/prometheus.yml",
            "observability/alertmanager.yml",
        ]

        self.stage_6_8_files = [
            "observability/alerts/promql_rules.yml",
            "observability/alerts/anomaly_strategies.py",
            "observability/alerts/notifier.py",
            "observability/dashboards/service_dashboard.json",
        ]

        self.stage_6_8_1_files = [
            "observability/ai_agent/incident_analyzer.py",
            "observability/ai_agent/postmortem_generator.py",
            "observability/ai_agent/integrations/slack_bot.py",
            "observability/ai_agent/main.py",
        ]

        self.ci_files = [
            ".github/workflows/observability.yml",
            ".github/workflows/ci.yml",
        ]

        self.required_dependencies = [
            "prometheus-client",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-instrumentation-flask",
            "numpy",
            "scipy",
        ]

    def log(self, message: str, color: str = Colors.WHITE, prefix: str = "🔍") -> None:
        """Print colored log message."""
        if not self.ci_mode:  # Don't use colors in CI mode
            print(f"{color}{prefix} {message}{Colors.END}")
        else:
            print(f"{prefix} {message}")

    def success(self, message: str) -> None:
        """Log success message."""
        self.log(f"✅ {message}", Colors.GREEN)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.log(f"⚠️ {message}", Colors.YELLOW)

    def error(self, message: str) -> None:
        """Log error message."""
        self.log(f"❌ {message}", Colors.RED)

    def info(self, message: str) -> None:
        """Log info message."""
        self.log(f"ℹ️ {message}", Colors.BLUE)

    def run_command(
        self, command: str, cwd: Path | None = None
    ) -> tuple[int, str, str]:
        """Run shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"

    def check_git_status(self) -> dict[str, Any]:
        """Check git repository state."""
        self.log("Git State Validation", Colors.CYAN, "📦")
        check_result = {"passed": True, "issues": []}

        # Check for uncommitted changes
        exit_code, stdout, stderr = self.run_command("git status --porcelain")
        if exit_code != 0:
            check_result["passed"] = False
            check_result["issues"].append("Failed to check git status")
            self.error("Failed to check git status")
            return check_result

        if stdout.strip():
            check_result["passed"] = False
            check_result["issues"].append("Uncommitted changes detected")
            self.error("Uncommitted changes detected:")
            for line in stdout.strip().split("\n"):
                self.error(f"  {line}")
        else:
            self.success("Clean working tree")

        # Check current branch
        exit_code, branch, _ = self.run_command("git rev-parse --abbrev-ref HEAD")
        if exit_code == 0:
            self.info(f"On branch: {branch.strip()}")
            if branch.strip() not in [
                "main",
                "develop",
            ] and not branch.strip().startswith("feature/"):
                check_result["issues"].append(
                    f"Not on expected branch (current: {branch.strip()})"
                )
                self.warning(f"Not on expected branch (current: {branch.strip()})")
        else:
            check_result["passed"] = False
            check_result["issues"].append("Failed to determine current branch")

        # Check for observability-related commits
        exit_code, stdout, _ = self.run_command(
            "git log --oneline -20 --grep='observability\\|runtime-intelligence\\|ai-incident-agent\\|Stage 6.7\\|Stage 6.8'"
        )

        if exit_code == 0 and stdout.strip():
            commits = stdout.strip().split("\n")
            self.success(f"Found {len(commits)} observability-related commits")
            check_result["commits_found"] = len(commits)
        else:
            check_result["issues"].append(
                "No observability-related commits found in recent history"
            )
            self.warning("No observability-related commits found in recent history")

        return check_result

    def check_file_structure(self) -> dict[str, Any]:
        """Check that all required files exist."""
        self.log("File Structure Validation", Colors.CYAN, "📁")
        check_result = {"passed": True, "missing_files": []}

        # Check Stage 6.7 files
        self.log("Stage 6.7 – Observability Checks", Colors.MAGENTA)
        for file_path in self.stage_6_7_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                self.success(f"{file_path} found")
            else:
                check_result["passed"] = False
                check_result["missing_files"].append(file_path)
                self.error(f"{file_path} missing")

        # Check Stage 6.8 files
        self.log("Stage 6.8 – Runtime Intelligence Checks", Colors.MAGENTA)
        for file_path in self.stage_6_8_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                self.success(f"{file_path} found")
            else:
                check_result["passed"] = False
                check_result["missing_files"].append(file_path)
                self.error(f"{file_path} missing")

        # Check Stage 6.8.1 files
        self.log("Stage 6.8.1 – AI Agent Checks", Colors.MAGENTA)
        for file_path in self.stage_6_8_1_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                self.success(f"{file_path} found")
            else:
                check_result["passed"] = False
                check_result["missing_files"].append(file_path)
                self.error(f"{file_path} missing")

        # Check CI files
        self.log("CI Workflow Checks", Colors.MAGENTA)
        for file_path in self.ci_files:
            full_path = self.repo_root / file_path
            if full_path.exists():
                self.success(f"{file_path} found")
            else:
                check_result["missing_files"].append(file_path)
                self.warning(f"{file_path} missing (non-critical)")

        return check_result

    def check_dependencies(self) -> dict[str, Any]:
        """Check that required dependencies are present."""
        self.log("Dependency Validation", Colors.CYAN, "📦")
        check_result = {"passed": True, "missing_deps": [], "found_deps": []}

        # Check main requirements.txt
        req_file = self.repo_root / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                req_content = f.read()

            for dep in self.required_dependencies:
                if dep in req_content:
                    check_result["found_deps"].append(dep)
                    self.success(f"{dep} found in requirements.txt")
                else:
                    check_result["missing_deps"].append(dep)
                    self.warning(f"{dep} missing from requirements.txt")

        # Check observability requirements
        obs_req_file = (
            self.repo_root / "observability" / "observability_requirements.txt"
        )
        if obs_req_file.exists():
            with open(obs_req_file) as f:
                obs_content = f.read()

            ml_deps = ["numpy", "scipy", "statsmodels"]
            for dep in ml_deps:
                if dep in obs_content:
                    self.success(f"{dep} found in observability requirements")
                else:
                    self.warning(f"{dep} missing from observability requirements")

        if check_result["missing_deps"]:
            check_result["passed"] = False

        return check_result

    def check_tests(self) -> dict[str, Any]:
        """Run tests and check coverage."""
        self.log("Test Validation", Colors.CYAN, "🧪")
        check_result = {"passed": True, "test_results": {}, "coverage": 0}

        # Check if pytest is available
        exit_code, _, _ = self.run_command("python -m pytest --version")
        if exit_code != 0:
            check_result["passed"] = False
            check_result["test_results"]["error"] = "pytest not available"
            self.error("pytest not available")
            return check_result

        # Run tests
        self.info("Running tests...")
        exit_code, stdout, stderr = self.run_command("python -m pytest -q --tb=short")

        if exit_code == 0:
            self.success("All tests passed")
            check_result["test_results"]["status"] = "passed"

            # Extract test count from output
            test_match = re.search(r"(\d+) passed", stdout)
            if test_match:
                test_count = int(test_match.group(1))
                self.success(f"Tests passed: {test_count}")
                check_result["test_results"]["count"] = test_count
        else:
            check_result["passed"] = False
            check_result["test_results"]["status"] = "failed"
            check_result["test_results"]["output"] = stdout + stderr
            self.error("Some tests failed")

        # Check coverage if available
        exit_code, stdout, _ = self.run_command(
            "python -m pytest --cov=observability --cov-report=term-missing -q"
        )
        if exit_code == 0:
            coverage_match = re.search(r"TOTAL.*?(\d+)%", stdout)
            if coverage_match:
                coverage = int(coverage_match.group(1))
                check_result["coverage"] = coverage
                if coverage >= 80:
                    self.success(f"Coverage: {coverage}%")
                else:
                    self.warning(f"Coverage: {coverage}% (<80%)")
                    if self.strict_mode:
                        check_result["passed"] = False

        return check_result

    def check_ci_workflows(self) -> dict[str, Any]:
        """Validate CI workflow files."""
        self.log("CI Workflow Validation", Colors.CYAN, "🔧")
        check_result = {"passed": True, "workflow_issues": []}

        workflows_dir = self.repo_root / ".github" / "workflows"
        if not workflows_dir.exists():
            check_result["passed"] = False
            check_result["workflow_issues"].append("No .github/workflows directory")
            self.error("No .github/workflows directory")
            return check_result

        # Check each workflow file
        for workflow_file in workflows_dir.glob("*.yml"):
            self.info(f"Validating {workflow_file.name}...")
            try:
                with open(workflow_file) as f:
                    yaml.safe_load(f)
                self.success(f"{workflow_file.name} is valid YAML")
            except yaml.YAMLError as e:
                check_result["passed"] = False
                check_result["workflow_issues"].append(
                    f"Invalid YAML in {workflow_file.name}: {e}"
                )
                self.error(f"Invalid YAML in {workflow_file.name}")

        # Check for observability workflow
        obs_workflow = workflows_dir / "observability.yml"
        if obs_workflow.exists():
            with open(obs_workflow) as f:
                content = f.read()

            if "validate_alert_rules.py" in content:
                self.success("observability.yml references validate_alert_rules.py")
            else:
                self.warning(
                    "observability.yml doesn't reference validate_alert_rules.py"
                )

            if "check_observability_hooks.py" in content:
                self.success(
                    "observability.yml references check_observability_hooks.py"
                )
            else:
                self.warning(
                    "observability.yml doesn't reference check_observability_hooks.py"
                )

        return check_result

    def generate_summary_report(self) -> None:
        """Generate final summary report."""
        self.log("Summary Report", Colors.CYAN, "📊")

        len(self.results["checks"])
        sum(
            1 for check in self.results["checks"].values() if check.get("passed", False)
        )

        # Count issues
        for _check_name, check_result in self.results["checks"].items():
            if check_result.get("passed", False):
                self.results["summary"]["passed"] += 1
            elif check_result.get("issues") and len(check_result["issues"]) > 0:
                critical_issues = [
                    issue
                    for issue in check_result["issues"]
                    if "missing" in issue.lower() or "failed" in issue.lower()
                ]
                if critical_issues:
                    self.results["summary"]["failures"] += 1
                else:
                    self.results["summary"]["warnings"] += 1
            else:
                self.results["summary"]["warnings"] += 1

        # Determine if ready for Stage 7
        critical_failures = self.results["summary"]["failures"] == 0
        self.results["ready_for_stage_7"] = critical_failures

        # Print summary
        print(f"\n{Colors.BOLD}📋 VERIFICATION SUMMARY{Colors.END}")
        print(
            f"{Colors.GREEN}✅ Passed: {self.results['summary']['passed']}{Colors.END}"
        )
        print(
            f"{Colors.YELLOW}⚠️ Warnings: {self.results['summary']['warnings']}{Colors.END}"
        )
        print(
            f"{Colors.RED}❌ Failures: {self.results['summary']['failures']}{Colors.END}"
        )

        if self.results["ready_for_stage_7"]:
            self.success("All critical checks passed. Safe to proceed to Stage 7.")
            print(
                f"\n{Colors.GREEN}{Colors.BOLD}🚀 RESULT: READY FOR STAGE 7{Colors.END}"
            )
        else:
            self.error("Critical issues found. NOT ready for Stage 7.")
            print(
                f"\n{Colors.RED}{Colors.BOLD}🚫 RESULT: NOT READY FOR STAGE 7{Colors.END}"
            )

            # List critical issues
            print(f"\n{Colors.RED}{Colors.BOLD}Critical Issues:{Colors.END}")
            for check_name, check_result in self.results["checks"].items():
                if not check_result.get("passed", False) and check_result.get("issues"):
                    critical_issues = [
                        issue
                        for issue in check_result["issues"]
                        if "missing" in issue.lower() or "failed" in issue.lower()
                    ]
                    for issue in critical_issues:
                        print(f"  {Colors.RED}❌ {check_name}: {issue}{Colors.END}")

    def run_verification(self) -> bool:
        """Run all verification checks."""
        self.log(
            "Starting Stage 6.7 → 6.8.1 Readiness Audit",
            Colors.BOLD + Colors.CYAN,
            "🧩",
        )

        # Run all checks
        self.results["checks"]["git_status"] = self.check_git_status()
        self.results["checks"]["file_structure"] = self.check_file_structure()
        self.results["checks"]["dependencies"] = self.check_dependencies()
        self.results["checks"]["tests"] = self.check_tests()
        self.results["checks"]["ci_workflows"] = self.check_ci_workflows()

        # Generate summary
        self.generate_summary_report()

        return self.results["ready_for_stage_7"]

    def save_json_report(self, filename: str) -> None:
        """Save results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        self.info(f"Results saved to {filename}")


def main(_):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Verify Stage 6.7 → 6.8.1 readiness for Stage 7"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if test coverage less than 80 percent",
    )

    parser.add_argument(
        "--ci",
        action="store_true",
        help="Exit with code 1 if any check fails (for CI pipelines)",
    )

    parser.add_argument(
        "--json-output", type=str, help="Write results to JSON file for dashboards"
    )

    args = parser.parse_args()

    # Run verification
    verifier = StageReadinessVerifier(strict_mode=args.strict, ci_mode=args.ci)
    success = verifier.run_verification()

    # Save JSON report if requested and if args.json_output:

    # Exit with appropriate code
    if args.ci and not success or not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
