#!/bin/bash
# Stage 7.1 Verification Script
# Verifies that all Self-Healing CI Intelligence Agent components are properly installed

echo "🔍 Verifying Stage 7.1: Self-Healing CI Intelligence Agent"
echo "============================================================"
echo ""

ERRORS=0

# Check scripts exist
echo "📂 Checking scripts..."
SCRIPTS=(
    "scripts/analyze_ci_failure.py"
    "scripts/auto_fix_ci_failures.py"
    "scripts/generate_ci_intelligence_report.py"
    "scripts/ci_agent_cli.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  ✅ $script"
    else
        echo "  ❌ $script - MISSING"
        ((ERRORS++))
    fi
done
echo ""

# Check workflows exist
echo "🔄 Checking workflows..."
WORKFLOWS=(
    ".github/workflows/ci.yml"
    ".github/workflows/ci-intelligence-report.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        echo "  ✅ $workflow"
        # Check for Stage 7.1 markers
        if grep -q "Stage 7.1" "$workflow" 2>/dev/null; then
            echo "     ✓ Contains Stage 7.1 enhancements"
        fi
    else
        echo "  ❌ $workflow - MISSING"
        ((ERRORS++))
    fi
done
echo ""

# Check documentation
echo "📚 Checking documentation..."
DOCS=(
    "docs/SELF_HEALING_CI.md"
    "CI_INTELLIGENCE_QUICKSTART.md"
    "STAGE_7.1_COMPLETION_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✅ $doc"
    else
        echo "  ❌ $doc - MISSING"
        ((ERRORS++))
    fi
done
echo ""

# Check directories
echo "📁 Checking directories..."
if [ -d "reports" ]; then
    echo "  ✅ reports/ directory"
else
    echo "  ❌ reports/ directory - MISSING"
    ((ERRORS++))
fi
echo ""

# Test script executability
echo "🔧 Checking script executability..."
for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo "  ✅ $script is executable"
    else
        echo "  ⚠️  $script is not executable (run: chmod +x $script)"
    fi
done
echo ""

# Test Python syntax
echo "🐍 Checking Python syntax..."
for script in "${SCRIPTS[@]}"; do
    if python3 -m py_compile "$script" 2>/dev/null; then
        echo "  ✅ $script - syntax OK"
    else
        echo "  ❌ $script - syntax ERROR"
        ((ERRORS++))
    fi
done
echo ""

# Test imports
echo "📦 Checking dependencies..."
python3 << 'EOF'
import sys
errors = 0

modules = [
    ('sqlite3', 'Built-in'),
    ('argparse', 'Built-in'),
    ('json', 'Built-in'),
    ('re', 'Built-in'),
    ('hashlib', 'Built-in'),
    ('subprocess', 'Built-in'),
    ('datetime', 'Built-in'),
]

optional = [
    ('tabulate', 'Optional (for CLI tables)'),
]

print("  Core dependencies:")
for module, desc in modules:
    try:
        __import__(module)
        print(f"    ✅ {module} - {desc}")
    except ImportError:
        print(f"    ❌ {module} - MISSING ({desc})")
        errors += 1

print("\n  Optional dependencies:")
for module, desc in optional:
    try:
        __import__(module)
        print(f"    ✅ {module} - {desc}")
    except ImportError:
        print(f"    ⚠️  {module} - not installed ({desc})")

sys.exit(errors)
EOF

if [ $? -ne 0 ]; then
    ((ERRORS++))
fi
echo ""

# Test CLI
echo "🎯 Testing CLI..."
if python3 scripts/ci_agent_cli.py --help > /dev/null 2>&1; then
    echo "  ✅ CLI runs successfully"
else
    echo "  ❌ CLI failed to run"
    ((ERRORS++))
fi
echo ""

# Summary
echo "============================================================"
if [ $ERRORS -eq 0 ]; then
    echo "✅ All verification checks passed!"
    echo ""
    echo "🎉 Stage 7.1 is fully operational!"
    echo ""
    echo "Quick start:"
    echo "  python scripts/ci_agent_cli.py --stats"
    echo "  python scripts/ci_agent_cli.py --show-trends"
    echo ""
    echo "Documentation:"
    echo "  📖 Quick Start: CI_INTELLIGENCE_QUICKSTART.md"
    echo "  📚 Full Docs: docs/SELF_HEALING_CI.md"
    exit 0
else
    echo "❌ Verification failed with $ERRORS error(s)"
    echo ""
    echo "Please review the errors above and fix any issues."
    exit 1
fi

