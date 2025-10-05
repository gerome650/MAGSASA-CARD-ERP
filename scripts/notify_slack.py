#!/usr/bin/env python3
"""
Slack notification system for CI/CD preflight failures.
Sends rich messages with branch info, commit SHA, and failure details.
"""

import os
import sys
from datetime import datetime

import requests


class SlackNotifier:
    """Handles Slack notifications for CI/CD failures."""

    def __init__(self, webhook_url: str | None = None):
        """Initialize Slack notifier with webhook URL."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL environment variable is required")

    def send_preflight_failure(
        self,
        branch: str,
        commit_sha: str,
        failing_check: str,
        logs_url: str | None = None,
        pr_url: str | None = None,
    ) -> bool:
        """
        Send notification about preflight failure.

        Args:
            branch: Git branch name
            commit_sha: Git commit SHA
            failing_check: Description of failing check
            logs_url: Optional URL to logs
            pr_url: Optional URL to pull request

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            # Build attachments with failure details
            attachments = [
                {
                    "color": "danger",
                    "title": "❌ Preflight Check Failed",
                    "text": f"**Check:** {failing_check}",
                    "fields": [
                        {
                            "title": "Branch",
                            "value": branch,
                            "short": True,
                        },
                        {
                            "title": "Commit",
                            "value": commit_sha[:8],
                            "short": True,
                        },
                        {
                            "title": "Time",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True,
                        },
                    ],
                }
            ]

            # Add action buttons if URLs provided
            if logs_url or pr_url:
                actions = []
                if logs_url:
                    actions.append(
                        {
                            "type": "button",
                            "text": "View Logs",
                            "url": logs_url,
                            "style": "primary",
                        }
                    )
                if pr_url:
                    actions.append(
                        {
                            "type": "button",
                            "text": "View PR",
                            "url": pr_url,
                        }
                    )

                attachments[0]["actions"] = actions

            # Build payload
            payload = {
                "text": f"🚨 Preflight FAILED on *{branch}*",
                "attachments": attachments,
                "channel": os.getenv("SLACK_CHANNEL", "#ci-cd"),
                "username": "CI/CD Bot",
                "icon_emoji": ":robot_face:",
            }

            # Send request
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                print("✅ Slack notification sent successfully")
                return True
            else:
                print(f"❌ Failed to send Slack notification: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending Slack notification: {e}")
            return False

    def send_success_notification(
        self,
        branch: str,
        commit_sha: str,
        checks_passed: int,
        total_checks: int,
    ) -> bool:
        """
        Send notification about successful preflight.

        Args:
            branch: Git branch name
            commit_sha: Git commit SHA
            checks_passed: Number of checks that passed
            total_checks: Total number of checks

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            payload = {
                "text": f"✅ Preflight PASSED on *{branch}*",
                "attachments": [
                    {
                        "color": "good",
                        "title": "All Checks Passed",
                        "text": f"**{checks_passed}/{total_checks}** checks passed successfully",
                        "fields": [
                            {
                                "title": "Branch",
                                "value": branch,
                                "short": True,
                            },
                            {
                                "title": "Commit",
                                "value": commit_sha[:8],
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S UTC"
                                ),
                                "short": True,
                            },
                        ],
                    }
                ],
                "channel": os.getenv("SLACK_CHANNEL", "#ci-cd"),
                "username": "CI/CD Bot",
                "icon_emoji": ":white_check_mark:",
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            return response.status_code == 200

        except Exception as e:
            print(f"❌ Error sending success notification: {e}")
            return False


def main():
    """CLI interface for Slack notifications."""
    if len(sys.argv) < 4:
        print("Usage: python notify_slack.py <branch> <commit_sha> <failing_check>")
        print("Example: python notify_slack.py main abc123 'Ruff linting failed'")
        sys.exit(1)

    branch = sys.argv[1]
    commit_sha = sys.argv[2]
    failing_check = sys.argv[3]

    try:
        notifier = SlackNotifier()
        success = notifier.send_preflight_failure(
            branch=branch,
            commit_sha=commit_sha,
            failing_check=failing_check,
            logs_url=os.getenv("CI_LOGS_URL"),
            pr_url=os.getenv("PR_URL"),
        )

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
