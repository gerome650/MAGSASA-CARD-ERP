#!/usr/bin/env python3
"""
📣 Enhanced Slack Notifier with PR Author Mentions

Sends rich Slack notifications with:
- PR author mentions
- Coverage trends with sparklines
- Merge readiness scores
- Test results
- Policy violations

Usage:
    python scripts/notify_slack_enhanced.py

Environment Variables:
    SLACK_WEBHOOK_URL: Slack webhook URL (required)
    PR_AUTHOR: PR author username
    PR_NUMBER: PR number
    PR_TITLE: PR title
    COVERAGE: Coverage percentage
    COVERAGE_THRESHOLD: Minimum coverage threshold
    MERGE_SCORE: Merge readiness score
    TESTS_PASSED: Number of tests passed
    TESTS_TOTAL: Total number of tests
    LINT_VIOLATIONS: Number of linting violations
    GITHUB_REPOSITORY: Repository name (e.g., "owner/repo")
    GITHUB_RUN_ID: GitHub Actions run ID
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from scripts.metrics.coverage_trend import CoverageTrend
except ImportError:
    CoverageTrend = None


def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable with default.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def get_coverage_trend() -> str:
    """Get coverage trend sparkline.

    Returns:
        Sparkline string or empty if unavailable
    """
    if CoverageTrend is None:
        return ""

    try:
        tracker = CoverageTrend()
        return tracker.generate_sparkline()
    except Exception:
        return ""


def build_slack_message() -> dict[str, Any]:
    """Build comprehensive Slack message payload.

    Returns:
        Slack message payload dictionary
    """
    # Get environment variables
    pr_author = get_env_var("PR_AUTHOR", "unknown")
    pr_number = get_env_var("PR_NUMBER", "N/A")
    pr_title = get_env_var("PR_TITLE", "Untitled PR")
    coverage = float(get_env_var("COVERAGE", "0"))
    coverage_threshold = float(get_env_var("COVERAGE_THRESHOLD", "85"))
    merge_score = float(get_env_var("MERGE_SCORE", "0"))
    tests_passed = int(get_env_var("TESTS_PASSED", "0"))
    tests_total = int(get_env_var("TESTS_TOTAL", "0"))
    lint_violations = int(get_env_var("LINT_VIOLATIONS", "0"))
    repo = get_env_var("GITHUB_REPOSITORY", "unknown/unknown")
    run_id = get_env_var("GITHUB_RUN_ID", "")

    # Calculate status
    coverage_ok = coverage >= coverage_threshold
    tests_ok = tests_passed == tests_total and tests_total > 0
    lint_ok = lint_violations == 0
    merge_ready = merge_score >= 80

    all_ok = coverage_ok and tests_ok and lint_ok and merge_ready

    # Determine color and status
    if all_ok:
        color = "#36a64f"  # Green
        status_emoji = "✅"
        status_text = "PASSED"
    else:
        color = "#ff0000"  # Red
        status_emoji = "❌"
        status_text = "FAILED"

    # Get coverage trend
    coverage_trend = get_coverage_trend()
    coverage_display = f"{coverage:.1f}%"
    if coverage_trend:
        coverage_display += f" {coverage_trend}"

    # Build fields
    fields: list[dict[str, Any]] = [
        {"title": "Coverage", "value": coverage_display, "short": True},
        {
            "title": "Tests",
            "value": (
                f"{tests_passed}/{tests_total} passed"
                if tests_total > 0
                else "No tests"
            ),
            "short": True,
        },
        {
            "title": "Merge Score",
            "value": f"{merge_score:.0f}/100 {'✅' if merge_ready else '❌'}",
            "short": True,
        },
        {
            "title": "Linting",
            "value": f"{lint_violations} violations {'✅' if lint_ok else '❌'}",
            "short": True,
        },
    ]

    # Build actions list
    actions_needed = []
    if not coverage_ok:
        actions_needed.append(f"• Increase coverage to >={coverage_threshold}%")
    if not tests_ok:
        actions_needed.append(f"• Fix {tests_total - tests_passed} failing tests")
    if not lint_ok:
        actions_needed.append(f"• Fix {lint_violations} linting violations")
    if not merge_ready:
        actions_needed.append("• Improve merge score to >=80")

    # Build message text
    pr_url = f"https://github.com/{repo}/pull/{pr_number}" if pr_number != "N/A" else ""
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if run_id else ""

    message_text = f"*PR #{pr_number}*: {pr_title}\n*Author*: @{pr_author}"
    if pr_url:
        message_text = f"<{pr_url}|PR #{pr_number}>: {pr_title}\n*Author*: @{pr_author}"

    # Build attachment
    attachment = {
        "color": color,
        "title": f"🛡️ Merge Gate: {status_emoji} {status_text}",
        "text": message_text,
        "fields": fields,
        "footer": "MAGSASA-CARD ERP CI/CD",
        "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
        "ts": int(datetime.utcnow().timestamp()),
    }

    # Add actions if needed
    if actions_needed:
        attachment["text"] += "\n\n*Required Actions:*\n" + "\n".join(actions_needed)

    # Add links
    if run_url:
        attachment["actions"] = [
            {"type": "button", "text": "View CI Run", "url": run_url}
        ]

    # Build final payload
    payload = {
        "username": "Merge Gate Bot",
        "icon_emoji": ":shield:",
        "attachments": [attachment],
    }

    return payload


def send_slack_notification(webhook_url: str, payload: dict[str, Any]) -> bool:
    """Send notification to Slack.

    Args:
        webhook_url: Slack webhook URL
        payload: Message payload

    Returns:
        True if successful, False otherwise
    """
    try:
        data = json.dumps(payload).encode("utf-8")

        request = Request(
            webhook_url, data=data, headers={"Content-Type": "application/json"}
        )

        with urlopen(request, timeout=10) as response:
            if response.status == 200:
                return True
            else:
                print(
                    f"❌ Slack API returned status {response.status}", file=sys.stderr
                )
                return False

    except URLError as e:
        print(f"❌ Failed to send Slack notification: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    # Get webhook URL
    webhook_url = get_env_var("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("⚠️  SLACK_WEBHOOK_URL not set, skipping notification", file=sys.stderr)
        sys.exit(0)

    print("📣 Building Slack notification...")

    # Build message
    try:
        payload = build_slack_message()
    except Exception as e:
        print(f"❌ Failed to build message: {e}", file=sys.stderr)
        sys.exit(1)

    # Print payload for debugging
    if get_env_var("DEBUG", "").lower() in ("true", "1", "yes"):
        print("Debug: Payload:")
        print(json.dumps(payload, indent=2))

    # Send notification
    print("📤 Sending to Slack...")
    if send_slack_notification(webhook_url, payload):
        print("✅ Slack notification sent successfully")
        sys.exit(0)
    else:
        print("❌ Failed to send Slack notification", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
