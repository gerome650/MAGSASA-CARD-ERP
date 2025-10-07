# 🚀 Slack Webhook Test - Quick Reference

## One-Line Setup
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXX/XXX/XXX"
```

## Three Test Commands

```bash
# 1️⃣ Basic connectivity test
python3 test_slack_webhook.py --basic

# 2️⃣ Preview CI notification format
python3 test_slack_webhook.py --rich

# 3️⃣ Test error handling
python3 test_slack_webhook.py --error
```

## Expected Results

| Mode | Status | What You'll See |
|------|--------|-----------------|
| `--basic` | ✅ 200 | Simple text message in Slack |
| `--rich` | ✅ 200 | Formatted notification with buttons |
| `--error` | ⚠️ 400 | Error response from Slack API |

## Common Issues

| Error | Quick Fix |
|-------|-----------|
| "SLACK_WEBHOOK_URL not set" | `export SLACK_WEBHOOK_URL="..."` |
| Status 404 | Regenerate webhook URL in Slack |
| Status 403 | Check channel permissions |
| Status 400 | Validate payload with Block Kit Builder |

## Resources

- 📚 Full Guide: `SLACK_WEBHOOK_TEST_GUIDE.md`
- 🛠️ Block Kit Builder: https://app.slack.com/block-kit-builder
- 📖 Webhooks Docs: https://api.slack.com/messaging/webhooks

---

**Ready for CI?** Once `--rich` test passes, you're good to integrate! 🎉


