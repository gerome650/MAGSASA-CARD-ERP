# 🚀 CI Preflight Validation System

## Overview

The CI Preflight Validation System ensures that all code changes meet quality standards before they reach the CI/CD pipeline. This system runs comprehensive checks locally and provides immediate feedback with rich notifications.

## 🎯 Features

- **Automated Quality Checks**: Linting, formatting, type checking, and testing
- **Rich Notifications**: Slack and Email alerts with detailed failure reports
- **Git Hook Integration**: Automatic validation before every push
- **Emergency Bypass**: `--no-verify` option for urgent fixes
- **Branch-Aware**: Skips checks for main/release branches
- **Detailed Reporting**: HTML email reports with fix suggestions

## 📋 Prerequisites

### Required Tools
- `uv` - Python package manager
- `git` - Version control
- Python 3.10+

### Environment Setup
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync --dev

# Install pre-push hook
./scripts/setup_ci_preflight_hook.sh
```

## 🔧 Configuration

### Environment Variables

#### Slack Notifications
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export SLACK_CHANNEL="#ci-cd"  # Optional, defaults to #ci-cd
```

#### Email Notifications
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASS="your-app-password"
export FROM_EMAIL="your-email@gmail.com"
export ALERT_EMAIL="team@yourcompany.com"
```

#### Optional Configuration
```bash
export CI_LOGS_URL="https://ci.yourcompany.com/logs"  # For notification links
export PR_URL="https://github.com/yourorg/repo/pull/123"  # For notification links
```

## 🚀 Usage

### Manual Preflight Check
```bash
# Run full preflight validation
make ci-preflight

# Or run the script directly
python3 scripts/ci_preflight.py
```

### Individual Checks
```bash
# Linting (with auto-fix)
uv run ruff check . --fix

# Code formatting
uv run black .

# Type checking
uv run mypy . --ignore-missing-imports

# Unit tests
uv run pytest tests/

# MCP validation
make mcp-check

# Agent orchestration
make agent-run-all

# Build packages
uv build
```

### Git Integration

The pre-push hook runs automatically on every `git push`. It will:
1. Run all preflight checks
2. Block the push if any checks fail
3. Send notifications about failures
4. Allow bypass with `git push --no-verify`

## 📊 Checks Performed

### 1. Code Quality
- **Ruff Linting**: Style, complexity, and error detection
- **Black Formatting**: Consistent code formatting
- **Type Checking**: Static type analysis (optional)

### 2. Testing
- **Unit Tests**: Core functionality validation
- **Integration Tests**: Component interaction testing

### 3. System Validation
- **MCP Check**: Model Context Protocol validation
- **Agent Orchestration**: Multi-agent system testing
- **Build Validation**: Package compilation verification

## 📱 Notifications

### Slack Notifications
- **Rich Messages**: Formatted with attachments and action buttons
- **Real-time Alerts**: Immediate notification of failures
- **Branch Context**: Shows current branch and commit info
- **Action Links**: Direct links to logs and pull requests

### Email Notifications
- **HTML Reports**: Professional, detailed failure reports
- **Fix Suggestions**: Step-by-step remediation guidance
- **Team Distribution**: Notifies entire development team
- **Mobile Friendly**: Responsive design for mobile devices

## 🛠️ Troubleshooting

### Common Issues

#### "Command not found: uv"
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

#### "SLACK_WEBHOOK_URL not set"
```bash
# Set environment variable
export SLACK_WEBHOOK_URL="your-webhook-url"

# Or skip notifications
unset SLACK_WEBHOOK_URL
```

#### "SMTP authentication failed"
```bash
# For Gmail, use App Password instead of regular password
export SMTP_PASS="your-16-character-app-password"

# Enable 2FA and generate App Password at:
# https://myaccount.google.com/apppasswords
```

#### "Pre-push hook failed"
```bash
# Check hook is executable
chmod +x .git/hooks/pre-push

# Reinstall hook
./scripts/setup_ci_preflight_hook.sh

# Emergency bypass
git push --no-verify
```

### Debug Mode
```bash
# Run with verbose output
python3 scripts/ci_preflight.py --verbose

# Test notifications only
make notify-test
```

## 🔄 Workflow Integration

### GitHub Actions
Add to your `.github/workflows/ci.yml`:
```yaml
- name: Run CI Preflight
  run: |
    python3 scripts/ci_preflight.py
    if [ $? -ne 0 ]; then
      echo "Preflight failed"
      exit 1
    fi
```

### Pre-commit Hooks
```bash
# Install pre-commit
uv run pre-commit install

# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: ci-preflight
      name: CI Preflight
      entry: python3 scripts/ci_preflight.py
      language: system
      pass_filenames: false
```

## 📈 Metrics & Reporting

### Success Metrics
- **Check Pass Rate**: Percentage of successful preflight runs
- **Fix Time**: Average time to resolve preflight failures
- **Notification Delivery**: Success rate of Slack/Email notifications

### Continuous Improvement
- Monitor common failure patterns
- Optimize check execution time
- Refine notification content based on team feedback

## 🚨 Emergency Procedures

### Bypass Preflight Checks
```bash
# Skip all checks (use sparingly!)
git push --no-verify

# Skip specific branch
git push origin feature-branch --no-verify
```

### Disable Notifications Temporarily
```bash
# Unset notification environment variables
unset SLACK_WEBHOOK_URL
unset SMTP_USER

# Or modify the hook to skip notifications
```

### Remove Pre-push Hook
```bash
# Remove the hook completely
rm .git/hooks/pre-push

# Reinstall later
./scripts/setup_ci_preflight_hook.sh
```

## 📚 Best Practices

### Development Workflow
1. **Frequent Commits**: Run preflight on feature branches
2. **Fix Early**: Address issues as they arise
3. **Team Communication**: Use notifications for coordination
4. **Emergency Planning**: Know when and how to bypass checks

### Configuration Management
1. **Environment Variables**: Store in secure, shared location
2. **Documentation**: Keep team informed of configuration changes
3. **Testing**: Validate notification setup regularly
4. **Backup Plans**: Have fallback notification methods

## 🔗 Related Documentation

- [Makefile Commands](Makefile) - Available make targets
- [Notification Scripts](scripts/) - Slack and Email notification implementations
- [CI Preflight Script](scripts/ci_preflight.py) - Core validation logic
- [Git Hooks Setup](scripts/setup_ci_preflight_hook.sh) - Hook installation

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Review troubleshooting section
3. Check notification configuration
4. Contact development team

---

**Last Updated**: December 2024  
**Version**: v0.7.0  
**Maintainer**: Development Team