# 🔧 Slack CI Notifications Setup Guide

Quick setup guide for configuring Slack webhooks for CI notifications.

## 📋 Prerequisites

- Admin access to your Slack workspace
- GitHub repository with Actions enabled
- Repository secrets management permissions

## 🚀 Step-by-Step Setup

### 1. Create Slack Incoming Webhook

1. **Navigate to Slack Apps**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"

2. **Configure App Details**
   - App Name: `CI/CD Notifications`
   - Workspace: Select your workspace
   - Click "Create App"

3. **Enable Incoming Webhooks**
   - In your app settings, go to "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to ON

4. **Create Webhook**
   - Click "Add New Webhook to Workspace"
   - Choose channel: `#ci-alerts` (or your preferred channel)
   - Click "Allow"

5. **Copy Webhook URL**
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### 2. Configure GitHub Secrets

1. **Go to Repository Settings**
   - Navigate to your GitHub repository
   - Click "Settings" tab

2. **Add Repository Secrets**
   - Click "Secrets and variables" → "Actions"
   - Click "New repository secret"

3. **Add Required Secrets**
   ```
   Name: SLACK_WEBHOOK_URL
   Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

4. **Optional: Enable Success Notifications**
   ```
   Name: SLACK_SUCCESS_NOTIFICATIONS
   Value: true
   ```

### 3. Test the Setup

1. **Validate Configuration**
   ```bash
   # Set webhook URL for testing
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   
   # Test payload validation
   python scripts/test_slack_ci_notifications.py --validate-only
   ```

2. **Send Test Notifications**
   ```bash
   # Test failure notification
   python scripts/test_slack_ci_notifications.py --test-type failure
   
   # Test success notification
   python scripts/test_slack_ci_notifications.py --test-type success
   ```

3. **Verify in Slack**
   - Check your `#ci-alerts` channel
   - Confirm messages appear with proper formatting
   - Test button links work correctly

## 🧪 Testing Checklist

- [ ] Webhook URL is correctly configured
- [ ] GitHub secrets are properly set
- [ ] Test notifications are received in Slack
- [ ] Message formatting looks correct
- [ ] Action buttons work properly
- [ ] Author mentions function correctly

## 🔍 Troubleshooting

### No Messages Received

1. **Check Webhook URL**
   - Verify URL is complete and correct
   - Ensure no extra spaces or characters

2. **Verify GitHub Secrets**
   - Confirm secret names match exactly: `SLACK_WEBHOOK_URL`
   - Check secret values are properly set

3. **Check Workflow Logs**
   - Go to Actions tab in GitHub
   - View workflow run logs
   - Look for error messages in Slack notification step

### Messages Malformed

1. **Validate Payload**
   ```bash
   python scripts/test_slack_ci_notifications.py --validate-only
   ```

2. **Check Block Kit Format**
   - Ensure proper JSON structure
   - Verify required fields are present

### Author Mentions Not Working

1. **Username Mapping**
   - GitHub usernames must match Slack usernames
   - Check user exists in Slack workspace

2. **Test with Known User**
   - Use a known Slack username for testing
   - Verify user permissions in channel

## 🎨 Customization

### Channel Configuration

**Option 1: Use Default Channel**
- Webhook posts to the channel it was created for

**Option 2: Override Channel**
```yaml
env:
  SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  SLACK_CHANNEL: "#custom-channel"
```

### Message Customization

Edit the workflow file to customize message content:

```yaml
# In .github/workflows/merge-gate.yml
- name: 🔔 Notify Slack on Failure
  run: |
    # Customize message content here
    PR_TITLE="${{ github.event.pull_request.title }}"
    # Add custom fields or modify existing ones
```

## 🔐 Security Best Practices

1. **Secret Management**
   - Never commit webhook URLs to code
   - Use GitHub secrets for all sensitive data
   - Rotate webhook URLs periodically

2. **Channel Permissions**
   - Limit channel access to relevant team members
   - Consider using private channels for sensitive projects

3. **Webhook Security**
   - Use dedicated webhook for CI notifications
   - Don't reuse webhooks for multiple purposes
   - Monitor webhook usage and access

## 📊 Monitoring

### GitHub Actions Monitoring

1. **Workflow Status**
   - Monitor `slack-notifications` job in Actions tab
   - Set up notifications for workflow failures

2. **Log Analysis**
   - Review logs for webhook delivery status
   - Check for timeout or connection errors

### Slack Integration Health

1. **Message Delivery**
   - Verify messages arrive consistently
   - Monitor for missing notifications

2. **User Engagement**
   - Track click-through rates on action buttons
   - Monitor response times to notifications

## 🚀 Advanced Configuration

### Multiple Channels

Create separate webhooks for different notification types:

```yaml
env:
  SLACK_FAILURE_WEBHOOK: ${{ secrets.SLACK_FAILURE_WEBHOOK }}
  SLACK_SUCCESS_WEBHOOK: ${{ secrets.SLACK_SUCCESS_WEBHOOK }}
```

### Conditional Notifications

```yaml
- name: 🔔 Notify Slack on Failure
  if: failure() && github.event.pull_request.base.ref == 'main'
  # Only notify for main branch PRs
```

### Custom Failure Thresholds

```yaml
- name: 🔔 Notify Slack on Failure
  if: failure() && contains(github.event.pull_request.labels.*.name, 'critical')
  # Only notify for critical PRs
```

## 📚 Additional Resources

- [Slack Incoming Webhooks Documentation](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [CI Notification Test Script](../scripts/test_slack_ci_notifications.py)

---

*Happy CI/CD monitoring! 🎉*
