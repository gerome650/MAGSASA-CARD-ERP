#!/usr/bin/env python3
"""
🔍 CI Stabilization Verification Script

Verifies that all CI stabilization improvements have been properly implemented.

Usage:
    python scripts/verify_ci_stabilization.py
"""

import sys
from pathlib import Path


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    exists = Path(filepath).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_file_contains(filepath: str, search_term: str, description: str) -> bool:
    """Check if a file contains a specific term."""
    try:
        with open(filepath) as f:
            content = f.read()
            contains = search_term in content
            status = "✅" if contains else "❌"
            print(f"{status} {description}")
            return contains
    except FileNotFoundError:
        print(f"❌ {description} (file not found)")
        return False


def verify_workflows() -> list[bool]:
    """Verify GitHub Actions workflows."""
    print_header("GitHub Actions Workflows")

    checks = []

    # Check CI workflow exists
    checks.append(check_file_exists(".github/workflows/ci.yml", "CI workflow exists"))

    # Check for concurrency control
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "concurrency:", "Concurrency control configured"
        )
    )

    # Check for caching
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "actions/cache@v4", "Dependency caching enabled"
        )
    )

    # Check for timeouts
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "timeout-minutes:", "Job timeouts configured"
        )
    )

    # Check for retry logic
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "for i in 1 2 3", "Retry logic implemented"
        )
    )

    # Check for security scan job
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "security-scan:", "Security scan job exists"
        )
    )

    # Check for readiness gate
    checks.append(
        check_file_contains(
            ".github/workflows/ci.yml", "readiness-gate:", "Readiness gate job exists"
        )
    )

    # Check update-readiness workflow
    checks.append(
        check_file_exists(
            ".github/workflows/update-readiness.yml", "Update readiness workflow exists"
        )
    )

    # Check staging smoke test workflow
    checks.append(
        check_file_exists(
            ".github/workflows/staging-smoke-test.yml",
            "Staging smoke test workflow exists",
        )
    )

    return checks


def verify_dependencies() -> list[bool]:
    """Verify dependency management."""
    print_header("Dependency Management")

    checks = []

    # Check pyproject.toml exists
    checks.append(check_file_exists("pyproject.toml", "pyproject.toml exists"))

    # Check for pinned versions in pyproject.toml
    checks.append(
        check_file_contains(
            "pyproject.toml", "pytest==", "Dependencies pinned in pyproject.toml"
        )
    )

    # Check for pytest-rerunfailures
    checks.append(
        check_file_contains(
            "pyproject.toml", "pytest-rerunfailures", "pytest-rerunfailures added"
        )
    )

    # Check for pytest-xdist
    checks.append(
        check_file_contains(
            "pyproject.toml", "pytest-xdist", "pytest-xdist added for parallel tests"
        )
    )

    # Check for security tools
    checks.append(
        check_file_contains("pyproject.toml", "bandit", "Bandit security scanner added")
    )

    # Check requirements.txt
    checks.append(check_file_exists("requirements.txt", "requirements.txt exists"))

    # Check for pinned versions in requirements.txt
    checks.append(
        check_file_contains(
            "requirements.txt", "pytest==", "Dependencies pinned in requirements.txt"
        )
    )

    # Check uv.lock exists
    checks.append(check_file_exists("uv.lock", "uv.lock file exists"))

    return checks


def verify_test_config() -> list[bool]:
    """Verify test configuration."""
    print_header("Test Configuration")

    checks = []

    # Check for reruns configuration
    checks.append(
        check_file_contains("pyproject.toml", "--reruns", "Test reruns configured")
    )

    # Check for parallel execution
    checks.append(
        check_file_contains(
            "pyproject.toml", "-n=auto", "Parallel test execution enabled"
        )
    )

    # Check for maxfail
    checks.append(
        check_file_contains("pyproject.toml", "--maxfail", "Max failures limit set")
    )

    # Check for flaky marker
    checks.append(
        check_file_contains("pyproject.toml", "flaky:", "Flaky test marker defined")
    )

    return checks


def verify_security() -> list[bool]:
    """Verify security configuration."""
    print_header("Security Configuration")

    checks = []

    # Check .bandit config exists
    checks.append(check_file_exists(".bandit", "Bandit configuration exists"))

    # Check bandit excludes
    checks.append(
        check_file_contains(".bandit", "exclude_dirs", "Bandit exclusions configured")
    )

    return checks


def verify_documentation() -> list[bool]:
    """Verify documentation."""
    print_header("Documentation")

    checks = []

    # Check completion report
    checks.append(
        check_file_exists("CI_STABILIZATION_COMPLETE.md", "Completion report exists")
    )

    # Check PR template
    checks.append(
        check_file_exists(".github/PULL_REQUEST_TEMPLATE.md", "PR template exists")
    )

    return checks


def main() -> int:
    """Main verification function."""
    print_header("🔍 CI Stabilization Verification")
    print("Verifying all CI stabilization improvements...\n")

    all_checks = []

    # Run all verification checks
    all_checks.extend(verify_workflows())
    all_checks.extend(verify_dependencies())
    all_checks.extend(verify_test_config())
    all_checks.extend(verify_security())
    all_checks.extend(verify_documentation())

    # Summary
    print_header("Summary")

    total = len(all_checks)
    passed = sum(all_checks)
    failed = total - passed
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Total checks: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success rate: {percentage:.1f}%\n")

    if failed == 0:
        print("🎉 All CI stabilization checks passed!")
        print("✅ Your CI pipeline is ready for production.\n")
        return 0
    else:
        print("⚠️  Some checks failed. Please review and fix.")
        print("💡 See CI_STABILIZATION_COMPLETE.md for details.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
