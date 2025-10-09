#!/bin/bash
# 🧪 Quick Verification Script
# Verifies that development environment is properly configured

set -e

echo "🧪 Development Environment Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 1: Virtual Environment
echo "📋 Test 1: Virtual Environment"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "   ✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "   ⚠️  Virtual environment not active"
    echo "      Run: source .venv/bin/activate"
fi
echo

# Test 2: Python Version
echo "📋 Test 2: Python Version"
python_version=$(python3 --version 2>&1)
echo "   ✅ $python_version"
echo

# Test 3: Critical Dependencies
echo "📋 Test 3: Critical Dependencies"
critical_deps=("aiohttp" "pytest" "ruff" "black" "yaml")

all_present=true
for dep in "${critical_deps[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo "   ✅ $dep"
    else
        echo "   ❌ $dep - NOT FOUND"
        all_present=false
    fi
done
echo

# Test 4: Make Commands
echo "📋 Test 4: Make Commands Available"
make_commands=("install-dev" "check-deps" "test" "lint" "verify-all")

for cmd in "${make_commands[@]}"; do
    if make -n $cmd &>/dev/null; then
        echo "   ✅ make $cmd"
    else
        echo "   ❌ make $cmd - NOT FOUND"
    fi
done
echo

# Test 5: Files Exist
echo "📋 Test 5: Required Files"
required_files=(
    "requirements-dev.txt"
    "pyproject.toml"
    "scripts/setup/install_dev_dependencies.py"
    "DEV_DEPENDENCIES_SETUP_GUIDE.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - MISSING"
    fi
done
echo

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$all_present" = true ] && [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ All checks passed! Environment is ready."
    echo
    echo "🚀 Next steps:"
    echo "   make test           # Run tests"
    echo "   make verify-all     # Full verification"
    exit 0
else
    echo "⚠️  Some issues detected. Please fix:"
    echo
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "   1. Activate virtual environment:"
        echo "      source .venv/bin/activate"
    fi
    if [ "$all_present" = false ]; then
        echo "   2. Install dependencies:"
        echo "      make install-dev"
    fi
    echo
    exit 1
fi


