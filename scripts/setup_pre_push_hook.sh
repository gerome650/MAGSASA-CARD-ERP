#!/bin/bash
# Setup pre-push hook for Stage Readiness Verification

echo "🔧 Setting up pre-push hook for Stage Readiness Verification..."

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create the pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook for Stage Readiness Verification

echo "🧩 Running Stage Readiness Verification..."

# Run the verification script
python3 scripts/verify_stage_readiness.py --ci

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Stage readiness check failed!"
    echo "Please fix the issues above before pushing."
    echo ""
    echo "To bypass this check (NOT RECOMMENDED):"
    echo "  git push --no-verify"
    echo ""
    exit 1
fi

echo "✅ Stage readiness check passed. Safe to push!"
EOF

# Make the hook executable
chmod +x .git/hooks/pre-push

echo "✅ Pre-push hook installed successfully!"
echo ""
echo "The hook will now run automatically before every push."
echo "To disable it temporarily: git push --no-verify"
echo "To remove it: rm .git/hooks/pre-push"
