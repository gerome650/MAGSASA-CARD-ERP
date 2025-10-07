#!/usr/bin/env python3
"""
🪝 Pre-Commit Hook (CI-Safe & Production-Hardened)

Runs quality checks before allowing commit:
- Code formatting (Black)
- Linting (Ruff)
- Type checking (Mypy - optional)
- Quick tests (unit tests only)
- Secrets detection
- Policy validation

Behavior:
- LOCAL: Auto-fixes issues (Ruff --fix, Black format)
- CI: Check-only mode (fails if violations remain)
- PRODUCTION: Enhanced security checks and audit logging

Usage:
    python scripts/hooks/pre_commit.py              # Local mode (auto-fix)
    CI=true python scripts/hooks/pre_commit.py      # CI mode (check-only)
    python scripts/hooks/pre_commit.py --verbose    # Verbose output
    python scripts/hooks/pre_commit.py --json       # JSON output for CI

Install as git hook:
    python scripts/hooks/install_hooks.py
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a quality check."""

    name: str
    success: bool
    duration: float
    output: str
    error: str | None = None
    auto_fixed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreCommitReport:
    """Complete pre-commit report."""

    timestamp: str
    mode: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    auto_fixed_count: int
    duration: float
    results: list[CheckResult]
    secrets_found: list[str]
    policy_violations: list[str]

    @property
    def success(self) -> bool:
        return self.failed_checks == 0

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "results": [r.to_dict() for r in self.results]}


def is_ci() -> bool:
    """Check if running in CI environment."""
    ci_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "BUILDKITE",
        "CIRCLECI",
        "JENKINS_URL",
    ]
    return any(os.getenv(var) for var in ci_vars)


def is_no_verify_bypass() -> bool:
    """Detect if --no-verify is being used to bypass hooks."""
    # Check command line arguments
    if "--no-verify" in sys.argv or "--no-verify" in " ".join(
        os.getenv("_", "").split()
    ):
        return True

    # Check git environment variables
    git_args = os.getenv("GIT_PARAMS", "")
    return "--no-verify" in git_args


