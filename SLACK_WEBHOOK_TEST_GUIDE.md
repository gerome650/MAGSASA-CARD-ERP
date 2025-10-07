# 🧪 Slack Webhook Test Guide

Complete guide for using `test_slack_webhook.py` to verify Slack webhook connectivity and message formatting.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Setup Instructions](#setup-instructions)
3. [Usage Examples](#usage-examples)
4. [Payload Types](#payload-types)
5. [Troubleshooting](#troubleshooting)
6. [CI Integration](#ci-integration)

---

## 🚀 Quick Start

```bash
# 1. Set your webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXX/XXXX/XXXXXXXX"

# 2. Run a basic test
python3 test_slack_webhook.py --basic

# 3. Test CI-style rich formatting
python3 test_slack_webhook.py --rich
```

---

## 🔧 Setup Instructions

### Step 1: Get Your Slack Webhook URL

1. Go to [Slack App Directory - Incoming Webhooks](https://api.slack.com/messaging/webhooks)
2. Click "Create New App" or select an existing app
3. Enable "Incoming Webhooks"
4. Click "Add New Webhook to Workspace"
5. Select the channel where messages will be posted
6. Copy the webhook URL (format: `https://hooks.slack.com/services/XXX/XXX/XXX`)

### Step 2: Set Environment Variable

```bash
# For current session (temporary)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# For permanent setup (add to ~/.bashrc or ~/.zshrc)
echo 'export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Install Dependencies

```bash
pip install requests
```

### Step 4: Make Script Executable (Optional)

```bash
chmod +x test_slack_webhook.py
./test_slack_webhook.py --help
```

---

## 📖 Usage Examples

### Test 1: Basic Text Message (Default)

Send a simple text message to verify basic connectivity:

```bash
python3 test_slack_webhook.py --basic
```

**What it does:**
- ✅ Verifies webhook URL is valid
- ✅ Tests basic message delivery
- ✅ Returns detailed API response

**Expected Output:**
```
🎉 TEST PASSED! Message sent successfully!
✅ Basic text message delivered successfully
📬 Check your Slack channel for the simple test message
```

---

### Test 2: Rich Block Kit Message (CI-Style)

Preview how production CI notifications will render:

```bash
python3 test_slack_webhook.py --rich
```

**What it does:**
- ✅ Sends a full Block Kit formatted message
- ✅ Includes header, status fields, coverage stats
- ✅ Shows action buttons (PR link, build logs)
- ✅ Demonstrates production-ready formatting

**Expected Slack Output:**
```
🚀 CI Notification Test
━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ Success          Environment: Production
Coverage: 92.3% 📊         Build Time: 3m 42s ⏱️

Build Details:
• All tests passed ✓
• Code quality checks passed ✓
• Security scan completed ✓
• Deployment ready 🚀

📦 Repository: MAGSASA-CARD-ERP
🌿 Branch: main
👤 Author: Test User

[View Pull Request 🔗]  [View Build Logs 📋]
```

---

### Test 3: Error Simulation

Test error handling and API error responses:

```bash
python3 test_slack_webhook.py --error
```

**What it does:**
- ⚠️ Sends an intentionally invalid payload
- ⚠️ Shows how Slack responds to malformed requests
- ✅ Helps understand error messages for debugging

**Expected Response:**
```
⚠️ Status 400: Bad Request
📨 Response: {
  "error": "invalid_blocks",
  "details": "blocks[0].type is invalid"
}
```

---

## 🎨 Payload Types Explained

### 1. Basic Payload (`--basic`)

**Structure:**
```json
{
  "text": "✅ *Webhook Connection Test Successful!*\n\nThis is a basic text message..."
}
```

**Use Case:**
- Quick connectivity tests
- Simple notifications
- Legacy systems that don't support Block Kit

---

### 2. Rich Payload (`--rich`)

**Structure:**
```json
{
  "text": "🚀 CI Notification Test",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 CI Notification Test"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Status:*\n✅ Success"},
        {"type": "mrkdwn", "text": "*Coverage:*\n92.3% 📊"}
      ]
    }
    // ... more blocks
  ]
}
```

**Features:**
- ✅ Header section with emoji
- ✅ Multi-column field layout
- ✅ Action buttons with links
- ✅ Dividers and context sections
- ✅ Markdown formatting support

**Use Case:**
- Production CI/CD notifications
- Detailed status reports
- Interactive messages with buttons

---

### 3. Error Payload (`--error`)

**Structure:**
```json
{
  "invalid_field": "This should not work",
  "blocks": [
    {
      "type": "invalid_type",
      "random_field": "test"
    }
  ]
}
```

**Use Case:**
- Testing error handling logic
- Understanding Slack API error messages
- Debugging payload validation issues

---

## 🔍 Troubleshooting

### Error: "SLACK_WEBHOOK_URL not set"

**Solution:**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/XXX/XXX"
```

---

### Error: Status 404 - Webhook Not Found

**Possible Causes:**
- Webhook URL is incorrect
- Webhook has been deleted or revoked
- URL contains typos or extra spaces

**Solution:**
1. Verify the webhook URL in Slack settings
2. Generate a new webhook URL if necessary
3. Update your environment variable

---

### Error: Status 403 - Forbidden

**Possible Causes:**
- Webhook is disabled
- Channel permissions changed
- Slack workspace security settings

**Solution:**
1. Check webhook status in Slack App settings
2. Verify channel still exists
3. Re-authorize the webhook

---

### Error: Status 400 - Bad Request

**Possible Causes:**
- Invalid Block Kit structure
- Malformed JSON payload
- Unsupported block types

**Solution:**
1. Validate payload structure using [Block Kit Builder](https://app.slack.com/block-kit-builder)
2. Check for syntax errors in custom payloads
3. Review Slack Block Kit documentation

---

### Connection Timeout

**Possible Causes:**
- Network connectivity issues
- Firewall blocking outbound requests
- Slack API experiencing issues

**Solution:**
1. Check internet connection
2. Test with: `curl -X POST $SLACK_WEBHOOK_URL -H 'Content-Type: application/json' -d '{"text":"test"}'`
3. Check Slack Status: https://status.slack.com/

---

## 🚀 CI Integration

Once you've verified the webhook works with this test script, you can integrate it into your CI/CD pipeline.

### GitHub Actions Example

```yaml
- name: Send Slack Notification
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  run: |
    python3 scripts/send_slack_notification.py \
      --status "${{ job.status }}" \
      --coverage "92.3%" \
      --pr-url "${{ github.event.pull_request.html_url }}"
```

### GitLab CI Example

```yaml
notify_slack:
  stage: notify
  script:
    - python3 test_slack_webhook.py --rich
  only:
    - main
```

---

## 📚 Additional Resources

- [Slack Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Block Kit Reference](https://api.slack.com/reference/block-kit)
- [Message Formatting](https://api.slack.com/reference/surfaces/formatting)

---

## 🎯 Best Practices

1. **Store webhook URL securely**
   - Use environment variables
   - Never commit webhook URLs to git
   - Use secret management in CI/CD

2. **Test before deploying**
   - Always run `--basic` test first
   - Verify `--rich` formatting matches expectations
   - Test error handling with `--error`

3. **Rate limiting**
   - Slack webhooks have rate limits
   - Don't send more than 1 message per second
   - Batch notifications when possible

4. **Message design**
   - Keep messages concise and actionable
   - Use emoji sparingly for visual hierarchy
   - Include relevant links (PR, logs, docs)
   - Test on mobile devices

---

## 💡 Pro Tips

- Use the `--rich` mode to preview exactly how CI notifications will look
- Run all three test modes before integrating into production
- Save successful payloads as templates for CI scripts
- Use the error details to improve error handling in your CI pipeline
- Test webhooks in a dedicated #testing channel first

---

## 🆘 Getting Help

If you encounter issues:

1. Run with `--error` to test error handling
2. Check the detailed API response output
3. Verify webhook URL in Slack settings
4. Review Slack API status: https://status.slack.com/
5. Consult [Slack API documentation](https://api.slack.com/)

---

**Happy Testing! 🚀**


