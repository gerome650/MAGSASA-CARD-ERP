#!/bin/bash
# Chaos Engineering Test Runner
# Quick script to run complete chaos engineering suite

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TARGET_URL="${TARGET_URL:-http://localhost:8000}"
CONFIG_FILE="deploy/chaos_scenarios.yml"
RESULTS_DIR="deploy/chaos_results_$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false
INTENSITY="standard"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET_URL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --intensity)
            INTENSITY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --target URL         Target service URL (default: http://localhost:8000)"
            echo "  --dry-run            Simulate chaos without actual injection"
            echo "  --intensity LEVEL    Test intensity: smoke, standard, stress (default: standard)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Chaos Engineering Test Suite - Stage 6.5        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Target:    ${TARGET_URL}"
echo -e "  Intensity: ${INTENSITY}"
echo -e "  Dry Run:   ${DRY_RUN}"
echo -e "  Results:   ${RESULTS_DIR}"
echo ""

# Function to check if service is healthy and ready
check_service_health() {
    echo -e "${YELLOW}⏳ Checking service health and readiness...${NC}"
    
    # First check basic health
    for i in {1..30}; do
        if curl -f -s "${TARGET_URL}/api/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service health check passed${NC}"
            break
        elif curl -f -s "${TARGET_URL}/api/health/live" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service liveness check passed${NC}"
            break
        fi
        echo -e "  Health check attempt $i/30..."
        sleep 2
    done
    
    # Then check readiness
    for i in {1..15}; do
        if curl -f -s "${TARGET_URL}/api/health/ready" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Service is ready for chaos testing${NC}"
            return 0
        fi
        echo -e "  Readiness check attempt $i/15..."
        sleep 2
    done
    
    echo -e "${RED}❌ Service readiness check failed${NC}"
    return 1
}

# Function to run chaos injection
run_chaos_injection() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Step 1: Chaos Injection${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    CHAOS_ARGS="--config ${CONFIG_FILE} --target ${TARGET_URL} --output ${RESULTS_DIR}/chaos_results.json --verbose"
    
    if [ "$DRY_RUN" = true ]; then
        CHAOS_ARGS="${CHAOS_ARGS} --dry-run"
    fi
    
    if python3 deploy/chaos_injector.py $CHAOS_ARGS; then
        echo -e "${GREEN}✅ Chaos injection completed${NC}"
        return 0
    else
        echo -e "${RED}❌ Chaos injection failed${NC}"
        return 1
    fi
}

# Function to run resilience validation
run_resilience_validation() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Step 2: Resilience Validation${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    if python3 deploy/resilience_validator.py \
        --target "${TARGET_URL}" \
        --config "${CONFIG_FILE}" \
        --chaos-results "${RESULTS_DIR}/chaos_results.json" \
        --output "${RESULTS_DIR}/resilience_validation.json" \
        --report "${RESULTS_DIR}/chaos_report.md" \
        --verbose; then
        echo -e "${GREEN}✅ Resilience validation passed${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Resilience validation completed with violations${NC}"
        return 1
    fi
}

# Function to display summary
display_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Test Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    if [ -f "${RESULTS_DIR}/chaos_report.md" ]; then
        echo -e "${GREEN}📄 Report generated: ${RESULTS_DIR}/chaos_report.md${NC}"
        echo ""
        echo "Quick Summary:"
        head -n 20 "${RESULTS_DIR}/chaos_report.md"
        echo ""
        echo "Full report available at: ${RESULTS_DIR}/chaos_report.md"
    fi
    
    if [ -f "${RESULTS_DIR}/chaos_results.json" ]; then
        echo -e "${GREEN}📊 Results saved: ${RESULTS_DIR}/chaos_results.json${NC}"
    fi
}

# Main execution
main() {
    # Check prerequisites
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    if [ ! -f "${CONFIG_FILE}" ]; then
        echo -e "${RED}❌ Configuration file not found: ${CONFIG_FILE}${NC}"
        exit 1
    fi
    
    # Check service health
    if ! check_service_health; then
        echo -e "${RED}❌ Cannot proceed - service is not healthy${NC}"
        exit 1
    fi
    
    # Run chaos injection
    CHAOS_EXIT_CODE=0
    run_chaos_injection || CHAOS_EXIT_CODE=$?
    
    # Run resilience validation
    VALIDATION_EXIT_CODE=0
    run_resilience_validation || VALIDATION_EXIT_CODE=$?
    
    # Display summary
    display_summary
    
    # Final status
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    if [ $CHAOS_EXIT_CODE -eq 0 ] && [ $VALIDATION_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All chaos engineering tests PASSED${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Chaos engineering tests completed with issues${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Review the following for details:"
        echo "  - ${RESULTS_DIR}/chaos_report.md"
        echo "  - ${RESULTS_DIR}/resilience_validation.json"
        exit 1
    fi
}

# Run main function
main

