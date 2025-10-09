# 🔔 Slack CI Notification System

A comprehensive Slack notification system for GitHub Actions CI/CD workflows with coverage enforcement and PR author mentions.

## 🎯 Features

- **🚨 Failure Notifications**: Automatic alerts when PRs fail CI checks
- **🎉 Success Notifications**: Optional celebration messages for passing PRs
- **👤 Author Mentions**: Direct mentions of PR authors for immediate attention
- **📊 Coverage Details**: Real-time coverage percentages and deficit calculations
- **🔗 Action Buttons**: Direct links to PR and coverage reports
- **🎨 Rich Formatting**: Beautiful Slack Block Kit messages with emojis and formatting

## 🚀 Quick Start

### 1. Slack Webhook Setup

1. Go to your Slack workspace
2. Navigate to **Apps** → **Incoming Webhooks**
3. Click **Add to Slack**
4. Choose your CI channel (e.g., `#ci-alerts`)
5. Copy the webhook URL

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

```bash
# Required: Slack webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: Enable success notifications (default: disabled)
SLACK_SUCCESS_NOTIFICATIONS=true
```

### 3. Test the Setup

```bash
# Test with your webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Validate payload format
python scripts/test_slack_ci_notifications.py --validate-only

# Test failure notification
python scripts/test_slack_ci_notifications.py --test-type failure

# Test success notification
python scripts/test_slack_ci_notifications.py --test-type success

# Test both (default)
python scripts/test_slack_ci_notifications.py
```

## 📋 Workflow Integration

The system is already integrated into `.github/workflows/merge-gate.yml` with the following behavior:

### Failure Notifications
- **Triggers**: When any CI job fails (`if: failure()`)
- **Content**: 
  - Repository, PR number, title, author, branch
  - Specific failure reasons (coverage, quality, security)
  - Coverage percentage and deficit
  - Direct mention of PR author
  - Action buttons for PR and coverage reports

### Success Notifications
- **Triggers**: When all CI jobs pass (`if: success()`)
- **Content**:
  - Repository, PR number, title, author, branch
  - Coverage percentage and merge score
  - Celebration message with author mention
  - Action buttons for PR and coverage reports
- **Control**: Only sent if `SLACK_SUCCESS_NOTIFICATIONS=true`

## 🎨 Message Examples

### Failure Notification
```
🚨 Merge Gate Failed 🚨

📁 Repository: magsasa-ci-template
🔀 PR: #42 - Refactor policy loader
👤 Author: @gerome
🌿 Branch: feature/coverage-improvements

❌ Failure Reasons:
• 📊 Coverage below 85.0% threshold
• 🧹 Code quality issues (linting/formatting)

📊 Coverage: 83.4% (1.6% below threshold)
🎯 Required: 85.0%

[🔗 View PR] [📊 Coverage Report]

⚠️ @gerome Please address the issues above before this PR can be merged.

🤖 Automated by Merge Gate • Coverage enforcement active
```

### Success Notification
```
🎉 Merge Gate Passed! 🎉

📁 Repository: magsasa-ci-template
🔀 PR: #43 - Add comprehensive test coverage
👤 Author: @gerome
🌿 Branch: feature/test-coverage

📊 Coverage: 92.3% ✅
🎯 Required: 85.0%
📈 Merge Score: 95.2%
✅ All Checks: PASSED

[🔗 View PR] [📊 Coverage Report]

🎉 @gerome Great job! This PR meets all requirements and is ready to merge.

🤖 Automated by Merge Gate • All quality checks passed
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | Yes | - | Slack incoming webhook URL |
| `SLACK_SUCCESS_NOTIFICATIONS` | No | `false` | Enable success notifications |

### Workflow Conditions

| Condition | Description |
|-----------|-------------|
| `if: failure()` | Send failure notification when any job fails |
| `if: success()` | Send success notification when all jobs pass |
| `if: always() && github.event_name == 'pull_request'` | Only run for PR events |

## 🧪 Testing

### Manual Testing

```bash
# Test payload validation only
python scripts/test_slack_ci_notifications.py --validate-only

