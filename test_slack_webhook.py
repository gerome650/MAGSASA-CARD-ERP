#!/usr/bin/env python3
"""
Slack Webhook Multi-Payload Test Script

A comprehensive diagnostic tool for testing Slack webhook connections with multiple
payload types. This script helps verify webhook connectivity, message formatting,
and error handling before integrating Slack notifications into CI/CD pipelines.

Usage:
    # Set the environment variable
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXX/XXXX/XXXXXXXX"

    # Test with different payload types
    python3 test_slack_webhook.py --basic    # Simple text message (default)
    python3 test_slack_webhook.py --rich     # Full Block Kit formatted message
    python3 test_slack_webhook.py --error    # Intentionally invalid payload

    # Run directly
    chmod +x test_slack_webhook.py
    ./test_slack_webhook.py --rich

Examples:
    # Test basic connectivity
    ./test_slack_webhook.py

    # Preview how CI notifications will render
    ./test_slack_webhook.py --rich

    # Test error handling and API responses
    ./test_slack_webhook.py --error

Requirements:
    - requests library (install via: pip install requests)
    - Valid Slack Incoming Webhook URL

Environment Variables:
    SLACK_WEBHOOK_URL: The Slack Incoming Webhook URL (required)

Exit Codes:
    0: Success - message sent successfully
    1: Failure - environment variable missing or request failed
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

import requests


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments to determine which payload type to test.

    Returns:
        argparse.Namespace: Parsed arguments with payload_type attribute
    """
    parser = argparse.ArgumentParser(
        description="Test Slack webhook with different payload types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --basic     Send a simple text message
  %(prog)s --rich      Send a full Block Kit formatted message
  %(prog)s --error     Send an invalid payload to test error handling
        """,
    )

    # Create mutually exclusive group for payload types
    payload_group = parser.add_mutually_exclusive_group()
    payload_group.add_argument(
        "--basic",
        action="store_const",
        const="basic",
        dest="payload_type",
        help="Send a basic text payload (default)",
    )
    payload_group.add_argument(
        "--rich",
        action="store_const",
        const="rich",
        dest="payload_type",
        help="Send a rich Block Kit formatted payload",
    )
    payload_group.add_argument(
        "--error",
        action="store_const",
        const="error",
        dest="payload_type",
        help="Send an invalid payload to test error handling",
    )

    # Set default payload type if none specified
    parser.set_defaults(payload_type="basic")

    return parser.parse_args()


def check_webhook_url() -> str:
    """
    Check if the Slack webhook URL is set in environment variables.

    Returns:
        str: The webhook URL

    Exits:
        Exits with code 1 if SLACK_WEBHOOK_URL is not set
    """
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

    if not webhook_url:
        print("=" * 80)
        print("❌ ERROR: SLACK_WEBHOOK_URL environment variable is not set!")
        print("=" * 80)
        print()
        print("📋 Setup Instructions:")
        print()
        print("   1. Create or locate your Slack Incoming Webhook:")
        print("      → https://api.slack.com/messaging/webhooks")
        print()
        print("   2. Set the environment variable:")
        print(
            "      export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXX/XXX/XXX'"
        )
        print()
        print("   3. Run this script with a test mode:")
        print("      python3 test_slack_webhook.py --basic   # Simple message")
        print(
            "      python3 test_slack_webhook.py --rich    # Full CI-style notification"
        )
        print("      python3 test_slack_webhook.py --error   # Error simulation")
        print()
        sys.exit(1)

    return webhook_url


def create_basic_payload() -> dict[str, Any]:
    """
    Create a simple basic text payload for webhook testing.

    Returns:
        dict: Basic JSON payload with text message
    """
    payload = {
        "text": "✅ *Webhook Connection Test Successful!*\n\nThis is a basic text message to verify that your Slack webhook is properly configured and working."
    }

    return payload


def create_rich_payload() -> dict[str, Any]:
    """
    Create a rich Block Kit payload simulating a real CI notification.
    This payload mimics the format used in production CI/CD pipelines.

    Returns:
        dict: Rich Block Kit formatted payload with multiple sections
    """
    # Get current timestamp for realistic display
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get PR author from environment variable (set by GitHub Actions)
    pr_author = os.getenv("PR_AUTHOR", "unknown")
    pr_number = os.getenv("PR_NUMBER", "42")
    pr_title = os.getenv("PR_TITLE", "Test Pull Request")
    coverage = os.getenv("COVERAGE", "92.3")
    threshold = os.getenv("THRESHOLD", "85")

    # Determine if this is a failure or success based on coverage
    try:
        is_failure = float(coverage) < float(threshold)
    except (ValueError, TypeError):
        is_failure = False

    # Build appropriate message
    if is_failure:
        status_text = "❌ Failed"
        status_emoji = "🚨"
        header_text = f"🚨 CI Failed for PR #{pr_number}"
        message = f"⚠️ *@{pr_author}* — Your PR has failing checks."
        details = f"• Coverage: {coverage}% (required: {threshold}%)\n• Action Required: Add more tests to improve coverage"
    else:
        status_text = "✅ Success"
        status_emoji = "🎉"
        header_text = f"✅ CI Passed for PR #{pr_number}"
        message = f"🎉 *Great work @{pr_author}!* All checks passed."
        details = f"• All tests passed ✓\n• Code quality checks passed ✓\n• Security scan completed ✓\n• Coverage: {coverage}% 📊"

    payload = {
        "text": f"{status_emoji} CI Notification for PR #{pr_number} by @{pr_author}",  # Fallback text
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_text, "emoji": True},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": message}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n{status_text}"},
                    {"type": "mrkdwn", "text": f"*PR Author:*\n@{pr_author}"},
                    {"type": "mrkdwn", "text": f"*Coverage:*\n{coverage}% 📊"},
                    {"type": "mrkdwn", "text": f"*Required:*\n{threshold}%"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Details:*\n{details}"},
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📦 *Repository:* `MAGSASA-CARD-ERP`\n📝 *PR:* #{pr_number} - {pr_title}\n👤 *Author:* @{pr_author}",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Pull Request 🔗",
                            "emoji": True,
                        },
                        "url": f"https://github.com/owner/repo/pull/{pr_number}",
                        "style": "primary" if not is_failure else "danger",
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Build Logs 📋",
                            "emoji": True,
                        },
                        "url": "https://github.com/owner/repo/actions",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🧪 Automated CI notification | 📅 {timestamp} | 👤 @{pr_author}",
                    }
                ],
            },
        ],
    }

    return payload


def create_error_payload() -> dict[str, Any]:
    """
    Create an intentionally invalid payload to test error handling.
    This helps verify how Slack responds to malformed requests.

    Returns:
        dict: Invalid payload that will trigger a Slack error response
    """
    # Create a deliberately malformed payload
    # Missing required fields and invalid structure
    payload = {
        "invalid_field": "This should not work",
        "blocks": [
            {"type": "invalid_type", "random_field": "test"}  # Invalid block type
        ],
    }

    return payload


def get_payload(payload_type: str) -> tuple[dict[str, Any], str]:
    """
    Get the appropriate payload based on the selected type.

    Args:
        payload_type: Type of payload ('basic', 'rich', or 'error')

    Returns:
        tuple: (payload dict, description string)
    """
    if payload_type == "basic":
        return create_basic_payload(), "Basic Text Message"
    elif payload_type == "rich":
        return create_rich_payload(), "Rich Block Kit Message (CI-Style)"
    elif payload_type == "error":
        return create_error_payload(), "Invalid Payload (Error Simulation)"
    else:
        return create_basic_payload(), "Basic Text Message"


def send_slack_message(
    webhook_url: str, payload: dict[str, Any]
) -> tuple[bool, requests.Response]:
    """
    Send a message to the Slack webhook and return the response.

    Args:
        webhook_url: The Slack webhook URL
        payload: The message payload dictionary

    Returns:
        tuple: (success: bool, response: requests.Response object)
    """
    try:
        # Send POST request to Slack webhook
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        # Consider status 200 as success
        return (response.status_code == 200, response)

    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out after 15 seconds")
        print("   → Check your network connection or try again")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        print("❌ ERROR: Connection error")
        print(f"   → {str(e)}")
        print("   → Check your network connection and webhook URL")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print("❌ ERROR: Request failed")
        print(f"   → {str(e)}")
        sys.exit(1)


def print_response_details(
    response: requests.Response, success: bool, payload_type: str
) -> None:
    """
    Print detailed response information for debugging.

    Args:
        response: The requests.Response object from Slack
        success: Whether the request was successful
        payload_type: The type of payload that was sent
    """
    print()
    print("=" * 80)
    print("📡 SLACK API RESPONSE DETAILS")
    print("=" * 80)
    print()

    # Print HTTP status code with appropriate emoji
    status_emoji = "✅" if success else "⚠️"
    print(f"{status_emoji} HTTP Status Code: {response.status_code}")
    print()

    # Print raw response text
    print("📨 Raw Response:")
    if response.text:
        print(f"   {response.text}")
    else:
        print("   (Empty response - normal for successful Slack webhooks)")
    print()

    # Attempt to parse and pretty-print JSON response
    print("📦 Parsed JSON Response:")
    try:
        if response.text and response.text.strip():
            # Try to parse as JSON
            try:
                response_json = json.loads(response.text)
                print(json.dumps(response_json, indent=4))
            except json.JSONDecodeError:
                # For successful webhooks, Slack returns plain "ok" text
                print(f"   {response.text}")
        else:
            print("   (No JSON body - this is normal for successful webhook posts)")
    except Exception as e:
        print(f"   Error parsing response: {str(e)}")
    print()

    # Print selected response headers for debugging
    print("📋 Key Response Headers:")
    important_headers = [
        "content-type",
        "x-slack-req-id",
        "x-content-type-options",
        "date",
    ]
    for header in important_headers:
        if header in response.headers:
            print(f"   {header}: {response.headers[header]}")

    # Show all headers for error responses
    if not success:
        print()
        print("📋 All Response Headers:")
        for header, value in response.headers.items():
            if header.lower() not in important_headers:
                print(f"   {header}: {value}")

    print()
    print("=" * 80)


def print_payload_preview(payload: dict[str, Any], description: str) -> None:
    """
    Print a preview of the payload being sent.

    Args:
        payload: The payload dictionary
        description: Description of the payload type
    """
    print(f"📦 Payload Type: {description}")
    print()
    print("📄 Payload Structure:")
    print(json.dumps(payload, indent=4))
    print()


def print_success_summary(payload_type: str) -> None:
    """
    Print a success summary based on payload type.

    Args:
        payload_type: The type of payload that was sent
    """
    print("=" * 80)
    print("🎉 TEST PASSED! Message sent successfully!")
    print("=" * 80)
    print()

    if payload_type == "basic":
        print("✅ Basic text message delivered successfully")
        print("📬 Check your Slack channel for the simple test message")
    elif payload_type == "rich":
        print("✅ Rich Block Kit message delivered successfully")
        print("📬 Check your Slack channel for the formatted CI-style notification")
        print("💡 This is how your production CI notifications will look")
    elif payload_type == "error":
        print("⚠️  Note: You sent an invalid payload intentionally")
        print("📊 Review the API response above to understand error handling")

    print()
    print("🚀 Your Slack webhook is properly configured!")
    print("✨ You're ready to integrate Slack notifications into CI/CD")
    print()


def print_failure_summary(response: requests.Response, payload_type: str) -> None:
    """
    Print a failure summary with troubleshooting tips.

    Args:
        response: The failed response object
        payload_type: The type of payload that was sent
    """
    print("=" * 80)
    print("⚠️  TEST FAILED! Message was not sent successfully")
    print("=" * 80)
    print()

    # Special message for intentional error test
    if payload_type == "error":
        print("✅ Expected Result: You sent an invalid payload intentionally")
        print("📊 This is the expected behavior for malformed payloads")
        print()
        print("🔍 Error Details from Slack API:")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        print()
        print("💡 This demonstrates how Slack handles invalid requests")
        return

    # Troubleshooting tips for real failures
    print("🔍 Troubleshooting Guide:")
    print()

    if response.status_code == 404:
        print("   ❌ Status 404: Webhook Not Found")
        print("   → Your webhook URL is invalid or has been deleted")
        print("   → Solution: Generate a new webhook URL in Slack:")
        print("     https://api.slack.com/messaging/webhooks")
    elif response.status_code == 403:
        print("   ❌ Status 403: Forbidden")
        print("   → Permission denied or webhook is disabled")
        print("   → Solution: Check webhook permissions in Slack workspace settings")
    elif response.status_code == 400:
        print("   ❌ Status 400: Bad Request")
        print("   → Invalid payload format")
        print("   → Solution: Review the payload structure above")
        print("   → Verify Block Kit format: https://api.slack.com/block-kit")
    elif response.status_code == 500:
        print("   ❌ Status 500: Server Error")
        print("   → Slack is experiencing technical difficulties")
        print("   → Solution: Wait a moment and try again")
    elif response.status_code == 429:
        print("   ❌ Status 429: Too Many Requests")
        print("   → Rate limit exceeded")
        print("   → Solution: Wait before sending more messages")
    else:
        print(f"   ❌ Status {response.status_code}: Unexpected Error")
        print("   → Review the response details above")

    print()
    print("📚 Resources:")
    print("   • Webhook Documentation: https://api.slack.com/messaging/webhooks")
    print("   • Block Kit Builder: https://app.slack.com/block-kit-builder")
    print("   • API Reference: https://api.slack.com/methods")
    print()


def main():
    """
    Main function to orchestrate the multi-payload Slack webhook test.
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Print header
    print()
    print("=" * 80)
    print("🧪 SLACK WEBHOOK MULTI-PAYLOAD TEST")
    print("=" * 80)
    print()

    # Step 1: Check environment variable
    print("🔍 Step 1: Checking environment variables...")
    webhook_url = check_webhook_url()
    print("   ✅ SLACK_WEBHOOK_URL found")
    print(f"   🔗 URL: {webhook_url[:50]}...")
    print()

    # Step 2: Get the appropriate payload
    print(f"🎯 Step 2: Preparing payload (type: {args.payload_type})...")
    payload, description = get_payload(args.payload_type)
    print(f"   ✅ Payload created: {description}")
    print()

    # Step 3: Display payload preview
    print("👀 Step 3: Payload Preview...")
    print_payload_preview(payload, description)

    # Step 4: Send message to Slack
    print("📤 Step 4: Sending message to Slack...")
    print("   → Target: Slack Webhook API")
    print("   → Method: POST")
    print("   → Timeout: 15 seconds")
    print()

    success, response = send_slack_message(webhook_url, payload)

    # Step 5: Display response details
    print_response_details(response, success, args.payload_type)

    # Step 6: Print summary and exit
    if success:
        print_success_summary(args.payload_type)
        sys.exit(0)
    else:
        print_failure_summary(response, args.payload_type)
        # For error simulation, exit with 0 (since it worked as expected)
        sys.exit(0 if args.payload_type == "error" else 1)


if __name__ == "__main__":
    main()
