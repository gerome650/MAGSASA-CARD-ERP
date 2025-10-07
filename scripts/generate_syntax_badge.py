#!/usr/bin/env python3
"""
Generate Syntax Guard Badge JSON
=================================
Creates a shields.io-compatible JSON badge for the syntax regression guard.

Reads pytest output or re-runs the regression suite to determine PASS/FAIL status.
Outputs: ci-dashboard/syntax-guard.json

Usage:
    python scripts/generate_syntax_badge.py [--pytest-json pytest-report.json] [--out ci-dashboard]

    If --pytest-json is provided, reads results from there.
    Otherwise, runs the regression suite directly.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def badge_json(label: str, message: str, color: str = "blue") -> dict:
    """Generate shields.io endpoint JSON format."""
    return {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }


def check_pytest_json(pytest_json_path: str) -> dict:
    """
    Parse pytest JSON report to find syntax regression test results.
    Returns: {"passed": bool, "total_files": int, "failed_files": list}
    """
    if not os.path.isfile(pytest_json_path):
        return {"passed": False, "total_files": 0, "failed_files": []}

    try:
        with open(pytest_json_path, encoding="utf-8") as f:
            data = json.load(f)

        tests = data.get("tests", [])

        # Find regression tests
        regression_tests = [
            t
            for t in tests
            if "regression" in t.get("nodeid", "").lower()
            or "syntax" in t.get("nodeid", "").lower()
        ]

        if not regression_tests:
            # No regression tests found in report
            return {"passed": None, "total_files": 0, "failed_files": []}

        failed_files = []
        total_files = 0

        for test in regression_tests:
            outcome = test.get("outcome", "failed")
            if "test_syntax_regression_guard" in test.get("nodeid", ""):
                total_files += 1
                if outcome != "passed":
                    # Extract file name from test nodeid
                    nodeid = test.get("nodeid", "")
                    if "[" in nodeid:
                        file_name = nodeid.split("[")[1].split("]")[0]
                        failed_files.append(file_name)

        passed = len(failed_files) == 0 and total_files > 0

        return {
            "passed": passed,
            "total_files": total_files,
            "failed_files": failed_files,
        }

    except Exception as e:
        print(f"⚠️  Warning: Could not parse pytest JSON: {e}", file=sys.stderr)
        return {"passed": False, "total_files": 0, "failed_files": []}


def run_regression_suite() -> dict:
    """
    Run the regression suite directly and capture results.
    Returns: {"passed": bool, "total_files": int, "failed_files": list}
    """
    try:
        result = subprocess.run(
            [
                "pytest",
                "tests/regression/test_syntax_regressions.py",
                "-m",
                "regression",
                "--maxfail=1",
                "--disable-warnings",
                "-q",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        passed = result.returncode == 0

        # Parse output to count files
        output = result.stdout + result.stderr

        # Count test results
        import re

        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)

        total_files = 0
        failed_files = []

        if passed_match:
            total_files += int(passed_match.group(1))
        if failed_match:
            failed_count = int(failed_match.group(1))
            total_files += failed_count
            # Extract failed file names from output
            for line in output.split("\n"):
                if "FAILED" in line and "[" in line:
                    file_name = line.split("[")[1].split("]")[0]
                    failed_files.append(file_name)

        return {
            "passed": passed,
            "total_files": total_files,
            "failed_files": failed_files,
        }

    except subprocess.TimeoutExpired:
        print("❌ Error: Syntax regression tests timed out", file=sys.stderr)
        return {"passed": False, "total_files": 0, "failed_files": ["timeout"]}
    except Exception as e:
        print(f"❌ Error running regression suite: {e}", file=sys.stderr)
        return {"passed": False, "total_files": 0, "failed_files": ["error"]}


def generate_badge(results: dict) -> dict:
    """
    Generate badge JSON based on test results.

    Args:
        results: {"passed": bool, "total_files": int, "failed_files": list}

    Returns:
        Badge JSON dict
    """
    passed = results.get("passed")
    total_files = results.get("total_files", 0)
    failed_files = results.get("failed_files", [])

    if passed is None:
        # No regression tests found
        return badge_json("Syntax Guard", "N/A", "lightgrey")
    elif passed and total_files > 0:
        # All tests passed
        return badge_json(
            "Syntax Guard", f"PASS ✅ ({total_files} files)", "brightgreen"
        )
    elif not passed and total_files > 0:
        # Some tests failed
        failed_count = len(failed_files)
        return badge_json(
            "Syntax Guard", f"FAIL ❌ ({failed_count}/{total_files})", "red"
        )
    else:
        # No tests run
        return badge_json("Syntax Guard", "No Tests", "lightgrey")


def generate_extended_json(results: dict) -> dict:
    """
    Generate extended JSON with detailed results for dashboard consumption.

    Args:
        results: {"passed": bool, "total_files": int, "failed_files": list}

    Returns:
        Extended JSON with metadata
    """
    badge = generate_badge(results)

    return {
        **badge,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_files_checked": results.get("total_files", 0),
        "passed": results.get("passed", False),
        "failed_files": results.get("failed_files", []),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate syntax guard badge JSON for CI dashboard"
    )
    parser.add_argument(
        "--pytest-json",
        default="",
        help="Path to pytest JSON report (if available)",
    )
    parser.add_argument(
        "--out",
        default="ci-dashboard",
        help="Output directory for badge JSON",
    )
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Generate extended JSON with metadata",
    )
    args = parser.parse_args()

    # Determine test results
    if args.pytest_json and os.path.isfile(args.pytest_json):
        print(f"📊 Reading results from {args.pytest_json}")
        results = check_pytest_json(args.pytest_json)

        # If no regression tests found in JSON, run them directly
        if results.get("passed") is None:
            print("⚠️  No regression tests found in pytest JSON, running suite...")
            results = run_regression_suite()
    else:
        print("🧪 Running syntax regression suite...")
        results = run_regression_suite()

    # Generate badge JSON
    if args.extended:
        badge = generate_extended_json(results)
    else:
        badge = generate_badge(results)

    # Write badge file
    os.makedirs(args.out, exist_ok=True)
    badge_path = os.path.join(args.out, "syntax-guard.json")

    with open(badge_path, "w", encoding="utf-8") as f:
        json.dump(badge, f, indent=2)

    # Print results
    passed = results.get("passed")
    total_files = results.get("total_files", 0)
    failed_files = results.get("failed_files", [])

    print(f"\n{'='*70}")
    print("🛡️  Syntax Guard Badge Generated")
    print(f"{'='*70}")
    print(f"Status: {badge['message']}")
    print(f"Color: {badge['color']}")
    print(f"Files checked: {total_files}")

    if failed_files:
        print("\n❌ Failed files:")
        for file in failed_files:
            print(f"  - {file}")

    print(f"\n✅ Badge saved to: {badge_path}")
    print(f"{'='*70}\n")

    # Exit with appropriate code
    if passed:
        sys.exit(0)
    else:
        # Non-zero exit if tests failed (but still generate badge)
        sys.exit(1)


if __name__ == "__main__":
    main()
