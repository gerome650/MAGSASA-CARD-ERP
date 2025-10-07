#!/usr/bin/env python3
"""
✅ Governance System Validation Script

Validates that all governance components are correctly installed and configured.

Usage:
    python scripts/validate_governance_setup.py
    python scripts/validate_governance_setup.py --verbose
"""

import argparse
import sys
from pathlib import Path


class ValidationResult:
    """Represents validation result."""

    def __init__(self, name: str, passed: bool, message: str):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self) -> str:
        status = "✅" if self.passed else "❌"
        return f"{status} {self.name}: {self.message}"


def check_file_exists(path: Path, description: str) -> ValidationResult:
    """Check if a file exists."""
    if path.exists():
        return ValidationResult(description, True, f"Found at {path}")
    else:
        return ValidationResult(description, False, f"Not found at {path}")


def check_file_executable(path: Path, description: str) -> ValidationResult:
    """Check if a file is executable."""
    if not path.exists():
        return ValidationResult(description, False, f"File not found at {path}")

    import os

    if os.access(path, os.X_OK):
        return ValidationResult(description, True, f"Executable: {path}")
    else:
        return ValidationResult(description, False, f"Not executable: {path}")


def check_python_import(module: str, description: str) -> ValidationResult:
    """Check if a Python module can be imported."""
    try:
        __import__(module)
        return ValidationResult(
            description, True, f"Module '{module}' imports successfully"
        )
    except ImportError as e:
        return ValidationResult(description, False, f"Cannot import '{module}': {e}")


def check_yaml_valid(path: Path, description: str) -> ValidationResult:
    """Check if YAML file is valid."""
    if not path.exists():
        return ValidationResult(description, False, f"File not found at {path}")

    try:
        import yaml

        with open(path) as f:
            yaml.safe_load(f)
        return ValidationResult(description, True, f"Valid YAML: {path}")
    except Exception as e:
        return ValidationResult(description, False, f"Invalid YAML: {e}")


def validate_governance_system(
    _verbose: bool = False,
) -> tuple[list[ValidationResult], bool]:
    """Run all validation checks.

    Args:
        _verbose: Show detailed output (currently unused)

    Returns:
        Tuple of (results list, all_passed boolean)
    """
    repo_root = Path(__file__).parent.parent
    results = []

    # Check core files
    results.append(
        check_file_exists(repo_root / "merge_policy.yml", "Policy Configuration")
    )

    results.append(
        check_yaml_valid(repo_root / "merge_policy.yml", "Policy YAML Validity")
    )

    # Check scripts
    scripts = [
        ("scripts/utils/policy_loader.py", "Policy Loader"),
        ("scripts/hooks/enforce_coverage.py", "Coverage Enforcement"),
        ("scripts/hooks/pre_commit.py", "Pre-Commit Hook"),
        ("scripts/hooks/post_push.py", "Post-Push Hook"),
        ("scripts/hooks/install_hooks.py", "Hook Installer"),
        ("scripts/metrics/coverage_trend.py", "Coverage Trend Tracker"),
        ("scripts/metrics/coverage_badge.py", "Coverage Badge Generator"),
        ("scripts/notify_slack_enhanced.py", "Enhanced Slack Notifier"),
    ]

    for script_path, description in scripts:
        full_path = repo_root / script_path
        results.append(check_file_exists(full_path, description))
        if full_path.exists():
            results.append(
                check_file_executable(full_path, f"{description} Executable")
            )

    # Check workflows
    results.append(
        check_file_exists(
            repo_root / ".github" / "workflows" / "merge-gate.yml",
            "Merge Gate Workflow",
        )
    )

    # Check tests
    results.append(
        check_file_exists(
            repo_root / "tests" / "test_policy_loader.py", "Policy Loader Tests"
        )
    )

    # Check documentation
    docs = [
        ("PR_AUTHOR_INTEGRATION_GUIDE.md", "Integration Guide"),
        ("GOVERNANCE_QUICK_REFERENCE.md", "Quick Reference"),
        ("GOVERNANCE_IMPLEMENTATION_SUMMARY.md", "Implementation Summary"),
        ("README_GOVERNANCE_SECTION.md", "README Governance Section"),
    ]

    for doc_path, description in docs:
        results.append(check_file_exists(repo_root / doc_path, description))

    # Check Python dependencies
    dependencies = [
        ("yaml", "PyYAML"),
        ("pytest", "pytest"),
    ]

    for module, description in dependencies:
        results.append(check_python_import(module, f"Dependency: {description}"))

    # Check if git hooks are installed
    git_hooks_dir = repo_root / ".git" / "hooks"
    if git_hooks_dir.exists():
        for hook in ["pre-commit", "post-push"]:
            hook_file = git_hooks_dir / hook
            if hook_file.exists():
                with open(hook_file) as f:
                    content = f.read()
                    if "Auto-generated by install_hooks.py" in content:
                        results.append(
                            ValidationResult(
                                f"Git Hook: {hook}", True, "Installed and configured"
                            )
                        )
                    else:
                        results.append(
                            ValidationResult(
                                f"Git Hook: {hook}",
                                False,
                                "Exists but not installed by governance system",
                            )
                        )
            else:
                results.append(
                    ValidationResult(
                        f"Git Hook: {hook}",
                        False,
                        "Not installed (run 'make install-governance-hooks')",
                    )
                )
    else:
        results.append(
            ValidationResult(
                "Git Hooks Directory",
                False,
                ".git/hooks not found (not a git repository?)",
            )
        )

    # Check overall status
    all_passed = all(r.passed for r in results)

    return results, all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate governance system setup")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("🔍 Validating Governance System Setup")
    print("=" * 70)
    print()

    results, all_passed = validate_governance_system(args.verbose)

    # Print results
    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)

    for result in results:
        print(str(result))

    print()
    print("=" * 70)
    print(f"📊 Results: {passed_count}/{total_count} checks passed")
    print()

    if all_passed:
        print("✅ SUCCESS: All governance components are correctly installed!")
        print()
        print("🚀 Next Steps:")
        print("   1. Run 'make verify-all' to test the full pipeline")
        print("   2. Read 'PR_AUTHOR_INTEGRATION_GUIDE.md' for usage")
        print("   3. Configure SLACK_WEBHOOK_URL for notifications")
        print()
        return 0
    else:
        print("❌ FAILURE: Some components are missing or misconfigured")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Ensure you're in the repository root")
        print("   2. Run 'make install-governance-hooks' to install hooks")
        print("   3. Install Python dependencies: pip install -r requirements.txt")
        print("   4. Check that all files were committed correctly")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
