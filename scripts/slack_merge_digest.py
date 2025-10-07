#!/usr/bin/env python3
"""
Slack Merge Quality Digest Builder
==================================

Builds rich Slack Block Kit messages for merge quality reporting.
Includes merge readiness scores, trend analysis, early warnings, and performance metrics.
"""

import argparse
import json
import sys
from datetime import datetime, timezone


class SlackMergeDigestBuilder:
    """Builds Slack Block Kit messages for merge quality reporting."""

    def __init__(self):
        self.colors = {
            "good": "#56d364",  # Green
            "warning": "#ffd33d",  # Yellow
            "danger": "#ff6a69",  # Red
            "info": "#6ea8fe",  # Blue
        }

    def build_merge_digest(self, payload_data: dict, repo_info: dict) -> dict:
        """
        Build complete Slack Block Kit message for merge quality digest.

        Args:
            payload_data: Merge quality payload data
            repo_info: Repository and run information

        Returns:
            Slack Block Kit message payload
        """
        merge_score = payload_data.get("merge_score", 0)
        team_goal = payload_data.get("team_goal", 90)
        streak = payload_data.get("streak_below_goal", 0)
        early_warning = payload_data.get("early_warning", False)
        auto_fail = payload_data.get("auto_fail", False)

        # Determine overall status and color
        if auto_fail:
            status_emoji = "🔥"
            status_text = "AUTO-FAIL"
            color = self.colors["danger"]
        elif early_warning:
            status_emoji = "⚠️"
            status_text = "EARLY WARNING"
            color = self.colors["warning"]
        elif merge_score >= team_goal:
            status_emoji = "✅"
            status_text = "ON TRACK"
            color = self.colors["good"]
        else:
            status_emoji = "🟠"
            status_text = "BELOW GOAL"
            color = self.colors["warning"]

        blocks = []

        # Header block
        blocks.append(
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Merge Quality Report — {repo_info.get('repo', 'Unknown Repo')}",
                    "emoji": True,
                },
            }
        )

        # Main metrics section
        blocks.append(
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*📊 Merge Readiness Score:*\n`{merge_score}%` {status_emoji}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*📈 Delta vs Last PR:*\n{self._format_delta(payload_data.get('delta_vs_last', 0))}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*📊 10-PR Rolling Average:*\n`{payload_data.get('rolling_average', 0)}%` {self._get_average_emoji(payload_data.get('rolling_average', 0), team_goal)}",
                    },
                    {"type": "mrkdwn", "text": f"*🎯 Team Goal:*\n`{team_goal}%+`"},
                ],
            }
        )

        # Trend sparkline section
        sparkline = payload_data.get("sparkline", "—")
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📉 10-PR Score Trend:*\n`{sparkline}`",
                },
            }
        )

        # Severity breakdown section
        severity = payload_data.get("severity", {})
        if any(severity.values()):
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔍 Issue Breakdown:*\n🔴 Critical: {severity.get('critical', 0)} | 🟠 Warning: {severity.get('warning', 0)} | 🟡 Info: {severity.get('info', 0)}",
                    },
                }
            )

        # Quality badges section
        badges = payload_data.get("badges", {})
        if badges:
            badge_text = " | ".join(
                [f"{emoji} {name.title()}" for name, emoji in badges.items()]
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🏆 Quality Gates:* {badge_text}",
                    },
                }
            )

        # Early warning section
        if early_warning or auto_fail:
            warning_text = self._build_warning_message(streak, auto_fail)
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": warning_text}}
            )

        # Performance metrics section
        workflows = payload_data.get("top_slowest_workflows", [])
        if workflows:
            perf_text = "*🐢 Top 3 Slowest Workflows:*\n"
            for i, workflow in enumerate(workflows[:3], 1):
                perf_text += f"{i}. {workflow['name']}: {workflow['duration']} ({workflow['percent']}%)\n"

            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": perf_text.strip()},
                }
            )

        # Repository info section
        blocks.append(
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:*\n`{repo_info.get('branch', 'unknown')}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Commit:*\n<{repo_info.get('commit_url', '#')}|{repo_info.get('commit', 'unknown')[:8]}>",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Actor:*\n{repo_info.get('actor', 'unknown')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Timestamp:*\n{self._format_timestamp(repo_info.get('timestamp'))}",
                    },
                ],
            }
        )

        # Action buttons
        action_elements = []

        if repo_info.get("run_url"):
            action_elements.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🔗 View Run",
                        "emoji": True,
                    },
                    "url": repo_info["run_url"],
                }
            )

        if repo_info.get("dashboard_url"):
            action_elements.append(
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 View Dashboard",
                        "emoji": True,
                    },
                    "url": repo_info["dashboard_url"],
                }
            )

        if action_elements:
            blocks.append({"type": "actions", "elements": action_elements})

        # Footer context
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🚦 Status: *{status_text}* | Streak below goal: *{streak}* | Generated by Merge Quality System",
                    }
                ],
            }
        )

        return {
            "blocks": blocks,
            "color": color,
            "metadata": {
                "merge_score": merge_score,
                "status": status_text,
                "auto_fail": auto_fail,
                "early_warning": early_warning,
            },
        }

    def _format_delta(self, delta: float) -> str:
        """Format delta value with appropriate emoji."""
        if delta > 0:
            return f"`+{delta}%` 📈"
        elif delta < 0:
            return f"`{delta}%` 📉"
        else:
            return f"`{delta}%` ➡️"

    def _get_average_emoji(self, average: float, goal: float) -> str:
        """Get emoji for rolling average vs goal."""
        if average >= goal:
            return "🟢"
        elif average >= goal * 0.9:
            return "🟠"
        else:
            return "🔴"

    def _build_warning_message(self, streak: int, auto_fail: bool) -> str:
        """Build early warning message."""
        if auto_fail:
            return f"🔥 *AUTO-FAIL TRIGGERED!* 🔥\n{streak} consecutive PRs below goal. Merge blocked until quality improves."
        elif streak >= 2:
            return f"⚠️ *EARLY WARNING: {streak}/3 Strikes* ⚠️\n{streak} consecutive PRs below goal. Next failure will block merge."
        else:
            return ""

    def _format_timestamp(self, timestamp: str | None) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return "Unknown"

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except (ValueError, AttributeError):
            return timestamp

    def send_to_slack(self, message: dict, webhook_url: str) -> bool:
        """
        Send message to Slack webhook.

        Args:
            message: Slack message payload
            webhook_url: Slack webhook URL

        Returns:
            True if successful, False otherwise
        """
        try:
            import requests

            response = requests.post(webhook_url, json=message, timeout=30)
            response.raise_for_status()
            return True

        except ImportError:
            print("Error: requests library not available")
            return False
        except Exception as e:
            print(f"Error sending to Slack: {e}")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Build and send Slack merge quality digest"
    )
    parser.add_argument(
        "--payload", required=True, help="Merge quality payload JSON file"
    )
    parser.add_argument("--repo", default="Unknown Repo", help="Repository name")
    parser.add_argument("--branch", default="main", help="Branch name")
    parser.add_argument("--commit", default="", help="Commit hash")
    parser.add_argument("--actor", default="", help="Actor (user) name")
    parser.add_argument("--run-url", help="GitHub Actions run URL")
    parser.add_argument("--dashboard-url", help="CI Dashboard URL")
    parser.add_argument("--webhook-url", help="Slack webhook URL")
    parser.add_argument("--output", help="Output file for Slack message (optional)")
    parser.add_argument(
        "--send", action="store_true", help="Send to Slack (requires webhook-url)"
    )

    args = parser.parse_args()

    # Load payload data
    try:
        with open(args.payload) as f:
            payload_data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading payload file: {e}")
        sys.exit(1)

    # Prepare repository info
    repo_info = {
        "repo": args.repo,
        "branch": args.branch,
        "commit": args.commit,
        "actor": args.actor,
        "run_url": args.run_url,
        "dashboard_url": args.dashboard_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Build Slack message
    builder = SlackMergeDigestBuilder()
    slack_message = builder.build_merge_digest(payload_data, repo_info)

    # Output message
    if args.output:
        with open(args.output, "w") as f:
            json.dump(slack_message, f, indent=2)
        print(f"Slack message saved to: {args.output}")

    # Send to Slack if requested
    if args.send:
        if not args.webhook_url:
            print("Error: --webhook-url required for --send")
            sys.exit(1)

        if builder.send_to_slack(slack_message, args.webhook_url):
            print("✅ Slack message sent successfully")
        else:
            print("❌ Failed to send Slack message")
            sys.exit(1)

    # Print summary
    metadata = slack_message.get("metadata", {})
    print(f"Merge Score: {metadata.get('merge_score', 0)}%")
    print(f"Status: {metadata.get('status', 'Unknown')}")

    if metadata.get("auto_fail"):
        print("🔥 Auto-fail triggered!")
        sys.exit(1)


if __name__ == "__main__":
    main()
