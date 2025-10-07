#!/usr/bin/env python3
"""
Local Slack webhook tester.
Usage:
  export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
  python scripts/test_slack_webhook.py
"""
import json
import os
import sys
import urllib.request

WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "").strip() or (
    sys.argv[1] if len(sys.argv) > 1 else ""
)

payload = {
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🧪 Slack Webhook Test — Build Report Card",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": "*Env:*\nlocal"},
                {"type": "mrkdwn", "text": "*Status:*\n✅ connected"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "This is a sample message to verify the Incoming Webhook configuration.\nIf you can see this in your channel, you're good to go! ✅",
            },
        },
    ]
}


def main():
    if not WEBHOOK:
        print("Missing SLACK_WEBHOOK_URL (env or argv).")
        return 2
    req = urllib.request.Request(
        WEBHOOK,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        print(f"OK: {resp.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
