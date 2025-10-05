"""
Notification Module

Handles sending notifications to Slack and other channels.
"""

import os
from datetime import datetime
from typing import Any

try:
    import requests
except ImportError:
    raise ImportError("requests library not found. Install with: pip install requests")


class SlackNotifier:
    """Sends notifications to Slack via webhook."""

    def __init__(self, webhook_url: str | None = None, verbose: bool = False):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)
            verbose: Enable verbose logging
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.verbose = verbose

        if not self.webhook_url:
            if self.verbose:
                print("⚠ SLACK_WEBHOOK_URL not configured, notifications disabled")

    def send_readiness_alert(
        self,
        score: float,
        score_data: dict[str, Any],
        failing_workflows: list[dict[str, Any]] | None = None,
        blockers: list[str] | None = None,
    ) -> bool:
        """
        Send readiness score alert to Slack.

        Args:
            score: Current readiness score percentage
            score_data: Detailed score breakdown
            failing_workflows: List of failing workflow information
            blockers: List of blocking issues

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.webhook_url:
            if self.verbose:
                print("⚠ Cannot send Slack notification: webhook URL not configured")
            return False

        # Determine color and urgency
        if score >= 90:
            color = "good"
            emoji = "✅"
            urgency = "INFO"
        elif score >= 80:
            color = "warning"
            emoji = "⚠️"
            urgency = "WARNING"
        else:
            color = "danger"
            emoji = "🚨"
            urgency = "ALERT"

        # Build message
        message = {
            "username": "Release Dashboard Bot",
            "icon_emoji": ":rocket:",
            "attachments": [
                {
                    "fallback": f"Release Readiness: {score}%",
                    "color": color,
                    "pretext": f"{emoji} *Release Readiness Update* - {urgency}",
                    "title": f"v0.7.0 Release Readiness Score: {score}%",
                    "title_link": "https://github.com/MAGSASA-CARD-ERP/MAGSASA-CARD-ERP/blob/main/v0.7.0-release-checklist.md",
                    "fields": [
                        {
                            "title": "Status",
                            "value": score_data.get("status_text", "Unknown"),
                            "short": True,
                        },
                        {"title": "Target", "value": "95% for release", "short": True},
                        {
                            "title": "Core Gates",
                            "value": f"{score_data['core_passing']}/{score_data['core_total']} ({score_data['core_score']}%)",
                            "short": True,
                        },
                        {
                            "title": "Deployment",
                            "value": f"{score_data['deployment_passing']}/{score_data['deployment_total']} ({score_data['deployment_score']}%)",
                            "short": True,
                        },
                    ],
                    "footer": "Release Dashboard Updater",
                    "footer_icon": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                    "ts": int(datetime.now().timestamp()),
                }
            ],
        }

        # Add failing workflows section if any
        if failing_workflows and len(failing_workflows) > 0:
            workflows_text = ""
            for wf in failing_workflows[:3]:  # Top 3
                workflows_text += f"• *{wf['name']}*: {wf['count']} recent failures\n"
                workflows_text += f"  <{wf['url']}|View workflow>\n"

            message["attachments"].append(
                {
                    "color": "danger",
                    "title": "❌ Failing Workflows",
                    "text": workflows_text,
                    "mrkdwn_in": ["text"],
                }
            )

        # Add blockers section if any
        if blockers and len(blockers) > 0:
            blockers_text = "\n".join([f"• {b}" for b in blockers[:5]])  # Top 5

            message["attachments"].append(
                {
                    "color": "warning",
                    "title": "🚧 Current Blockers",
                    "text": blockers_text,
                    "mrkdwn_in": ["text"],
                }
            )

        # Add action buttons
        message["attachments"].append(
            {
                "fallback": "View Release Checklist",
                "actions": [
                    {
                        "type": "button",
                        "text": "📋 View Checklist",
                        "url": "https://github.com/MAGSASA-CARD-ERP/MAGSASA-CARD-ERP/blob/main/v0.7.0-release-checklist.md",
                    },
                    {
                        "type": "button",
                        "text": "🔧 View CI Runs",
                        "url": "https://github.com/MAGSASA-CARD-ERP/MAGSASA-CARD-ERP/actions",
                    },
                ],
            }
        )

        # Send notification
        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            response.raise_for_status()

            if self.verbose:
                print(
                    f"✓ Slack notification sent successfully (status: {response.status_code})"
                )

            return True

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"✗ Failed to send Slack notification: {e}")
            return False

    def send_success_notification(self, score: float) -> bool:
        """
        Send a success notification when readiness is high.

        Args:
            score: Current readiness score

        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            return False

        message = {
            "username": "Release Dashboard Bot",
            "icon_emoji": ":rocket:",
            "text": f":tada: *Great news!* Release readiness is at *{score}%* - we're ready to ship! :ship:",
            "attachments": [
                {
                    "color": "good",
                    "title": "Next Steps",
                    "text": "• Review final checklist\n• Get stakeholder approvals\n• Prepare release notes\n• Schedule deployment window",
                    "footer": "Release Dashboard Updater",
                }
            ],
        }

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            response.raise_for_status()

            if self.verbose:
                print(f"✓ Success notification sent (status: {response.status_code})")

            return True

        except Exception as e:
            if self.verbose:
                print(f"✗ Failed to send success notification: {e}")
            return False

    def send_custom_message(
        self, text: str, attachments: list[dict] | None = None
    ) -> bool:
        """
        Send a custom Slack message.

        Args:
            text: Main message text
            attachments: Optional Slack attachments

        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            return False

        message = {
            "username": "Release Dashboard Bot",
            "icon_emoji": ":robot_face:",
            "text": text,
        }

        if attachments:
            message["attachments"] = attachments

        try:
            response = requests.post(self.webhook_url, json=message, timeout=10)
            response.raise_for_status()

            if self.verbose:
                print(f"✓ Custom message sent (status: {response.status_code})")

            return True

        except Exception as e:
            if self.verbose:
                print(f"✗ Failed to send custom message: {e}")
            return False