# Test specific notification types
python scripts/test_slack_ci_notifications.py --test-type failure
python scripts/test_slack_ci_notifications.py --test-type success

# Test with custom webhook URL
python scripts/test_slack_ci_notifications.py --webhook-url "https://hooks.slack.com/services/..."
```

### Automated Testing

The test script validates:
- ✅ Payload structure and required fields
- ✅ Block Kit format compliance
- ✅ Button URLs and accessibility
- ✅ Message content and formatting
- ✅ Actual webhook delivery

## 🛠️ Customization

### Customizing Message Content

Edit the workflow file to modify message content:

```yaml
# In .github/workflows/merge-gate.yml
- name: 🔔 Notify Slack on Failure
  run: |
    # Customize PR information extraction
    PR_NUMBER="${{ github.event.pull_request.number }}"
    PR_TITLE="${{ github.event.pull_request.title }}"
    # ... rest of the script
```

### Adding Custom Fields

Extend the payload structure:

```json
{
  "type": "section",
  "fields": [
    {
      "type": "mrkdwn",
      "text": "*🕒 Build Time:*\n${BUILD_DURATION}"
    },
    {
      "type": "mrkdwn", 
      "text": "*🏷️ Tags:*\n${PR_LABELS}"
    }
  ]
}
```

### Channel-Specific Notifications

Modify the webhook URL or add channel parameter:

```yaml
env:
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  SLACK_CHANNEL: "#ci-alerts"  # Optional channel override
```

## 🔍 Troubleshooting

### Common Issues

1. **No notifications received**
   - Check `SLACK_WEBHOOK_URL` secret is configured
   - Verify webhook URL is correct and active
   - Check workflow logs for error messages

2. **Success notifications not working**
   - Ensure `SLACK_SUCCESS_NOTIFICATIONS=true` is set
   - Verify all CI jobs are passing (not just some)

3. **Author mentions not working**
   - Ensure GitHub usernames match Slack usernames
   - Check if user exists in the Slack workspace

4. **Payload validation errors**
   - Run `python scripts/test_slack_ci_notifications.py --validate-only`
   - Check for missing required fields or invalid block types

### Debug Mode

Enable debug logging in the workflow:

```yaml
- name: 🔔 Notify Slack on Failure
  run: |
    set -x  # Enable debug mode
    echo "Debug: PR_NUMBER=$PR_NUMBER"
    echo "Debug: PAYLOAD=$PAYLOAD"
    # ... rest of script
```

## 📊 Monitoring

### Workflow Status

Monitor notification delivery in GitHub Actions:
- Check the `slack-notifications` job status
- Review logs for webhook delivery confirmation
- Verify Slack channel receives messages

### Slack Integration Health

- Set up Slack app monitoring
- Track webhook response times
- Monitor notification delivery rates

## 🔐 Security Considerations

- ✅ Webhook URLs stored as GitHub secrets
- ✅ No sensitive data in notification messages
- ✅ PR information limited to public repository data
- ✅ Author mentions use GitHub usernames only

## 🚀 Future Enhancements

### Planned Features

- **📈 Coverage Trends**: Include coverage history and trends
- **🎯 Custom Thresholds**: Per-repository coverage requirements
- **🔔 Smart Notifications**: Reduce noise with intelligent filtering
- **📱 Mobile Optimization**: Enhanced mobile Slack experience
- **🤖 Bot Interactions**: Interactive Slack bot for CI management

### Integration Opportunities

- **Jira Integration**: Link PRs to Jira tickets
- **PagerDuty**: Escalation for critical failures
- **Teams Integration**: Microsoft Teams webhook support
- **Discord**: Discord webhook compatibility

## 📚 Related Documentation

- [GitHub Actions Workflows](../.github/workflows/)
- [Coverage Enforcement](../scripts/hooks/enforce_coverage.py)
- [Slack Block Kit](https://api.slack.com/block-kit)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## 🤝 Contributing

To contribute to the Slack notification system:

1. Test your changes with the test script
2. Update documentation for new features
3. Ensure backward compatibility
4. Add appropriate error handling
5. Follow the existing code style

---

*Built with ❤️ for better CI/CD communication*
