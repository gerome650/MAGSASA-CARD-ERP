#!/bin/bash

# MCP Setup Validation Script
# Validates that Step 2 MCP Simulation is correctly implemented

set -e

echo "🧠 AgSense MCP Setup Validation"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track status
ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        return 0
    else
        echo -e "${RED}❌${NC} $1 (missing)"
        ((ERRORS++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        return 0
    else
        echo -e "${RED}❌${NC} $1 (missing)"
        ((ERRORS++))
        return 1
    fi
}

echo "📁 Checking Directory Structure"
echo "--------------------------------"
check_dir "packages/core/src/core/adapters"
check_dir "packages/agent-ingest/adapters"
check_dir "packages/agent-retrieval/adapters"
check_dir "packages/agent-scoring/adapters"
check_dir "packages/agent-notify/adapters"
check_dir "packages/agent-billing/adapters"
check_dir ".github/workflows"
check_dir "tests"
echo ""

echo "📄 Checking Core Files"
echo "----------------------"
check_file "packages/core/src/core/adapters/__init__.py"
check_file "packages/core/src/core/adapters/mcp_base.py"
check_file "packages/core/src/core/models/contracts.py"
echo ""

echo "🔌 Checking MCP Stub Adapters"
echo "-----------------------------"
check_file "packages/agent-ingest/adapters/mcp_stub.py"
check_file "packages/agent-retrieval/adapters/mcp_stub.py"
check_file "packages/agent-scoring/adapters/mcp_stub.py"
check_file "packages/agent-notify/adapters/mcp_stub.py"
check_file "packages/agent-billing/adapters/mcp_stub.py"
echo ""

echo "🛠️  Checking CLI & Build Tools"
echo "------------------------------"
check_file "packages/cli/src/ags/app.py"
check_file "Makefile"
check_file ".pre-commit-config.yaml"
check_file "pyproject.toml"
echo ""

echo "🤖 Checking CI/CD Workflows"
echo "---------------------------"
check_file ".github/workflows/mcp-validation.yml"
check_file ".github/workflows/ci.yml"
echo ""

echo "📚 Checking Documentation"
echo "-------------------------"
check_file "README.md"
check_file "MCP_QUICK_START.md"
check_file "STEP_2_MCP_SIMULATION_COMPLETE.md"
check_file "STEP_2_EXECUTIVE_SUMMARY.md"
echo ""

echo "🧪 Checking Test Files"
echo "----------------------"
check_file "tests/test_mcp_adapters.py"
echo ""

echo "🔍 Checking Python Environment"
echo "------------------------------"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅${NC} Python $PYTHON_VERSION"
    
    # Check version is 3.10+
    if [[ $(python3 -c "import sys; print(sys.version_info >= (3, 10))") == "True" ]]; then
        echo -e "${GREEN}✅${NC} Python version >= 3.10"
    else
        echo -e "${RED}❌${NC} Python version < 3.10 (3.10+ required)"
        ((ERRORS++))
    fi
else
    echo -e "${RED}❌${NC} Python 3 not found"
    ((ERRORS++))
fi
echo ""

echo "📦 Checking uv Package Manager"
echo "------------------------------"
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version | cut -d' ' -f2)
    echo -e "${GREEN}✅${NC} uv $UV_VERSION"
else
    echo -e "${RED}❌${NC} uv not found"
    echo "   Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    ((ERRORS++))
fi
echo ""

echo "🌍 Checking Environment Variables"
echo "---------------------------------"
if [ -n "$AGS_MCP_ENABLED" ]; then
    if [ "$AGS_MCP_ENABLED" = "true" ] || [ "$AGS_MCP_ENABLED" = "1" ]; then
        echo -e "${GREEN}✅${NC} AGS_MCP_ENABLED=true"
    else
        echo -e "${YELLOW}⚠️${NC}  AGS_MCP_ENABLED=$AGS_MCP_ENABLED (not enabled)"
        echo "   Run: export AGS_MCP_ENABLED=true"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠️${NC}  AGS_MCP_ENABLED not set"
    echo "   Run: export AGS_MCP_ENABLED=true"
    ((WARNINGS++))
fi
echo ""

echo "🧪 Running Functional Tests"
echo "---------------------------"

# Test 1: Check if ags command exists
if command -v ags &> /dev/null; then
    echo -e "${GREEN}✅${NC} ags CLI command available"
    
    # Test 2: Run ags --version
    if ags --version &> /dev/null; then
        echo -e "${GREEN}✅${NC} ags --version works"
    else
        echo -e "${RED}❌${NC} ags --version failed"
        ((ERRORS++))
    fi
    
    # Test 3: Run ags mcp-check (if MCP enabled)
    if [ "$AGS_MCP_ENABLED" = "true" ] || [ "$AGS_MCP_ENABLED" = "1" ]; then
        echo -n "Running ags mcp-check... "
        if ags mcp-check &> /tmp/mcp-check-output.txt; then
            echo -e "${GREEN}✅${NC}"
            # Check if all agents are ready
            if grep -q "All .* agents are fully MCP-ready" /tmp/mcp-check-output.txt; then
                echo -e "${GREEN}✅${NC} All agents MCP-ready"
            else
                echo -e "${YELLOW}⚠️${NC}  Some agents may not be MCP-ready"
                ((WARNINGS++))
            fi
        else
            echo -e "${RED}❌${NC}"
            echo "Output saved to /tmp/mcp-check-output.txt"
            ((ERRORS++))
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  Skipping ags mcp-check (MCP not enabled)"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}❌${NC} ags command not found"
    echo "   Run: make setup"
    ((ERRORS++))
fi
echo ""

# Summary
echo "================================"
echo "📊 Validation Summary"
echo "================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: export AGS_MCP_ENABLED=true"
    echo "  2. Run: ags mcp-check"
    echo "  3. Run: ags agent run all --trace"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Validation passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Address warnings above for full functionality."
    echo ""
    exit 0
else
    echo -e "${RED}❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix errors above before proceeding."
    echo ""
    echo "Quick fix:"
    echo "  1. Run: make setup"
    echo "  2. Run: $0 (this script again)"
    echo ""
    exit 1
fi

