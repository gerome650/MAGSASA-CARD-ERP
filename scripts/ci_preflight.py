#!/usr/bin/env python3
"""
CI Preflight Validation Script
Runs comprehensive checks before pushing code to ensure CI safety.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

try:
    from notify_email import EmailNotifier
    from notify_slack import SlackNotifier
except ImportError as e:
    print(f"⚠️  Warning: Could not import notification modules: {e}")
    SlackNotifier = None
    EmailNotifier = None

# Configure environment
os.environ["PYTHONUNBUFFERED"] = "1"
# Add uv to PATH if not already there
if "/Users/palawan/.local/bin" not in os.environ.get("PATH", ""):
    os.environ["PATH"] = "/Users/palawan/.local/bin:" + os.environ.get("PATH", "")


def run_command(
    name: str, cmd: list[str], description: str = "", timeout: int = 300
) -> tuple[str, bool, float]:
    """
    Run a command and return the result with timing.

    Args:
        name: Display name for the check
        cmd: Command to run as list of strings
        description: Optional description of what the command does
        timeout: Timeout in seconds (default 5 minutes)

    Returns:
        Tuple of (name, success_boolean, duration_seconds)
    """
    print(f"🚀 {name}...")
    if description:
        print(f"   {description}")

    start_time = time.time()

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=False,  # Let output show in real-time
            text=True,
            timeout=timeout,
        )
        duration = time.time() - start_time
        print(f"   ✅ {name} completed successfully ({duration:.1f}s)")
        return (name, True, duration)
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"   ⏰ {name} timed out after {duration:.1f}s")
        return (name, False, duration)
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"   ❌ {name} failed with exit code {e.returncode} ({duration:.1f}s)")
        return (name, False, duration)
    except FileNotFoundError:
        duration = time.time() - start_time
        print(f"   ❌ {name} failed: command not found ({duration:.1f}s)")
        return (name, False, duration)


def send_failure_notifications(branch: str, failed_checks: list, total_time: float):
    """Send notifications about preflight failures."""
    print("\n📤 Sending failure notifications...")

    # Send Slack notification
    if SlackNotifier:
        try:
            slack_notifier = SlackNotifier()
            slack_notifier.send_preflight_failure(
                branch=branch,
                failed_checks=failed_checks,
                total_time=total_time,
                details={"Failed Count": len(failed_checks)},
            )
        except Exception as e:
            print(f"⚠️  Slack notification failed: {e}")

    # Send email notification
    if EmailNotifier:
        try:
            email_notifier = EmailNotifier()
            email_notifier.send_preflight_failure(
                branch=branch,
                failed_checks=failed_checks,
                total_time=total_time,
                details={"Failed Count": len(failed_checks)},
            )
        except Exception as e:
            print(f"⚠️  Email notification failed: {e}")


def send_success_notifications(branch: str, total_time: float):
    """Send notifications about preflight success."""
    print("\n📤 Sending success notifications...")

    # Send Slack notification
    if SlackNotifier:
        try:
            slack_notifier = SlackNotifier()
            slack_notifier.send_preflight_success(
                branch=branch,
                total_time=total_time,
                details={"Status": "All checks passed"},
            )
        except Exception as e:
            print(f"⚠️  Slack notification failed: {e}")

    # Send email notification
    if EmailNotifier:
        try:
            email_notifier = EmailNotifier()
            email_notifier.send_preflight_success(
                branch=branch,
                total_time=total_time,
                details={"Status": "All checks passed"},
            )
        except Exception as e:
            print(f"⚠️  Email notification failed: {e}")


def main():
    """Run all CI preflight checks."""
    print("🔎 Running full CI Preflight Validation...")
    print("=" * 50)

    # Define checks in order with timeouts
    checks = [
        (
            "Linting",
            ["uv", "run", "ruff", "check", "."],
            "Check code style with ruff",
            60,
        ),
        (
            "Black Format",
            ["uv", "run", "black", "--check", "."],
            "Check code formatting",
            60,
        ),
        # ("Type Check", ["uv", "run", "mypy", ".", "--ignore-missing-imports"], "Check type annotations", 120),
        (
            "Unit Tests",
            ["uv", "run", "pytest", "--maxfail=1", "--disable-warnings", "-q"],
            "Run unit tests",
            180,
        ),
        ("MCP Validation", ["make", "mcp-check"], "Validate MCP setup", 60),
        ("Agent Trace", ["make", "agent-run-all"], "Run agent orchestration", 120),
        ("Build", ["uv", "build"], "Build all packages", 300),
    ]

    results = []
    total_start_time = time.time()

    # Run each check
    for name, cmd, description, timeout in checks:
        result = run_command(name, cmd, description, timeout)
        results.append(result)
        print()  # Add spacing between checks

    total_duration = time.time() - total_start_time

    # Print summary
    print("📊 CI Preflight Results Summary")
    print("=" * 50)

    failed_checks = []
    total_duration_checks = 0.0

    for name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<18} {status:<10} ({duration:.1f}s)")
        total_duration_checks += duration
        if not success:
            failed_checks.append(name)

    print("=" * 50)
    print(f"⏱️  Total time: {total_duration:.1f}s")
    print(f"📈 Checks time: {total_duration_checks:.1f}s")

    # Get current branch for notifications
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        current_branch = result.stdout.strip()
    except subprocess.CalledProcessError:
        current_branch = "unknown"

    if failed_checks:
        print(f"🚨 {len(failed_checks)} check(s) failed: {', '.join(failed_checks)}")
        print("💡 Please fix the issues above before pushing.")
        print("🔧 Run individual commands to debug specific failures:")
        for check in failed_checks:
            if check == "Linting":
                print("   • uv run ruff check . --fix  # Auto-fix some issues")
            elif check == "Black Format":
                print("   • uv run black .  # Auto-format code")
            elif check == "Type Check":
                print("   • uv run mypy . --ignore-missing-imports  # Check types")
            elif check == "Unit Tests":
                print("   • uv run pytest tests/ -v  # Run specific tests")

        # Send failure notifications
        send_failure_notifications(current_branch, failed_checks, total_duration)
        sys.exit(1)
    else:
        print("🎉 All checks passed! Safe to push 🚀")
        print("✨ Your code is ready for CI/CD pipeline.")

        # Send success notifications
        send_success_notifications(current_branch, total_duration)
        sys.exit(0)


if __name__ == "__main__":
    main()
