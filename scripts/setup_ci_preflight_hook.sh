#!/bin/bash
# Setup pre-push hook for CI Preflight Validation

echo "🔧 Setting up pre-push hook for CI Preflight Validation..."

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create the pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook for CI Preflight Validation

echo "🚀 Running CI preflight before push..."
echo "=========================================="

# Get current branch and commit info
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_SHA=$(git rev-parse HEAD)

echo "📋 Branch: $BRANCH"
echo "📋 Commit: ${COMMIT_SHA:0:8}"
echo ""

# Skip checks for main and release branches (optional)
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" || "$BRANCH" == release/* ]]; then
    echo "⚠️  Skipping preflight checks for $BRANCH branch"
    echo "✅ Proceeding with push..."
    exit 0
fi

# Run CI preflight
python3 scripts/ci_preflight.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Preflight failed. Push aborted."
    echo ""
    echo "💡 To fix issues:"
    echo "   • Review the failed checks above"
    echo "   • Run: make ci-preflight"
    echo "   • Fix the issues and try again"
    echo ""
    echo "🚨 Emergency bypass (NOT RECOMMENDED):"
    echo "   git push --no-verify"
    echo ""
    
    # Send notifications about the failure
    python3 scripts/notify_slack.py "$BRANCH" "$COMMIT_SHA" "Preflight validation failed" || true
    python3 scripts/notify_email.py "$BRANCH" "$COMMIT_SHA" "Preflight validation failed" || true
    
    exit 1
fi

echo ""
echo "✅ All preflight checks passed. Proceeding with push."
echo "🎉 Your code is CI-ready!"

# Send success notification (optional)
if [[ "$BRANCH" != "main" && "$BRANCH" != "master" ]]; then
    python3 scripts/notify_slack.py "$BRANCH" "$COMMIT_SHA" "Preflight validation passed" || true
fi

exit 0
EOF

# Make the hook executable
chmod +x .git/hooks/pre-push

echo "✅ CI preflight hook installed successfully!"
echo ""
echo "The hook will now run automatically before every push."
echo ""
echo "Features:"
echo "  • Runs full CI preflight validation"
echo "  • Sends Slack/Email notifications on failure"
echo "  • Skips checks for main/release branches"
echo "  • Emergency bypass: git push --no-verify"
echo ""
echo "To remove: rm .git/hooks/pre-push"
