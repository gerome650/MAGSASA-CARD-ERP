#!/usr/bin/env python3
"""
Syntax Regression Guard Suite
==============================
Tests historically-problematic files for syntax errors, undefined variables,
formatting issues, and import problems. Prevents regressions in critical files.

Each test runs 5 comprehensive checks:
1. ✅ Syntax compilation (py_compile)
2. ✅ AST parse validation (ast.parse)
3. ✅ Ruff lint scan (F821 undefined names, E999 syntax errors, E701 multiple statements)
4. ✅ Black format check
5. ✅ Dynamic import test (importlib)

Mark entire suite with: @pytest.mark.regression
"""
import ast
import importlib.util
import py_compile
import subprocess
import sys
from pathlib import Path

import pytest

# Base path for the project
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Known-problem files that need continuous monitoring
WATCHED_FILES = [
    "implement_farmer_role.py",
    "observability/alerts/webhook_server.py",
    "observability/alerts/notifier.py",
    "observability/alerts/anomaly_strategies.py",
    "test_data_integrity.py",
    "test_business_logic.py",
]


def get_file_path(relative_path: str) -> Path:
    """Convert relative path to absolute path."""
    return PROJECT_ROOT / relative_path


def check_syntax_compile(file_path: Path) -> tuple[bool, str]:
    """
    Check 1: Verify file compiles with py_compile.
    Returns: (success, error_message)
    """
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, ""
    except py_compile.PyCompileError as e:
        return False, f"❌ Syntax compilation failed: {e.msg}"