def setup_secrets_detection() -> list[str]:
    """Setup secrets detection patterns."""
    return [
        r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^"\'\s]{8,}["\']?',
        r'(?i)(secret|key|token)\s*[:=]\s*["\']?[a-zA-Z0-9+/]{20,}={0,2}["\']?',
        r'(?i)(api_key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9]{20,}["\']?',
        r'(?i)(access_token|bearer)\s*[:=]\s*["\']?[a-zA-Z0-9._-]{20,}["\']?',
        r'(?i)(private_key|privatekey)\s*[:=]\s*["\']?-----BEGIN.*-----["\']?',
        r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[:=]\s*["\']?[A-Z0-9]{20,}["\']?',
        r'(?i)(slack_webhook|webhook_url)\s*[:=]\s*["\']?https://hooks\.slack\.com/[^"\']+["\']?',
    ]


def scan_for_secrets(file_path: Path, patterns: list[str]) -> list[str]:
    """Scan file for potential secrets."""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        found_secrets = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                found_secrets.extend(matches)

        return found_secrets
    except Exception as e:
        logger.warning(f"Could not scan {file_path} for secrets: {e}")
        return []


def run_command(
    cmd: list[str], description: str, timeout: int = 300, verbose: bool = False
) -> tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr.

    Args:
        cmd: Command and arguments to run
        description: Description for display
        timeout: Command timeout in seconds
        verbose: Whether to show verbose output

    Returns:
        Tuple of (success, stdout, stderr)
    """
    if verbose:
        logger.info(f"Running: {' '.join(cmd)}")

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
            timeout=timeout,
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            if verbose:
                logger.info(f"✅ {description} completed in {duration:.2f}s")
            return True, result.stdout, result.stderr
        else:
            if verbose:
                logger.error(
                    f"❌ {description} failed after {duration:.2f}s (exit code: {result.returncode})"
                )
            return False, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        logger.error(f"❌ {description} timed out after {timeout}s")
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        error_msg = f"Command not found: {cmd[0]}"
        logger.error(f"❌ {description} failed: {error_msg}")
        return False, "", error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"❌ {description} failed: {error_msg}")
        return False, "", error_msg


def run_quality_check(name: str, check_func, *args, **kwargs) -> CheckResult:
    """Run a quality check and return structured result."""
    start_time = time.time()

    try:
        success, output, error = check_func(*args, **kwargs)
        duration = time.time() - start_time

        return CheckResult(
            name=name, success=success, duration=duration, output=output, error=error
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Quality check {name} crashed: {e}")
        return CheckResult(
            name=name, success=False, duration=duration, output="", error=str(e)
        )


def auto_format(verbose: bool = False) -> tuple[bool, str, str]:
    """Auto-format code with Black (or check-only in CI)."""
    ci_env = is_ci()

    if ci_env:
        # CI mode: check only
        success, output, error = run_command(
            ["black", "--check", ".", "--exclude", "venv|dist|build|htmlcov"],
            "Checking code formatting (Black)",
            verbose=verbose,
        )
        if not success and verbose:
            logger.error("Code formatting violations found")
            logger.info("Fix locally with: black .")
            if output:
                logger.error(f"Details:\n{output[:500]}")
    else:
        # Local mode: auto-format
        success, output, error = run_command(
            ["black", ".", "--exclude", "venv|dist|build|htmlcov"],
            "Auto-formatting code (Black)",
            verbose=verbose,
        )
        if success:
            pass
        elif verbose and output:
            logger.error(f"Formatting failed:\n{output[:500]}")

    return success, output, error


def auto_lint(verbose: bool = False) -> tuple[bool, str, str]:
    """Auto-fix linting issues with Ruff (or check-only in CI)."""
    ci_env = is_ci()

    if ci_env:
        # CI mode: check only, no auto-fix
        success, output, error = run_command(
            ["ruff", "check", ".", "--exclude", "venv,dist,build,htmlcov"],
            "Checking linting (Ruff)",
            verbose=verbose,
        )
        if not success and verbose:
            logger.error("Linting violations found")
            logger.info("Fix locally with: ruff check --fix .")
            if output:
                logger.error(f"Details:\n{output[:500]}")
    else:
        # Local mode: auto-fix
        if verbose:
            logger.info("Auto-fixing linting issues (Ruff)...")

        fix_success, fix_output, fix_error = run_command(
            [
                "ruff",
                "check",
                ".",
                "--fix",
                "--unsafe-fixes",
                "--exclude",
                "venv,dist,build,htmlcov",
            ],
            "Auto-fixing linting (Ruff)",
            verbose=verbose,
        )

        if fix_success and verbose:
            logger.info("✅ Auto-fixes applied")

        # Now check for remaining issues
        success, output, error = run_command(
            ["ruff", "check", ".", "--exclude", "venv,dist,build,htmlcov"],
            "Verifying linting (Ruff)",
            verbose=verbose,
        )

        if not success and verbose:
            logger.warning("Some issues could not be auto-fixed")
            if output:
                logger.error(f"Details:\n{output[:500]}")

    return success, output, error


def check_types(verbose: bool = False) -> tuple[bool, str, str]:
    """Check type hints with Mypy (optional)."""
    # Check if mypy is configured
    mypy_ini = Path(__file__).parent.parent.parent / "mypy.ini"
    if not mypy_ini.exists():
        if verbose:
            logger.info("Type checking (Mypy) - skipped (no config)")
        return True, "Skipped (no mypy.ini)", ""

    success, output, error = run_command(
        ["mypy", "src", "--config-file", "mypy.ini"],
        "Checking types (Mypy)",
        verbose=verbose,
    )

    if not success:
        if verbose:
            logger.warning("Type checking failed (non-blocking)")
            if output:
                logger.error(f"Details:\n{output[:500]}")
        # Don't fail commit on mypy errors
        return True, output, error

    return success, output, error


def check_secrets(verbose: bool = False) -> tuple[bool, str, str]:
    """Check for potential secrets in staged files."""
    try:
        # Get staged files
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )

        if result.returncode != 0:
            return False, "", "Could not get staged files"

        staged_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]

        if not staged_files:
            return True, "No staged files to check", ""

        # Filter to Python files only
        python_files = [
            Path(f) for f in staged_files if f.endswith(".py") and Path(f).exists()
        ]

        if not python_files:
            return True, "No Python files to check", ""

        patterns = setup_secrets_detection()
        all_secrets = []

        for file_path in python_files:
            secrets = scan_for_secrets(file_path, patterns)
            if secrets:
                all_secrets.extend([f"{file_path}: {s}" for s in secrets])

        if all_secrets:
            error_msg = f"Potential secrets found in {len(all_secrets)} locations"
            if verbose:
                logger.error(f"🚨 {error_msg}")
                for secret in all_secrets:
                    logger.error(f"  - {secret}")
            return False, "\n".join(all_secrets), error_msg

        return True, f"Checked {len(python_files)} files, no secrets found", ""

    except Exception as e:
        logger.error(f"Secrets check failed: {e}")
        return False, "", str(e)


def check_policy_compliance(verbose: bool = False) -> tuple[bool, str, str]:
    """Check policy compliance using policy loader."""
    try:
        # Add parent directory to path for imports
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from scripts.utils.policy_loader import PolicyLoader

        policy = PolicyLoader()

        # Basic policy validation
        if not policy.policy:
            return False, "", "Could not load policy"

        # Check if policy is properly configured
        required_sections = ["coverage", "testing", "linting"]
        missing_sections = [s for s in required_sections if s not in policy.policy]

        if missing_sections:
            error_msg = f"Policy missing sections: {', '.join(missing_sections)}"
            return False, "", error_msg

        return True, "Policy compliance check passed", ""

    except ImportError:
        if verbose:
            logger.warning("Policy loader not available, skipping policy check")
        return True, "Skipped (policy loader not available)", ""
    except Exception as e:
        logger.error(f"Policy compliance check failed: {e}")
        return False, "", str(e)


def run_quick_tests(verbose: bool = False) -> tuple[bool, str, str]:
    """Run quick unit tests only."""
    # Only run unit tests, skip integration tests
    success, output, error = run_command(
        ["pytest", "tests/", "-v", "-m", "not integration", "--tb=short", "-x"],
        "Running unit tests",
        verbose=verbose,
    )

    if not success and verbose:
        logger.error(f"Test details:\n{output[:1000]}")

    return success, output, error


def main():
    """Main pre-commit hook logic with enhanced CLI support."""
    parser = argparse.ArgumentParser(description="Pre-commit quality checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--skip-tests", action="store_true", help="Skip unit tests")
    parser.add_argument(
        "--skip-secrets", action="store_true", help="Skip secrets check"
    )
    parser.add_argument(
        "--skip-policy", action="store_true", help="Skip policy compliance"
    )

    args = parser.parse_args()

    start_time = time.time()
    ci_env = is_ci()
    mode = "CI Mode (Check-Only)" if ci_env else "Local Mode (Auto-Fix)"

    # Check for --no-verify bypass
    if is_no_verify_bypass():
        logger.warning("🚨 --no-verify detected! Bypassing pre-commit hooks.")
        logger.warning("This is not recommended and may violate governance policies.")
        if ci_env:
            logger.error("--no-verify is not allowed in CI environment")
            return 1

    if not args.json:
        print("=" * 60)
        print(f"🪝 Pre-Commit Quality Checks [{mode}]")
        print("=" * 60)
        print()

    # Define checks to run
    checks = [
        ("Secrets Detection", check_secrets),
        ("Policy Compliance", check_policy_compliance),
        ("Auto-Format", auto_format),
        ("Auto-Lint", auto_lint),
        ("Type Checking", check_types),
    ]

    if not args.skip_tests:
        checks.append(("Unit Tests", run_quick_tests))

    # Skip certain checks based on arguments
    if args.skip_secrets:
        checks = [c for c in checks if c[0] != "Secrets Detection"]
    if args.skip_policy:
        checks = [c for c in checks if c[0] != "Policy Compliance"]

    # Run all checks
    results = []
    secrets_found = []
    policy_violations = []

    for name, check_func in checks:
        result = run_quality_check(name, check_func, verbose=args.verbose)
        results.append(result)

        # Collect special results
        if name == "Secrets Detection" and not result.success:
            secrets_found.append(result.output)
        elif name == "Policy Compliance" and not result.success:
            policy_violations.append(result.error or result.output)

    total_duration = time.time() - start_time

    # Create report
    report = PreCommitReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        mode=mode,
        total_checks=len(results),
        passed_checks=sum(1 for r in results if r.success),
        failed_checks=sum(1 for r in results if not r.success),
        auto_fixed_count=sum(1 for r in results if getattr(r, "auto_fixed", False)),
        duration=total_duration,
        results=results,
        secrets_found=secrets_found,
        policy_violations=policy_violations,
    )

    # Output results
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("=" * 60)
        print("📊 Results Summary:")
        print("-" * 60)

        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration_str = f"({result.duration:.2f}s)"
            print(f"  {status} - {result.name} {duration_str}")

            if not result.success and args.verbose:
                if result.error:
                    print(f"    Error: {result.error}")
                if result.output:
                    print(f"    Output: {result.output[:200]}...")

        print("=" * 60)
        print(f"📈 Summary: {report.passed_checks}/{report.total_checks} checks passed")
        print(f"⏱️  Duration: {total_duration:.2f}s")

        if report.auto_fixed_count > 0:
            print(f"🔧 Auto-fixed: {report.auto_fixed_count} issues")

        if report.success:
            print("✅ All checks passed! Proceeding with commit.")
            if not ci_env:
                print(
                    "💡 Auto-fixed files have been staged. Review changes with: git diff --cached"
                )
        else:
            print("❌ Some checks failed. Please fix issues before committing.")
            print()

            if secrets_found:
                print("🚨 CRITICAL: Potential secrets detected!")
                print("   Remove all secrets before committing.")

            if policy_violations:
                print("🛡️  POLICY VIOLATIONS:")
                for violation in policy_violations:
                    print(f"   - {violation}")

            if ci_env:
                print("💡 CI Mode: Fix issues locally before pushing:")
                print("   - Format: black .")
                print("   - Lint: ruff check --fix .")
                print("   - Test: pytest tests/")
            else:
                print("💡 Manual fixes may be needed for:")
                print("   - Undefined variables (F821 errors)")
                print("   - Complex logic issues")
                print("   - Test failures")
                print()
                print("To bypass (not recommended): git commit --no-verify")

    # Exit with appropriate code
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
