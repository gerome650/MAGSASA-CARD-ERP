#!/bin/bash
# 🧪 Test Script for CI-Safe Git Hooks
#
# Usage:
#   ./scripts/hooks/test_hooks.sh

set -e

echo "🧪 Testing CI-Safe Git Hooks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 1: Pre-Commit (Local Mode)
echo "📋 Test 1: Pre-Commit Hook (Local Mode)"
echo "   Should auto-fix issues..."
echo
python3 scripts/hooks/pre_commit.py 2>&1 | head -10
echo
echo "✅ Test 1 Complete"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 2: Pre-Commit (CI Mode)
echo "📋 Test 2: Pre-Commit Hook (CI Mode)"
echo "   Should check-only (no auto-fix)..."
echo
CI=true python3 scripts/hooks/pre_commit.py 2>&1 | head -15
echo
echo "✅ Test 2 Complete"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 3: Post-Push (No Slack)
echo "📋 Test 3: Post-Push Hook (No Slack Webhook)"
echo "   Should exit gracefully..."
echo
PR_AUTHOR="testuser" \
PR_NUMBER="999" \
PR_TITLE="Test PR" \
python3 scripts/hooks/post_push.py 2>&1
echo
echo "✅ Test 3 Complete"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 4: Lint Check
echo "📋 Test 4: Lint Check (Ruff)"
echo "   Should pass for both hooks..."
echo
ruff check scripts/hooks/pre_commit.py scripts/hooks/post_push.py 2>&1
echo
echo "✅ Test 4 Complete"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Summary
echo "🎉 All Tests Completed!"
echo
echo "Next Steps:"
echo "  1. To test with Slack, set SLACK_WEBHOOK_URL:"
echo "     export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/XXX'"
echo
echo "  2. Test post-push with Slack:"
echo "     PR_AUTHOR='your-name' PR_NUMBER='123' PR_TITLE='Test' python3 scripts/hooks/post_push.py"
echo
echo "  3. Install hooks:"
echo "     python3 scripts/hooks/install_hooks.py"
echo