def check_ast_parse(file_path: Path) -> tuple[bool, str]:
    """
    Check 2: Verify file can be parsed into AST.
    Returns: (success, error_message)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        ast.parse(source, filename=str(file_path))
        return True, ""
    except SyntaxError as e:
        return False, f"❌ AST parse failed: {e.msg} (line {e.lineno})"
    except Exception as e:
        return False, f"❌ AST parse error: {str(e)}"


def check_ruff_lint(file_path: Path) -> tuple[bool, str]:
    """
    Check 3: Run Ruff linter focusing on critical issues.
    F821 = undefined name
    E999 = syntax error
    E701 = multiple statements on one line
    Returns: (success, error_message)
    """
    try:
        result = subprocess.run(
            [
                "ruff",
                "check",
                str(file_path),
                "--select",
                "F821,E999,E701",
                "--output-format",
                "text",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, ""
        else:
            errors = result.stdout.strip()
            return False, f"❌ Ruff lint issues detected:\n{errors}"
    except FileNotFoundError:
        # Ruff not installed, skip this check
        return True, "⚠️ Ruff not found, skipping lint check"
    except subprocess.TimeoutExpired:
        return False, "❌ Ruff lint check timed out"
    except Exception as e:
        return False, f"❌ Ruff lint check error: {str(e)}"


def check_black_format(file_path: Path) -> tuple[bool, str]:
    """
    Check 4: Verify file passes Black formatting check.
    Returns: (success, error_message)
    """
    try:
        result = subprocess.run(
            ["black", "--check", "--quiet", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, ""
        else:
            return False, "❌ Black formatting check failed (would reformat)"
    except FileNotFoundError:
        # Black not installed, skip this check
        return True, "⚠️ Black not found, skipping format check"
    except subprocess.TimeoutExpired:
        return False, "❌ Black format check timed out"
    except Exception as e:
        return False, f"❌ Black format check error: {str(e)}"


def check_dynamic_import(file_path: Path) -> tuple[bool, str]:
    """
    Check 5: Attempt dynamic import to verify module loads.
    Returns: (success, error_message)
    """
    # Skip dynamic import for test files to avoid pytest collection conflicts
    if file_path.name.startswith("test_"):
        return True, "⚠️ Skipped dynamic import for test file"

    try:
        # Add project root to sys.path temporarily
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))

        # Create module name from relative path
        relative_path = file_path.relative_to(PROJECT_ROOT)
        module_name = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return False, "❌ Could not create module spec"

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return True, ""
    except SyntaxError as e:
        return False, f"❌ Import failed with syntax error: {e.msg} (line {e.lineno})"
    except NameError as e:
        return False, f"❌ Import failed with undefined name: {str(e)}"
    except Exception as e:
        return False, f"❌ Import failed: {type(e).__name__}: {str(e)}"


def run_all_checks(file_path: Path) -> list[tuple[str, bool, str]]:
    """
    Run all 5 checks on a file.
    Returns: List of (check_name, success, message) tuples
    """
    checks = [
        ("Syntax Compilation", check_syntax_compile(file_path)),
        ("AST Parse", check_ast_parse(file_path)),
        ("Ruff Lint", check_ruff_lint(file_path)),
        ("Black Format", check_black_format(file_path)),
        ("Dynamic Import", check_dynamic_import(file_path)),
    ]
    return [(name, success, msg) for name, (success, msg) in checks]


@pytest.mark.regression
@pytest.mark.parametrize("relative_path", WATCHED_FILES)
def test_syntax_regression_guard(relative_path: str):
    """
    Comprehensive syntax regression test for historically-problematic files.

    This test ensures that files which have had syntax issues in the past
    remain free of:
    - Syntax errors
    - Undefined variables
    - Formatting issues
    - Import problems

    Fails fast with descriptive error messages to prevent regressions.
    """
    file_path = get_file_path(relative_path)

    # Verify file exists
    if not file_path.exists():
        pytest.skip(f"File not found: {relative_path}")

    # Run all checks
    results = run_all_checks(file_path)

    # Collect failures
    failures = []
    for check_name, success, message in results:
        if not success and not message.startswith("⚠️"):
            failures.append(f"{check_name}: {message}")

    # Report results
    if failures:
        error_report = f"\n{'='*70}\n"
        error_report += f"❌ SYNTAX REGRESSION DETECTED in {relative_path}\n"
        error_report += f"{'='*70}\n\n"
        for i, failure in enumerate(failures, 1):
            error_report += f"{i}. {failure}\n\n"
        error_report += f"{'='*70}\n"
        error_report += "Fix these issues to prevent regression.\n"
        error_report += f"{'='*70}\n"
        pytest.fail(error_report)

    # All checks passed
    print(f"✅ All syntax checks passed for {relative_path}")


@pytest.mark.regression
def test_syntax_guard_coverage():
    """
    Meta-test: Verify that all watched files exist and are being monitored.
    """
    missing_files = []
    for relative_path in WATCHED_FILES:
        file_path = get_file_path(relative_path)
        if not file_path.exists():
            missing_files.append(relative_path)

    if missing_files:
        pytest.fail(
            f"❌ Syntax guard configuration error: "
            f"The following watched files do not exist:\n"
            f"{chr(10).join(f'  - {f}' for f in missing_files)}\n"
            f"Update WATCHED_FILES in test_syntax_regressions.py"
        )


if __name__ == "__main__":
    """
    Allow running this test directly for quick validation:
    python tests/regression/test_syntax_regressions.py
    """
    print("🛡️ Running Syntax Regression Guard Suite...\n")

    all_passed = True
    for relative_path in WATCHED_FILES:
        file_path = get_file_path(relative_path)

        if not file_path.exists():
            print(f"⚠️  SKIPPED: {relative_path} (file not found)")
            continue

        print(f"🔍 Checking {relative_path}...")
        results = run_all_checks(file_path)

        file_passed = True
        for check_name, success, message in results:
            if success:
                if message.startswith("⚠️"):
                    print(f"   ⚠️  {check_name}: {message}")
                else:
                    print(f"   ✅ {check_name}: PASS")
            else:
                print(f"   ❌ {check_name}: FAIL")
                print(f"      {message}")
                file_passed = False
                all_passed = False

        if file_passed:
            print("   ✅ Overall: PASS\n")
        else:
            print("   ❌ Overall: FAIL\n")

    if all_passed:
        print("\n✅ All syntax regression checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some syntax regression checks failed!")
        sys.exit(1)
