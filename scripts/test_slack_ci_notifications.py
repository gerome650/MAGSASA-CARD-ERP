#!/usr/bin/env python3
"""
Test script for Slack CI notification system.
Validates payload format and tests both failure and success scenarios.

Usage:
  export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
  python scripts/test_slack_ci_notifications.py [--test-type failure|success|both]
"""

import argparse
import os
import sys

import requests


class SlackCINotificationTester:
    """Test Slack CI notification payloads and functionality."""

    def __init__(self, webhook_url: str = None):
        """Initialize tester with webhook URL."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL environment variable is required")

    def create_failure_payload(
        self,
        pr_number: str = "42",
        pr_title: str = "Refactor policy loader",
        pr_author: str = "gerome",
        pr_url: str = "https://github.com/gerome/magsasa-ci-template/pull/42",
        repo: str = "magsasa-ci-template",
        branch: str = "feature/coverage-improvements",
        coverage: str = "83.4",
        threshold: str = "85.0",
        failures: list = None,
    ) -> dict:
        """Create a failure notification payload."""
        if failures is None:
            failures = [
                "📊 Coverage below 85.0% threshold",
                "🧹 Code quality issues (linting/formatting)",
            ]

        # Calculate coverage deficit
        coverage_deficit = ""
        if coverage and threshold:
            try:
                deficit = float(threshold) - float(coverage)
                coverage_deficit = f" ({deficit:.1f}% below threshold)"
            except (ValueError, TypeError):
                pass

        # Build failure details
        failure_details = "\n".join([f"• {failure}" for failure in failures])

        # Create payload
        payload = {
            "text": f"🚨 Merge Gate Failed - PR #{pr_number}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 Merge Gate Failed 🚨",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*📁 Repository:*\n{repo}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*🔀 PR:*\n#{pr_number} - {pr_title}",
                        },
                        {"type": "mrkdwn", "text": f"*👤 Author:*\n@{pr_author}"},
                        {"type": "mrkdwn", "text": f"*🌿 Branch:*\n{branch}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*❌ Failure Reasons:*\n{failure_details}",
                    },
                },
            ],
        }

        # Add coverage information
        if coverage:
            coverage_section = {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*📊 Coverage:*\n{coverage}%{coverage_deficit}",
                    },
                    {"type": "mrkdwn", "text": f"*🎯 Required:*\n{threshold}%"},
                ],
            }
            payload["blocks"].append(coverage_section)

        # Add action buttons
        actions_section = {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔗 View PR", "emoji": True},
                    "url": pr_url,
                    "style": "primary",
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Coverage Report",
                        "emoji": True,
                    },
                    "url": f"{pr_url}/checks",
                },
            ],
        }
        payload["blocks"].append(actions_section)

        # Add mention and context
        mention_section = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"⚠️ <@{pr_author}> Please address the issues above before this PR can be merged.",
            },
        }
        payload["blocks"].append(mention_section)

        context_section = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 Automated by Merge Gate • Coverage enforcement active",
                }
            ],
        }
        payload["blocks"].append(context_section)

        return payload

    def create_success_payload(
        self,
        pr_number: str = "43",
        pr_title: str = "Add comprehensive test coverage",
        pr_author: str = "gerome",
        pr_url: str = "https://github.com/gerome/magsasa-ci-template/pull/43",
        repo: str = "magsasa-ci-template",
        branch: str = "feature/test-coverage",
        coverage: str = "92.3",
        threshold: str = "85.0",
        score: str = "95.2",
    ) -> dict:
        """Create a success notification payload."""
        payload = {
            "text": f"🎉 Merge Gate Passed - PR #{pr_number}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎉 Merge Gate Passed! 🎉",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*📁 Repository:*\n{repo}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*🔀 PR:*\n#{pr_number} - {pr_title}",
                        },
                        {"type": "mrkdwn", "text": f"*👤 Author:*\n@{pr_author}"},
                        {"type": "mrkdwn", "text": f"*🌿 Branch:*\n{branch}"},
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*📊 Coverage:*\n{coverage}% ✅"},
                        {"type": "mrkdwn", "text": f"*🎯 Required:*\n{threshold}%"},
                        {"type": "mrkdwn", "text": f"*📈 Merge Score:*\n{score}%"},
                        {"type": "mrkdwn", "text": "*✅ All Checks:*\nPASSED"},
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 View PR",
                                "emoji": True,
                            },
                            "url": pr_url,
                            "style": "primary",
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "📊 Coverage Report",
                                "emoji": True,
                            },
                            "url": f"{pr_url}/checks",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🎉 <@{pr_author}> Great job! This PR meets all requirements and is ready to merge.",
                    },
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🤖 Automated by Merge Gate • All quality checks passed",
                        }
                    ],
                },
            ],
        }
        return payload

    def validate_payload(self, payload: dict) -> tuple[bool, list]:
        """Validate Slack payload structure."""
        errors = []

        # Check required fields
        if "blocks" not in payload:
            errors.append("Missing 'blocks' field")
        else:
            blocks = payload["blocks"]
            if not isinstance(blocks, list):
                errors.append("'blocks' must be an array")
            elif len(blocks) == 0:
                errors.append("'blocks' array cannot be empty")
            else:
                # Validate block structure
                for i, block in enumerate(blocks):
                    if "type" not in block:
                        errors.append(f"Block {i}: Missing 'type' field")
                    elif block["type"] not in [
                        "header",
                        "section",
                        "divider",
                        "context",
                        "actions",
                        "input",
                        "file",
                        "image",
                    ]:
                        errors.append(
                            f"Block {i}: Invalid block type '{block['type']}'"
                        )

                    # Validate section blocks
                    if block.get("type") == "section" and "fields" in block:
                        for j, field in enumerate(block["fields"]):
                            if "type" not in field or field["type"] not in [
                                "mrkdwn",
                                "plain_text",
                            ]:
                                errors.append(
                                    f"Block {i}, Field {j}: Invalid field type"
                                )
                            if "text" not in field:
                                errors.append(
                                    f"Block {i}, Field {j}: Missing 'text' field"
                                )

                    # Validate actions blocks
                    if block.get("type") == "actions":
                        if "elements" not in block:
                            errors.append(
                                f"Block {i}: Actions block missing 'elements'"
                            )
                        else:
                            for j, element in enumerate(block["elements"]):
                                if (
                                    element.get("type") == "button"
                                    and "url" not in element
                                ):
                                    errors.append(
                                        f"Block {i}, Element {j}: Button missing 'url'"
                                    )

        return len(errors) == 0, errors

    def send_notification(
        self, payload: dict, description: str = "Test notification"
    ) -> bool:
        """Send notification to Slack."""
        try:
            print(f"📤 Sending {description}...")
            print(f"📋 Payload preview: {payload.get('text', 'No text field')}")

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                print(f"✅ {description} sent successfully")
                return True
            else:
                print(f"❌ Failed to send {description}: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending {description}: {e}")
            return False

    def test_failure_notification(self) -> bool:
        """Test failure notification."""
        print("\n🧪 Testing Failure Notification...")
        payload = self.create_failure_payload()

        # Validate payload
        is_valid, errors = self.validate_payload(payload)
        if not is_valid:
            print(f"❌ Payload validation failed: {errors}")
            return False

        print("✅ Payload validation passed")
        return self.send_notification(payload, "failure notification")

    def test_success_notification(self) -> bool:
        """Test success notification."""
        print("\n🧪 Testing Success Notification...")
        payload = self.create_success_payload()

        # Validate payload
        is_valid, errors = self.validate_payload(payload)
        if not is_valid:
            print(f"❌ Payload validation failed: {errors}")
            return False

        print("✅ Payload validation passed")
        return self.send_notification(payload, "success notification")

    def test_both(self) -> bool:
        """Test both failure and success notifications."""
        print("🧪 Testing Both Notification Types...")
        failure_success = self.test_failure_notification()
        success_success = self.test_success_notification()
        return failure_success and success_success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Slack CI notifications")
    parser.add_argument(
        "--test-type",
        choices=["failure", "success", "both"],
        default="both",
        help="Type of notification to test",
    )
    parser.add_argument(
        "--webhook-url",
        help="Slack webhook URL (overrides SLACK_WEBHOOK_URL env var)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate payloads, don't send",
    )

    args = parser.parse_args()

    try:
        tester = SlackCINotificationTester(args.webhook_url)

        if args.validate_only:
            print("🔍 Validating payloads only...")
            failure_payload = tester.create_failure_payload()
            success_payload = tester.create_success_payload()

            failure_valid, failure_errors = tester.validate_payload(failure_payload)
            success_valid, success_errors = tester.validate_payload(success_payload)

            print(
                f"\n📋 Failure Payload: {'✅ Valid' if failure_valid else '❌ Invalid'}"
            )
            if failure_errors:
                for error in failure_errors:
                    print(f"  - {error}")

            print(
                f"\n📋 Success Payload: {'✅ Valid' if success_valid else '❌ Invalid'}"
            )
            if success_errors:
                for error in success_errors:
                    print(f"  - {error}")

            sys.exit(0 if (failure_valid and success_valid) else 1)

        # Run tests
        if args.test_type == "failure":
            success = tester.test_failure_notification()
        elif args.test_type == "success":
            success = tester.test_success_notification()
        else:  # both
            success = tester.test_both()

        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
