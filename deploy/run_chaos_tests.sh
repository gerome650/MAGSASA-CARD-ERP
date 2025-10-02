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
CONFIG_FILE="deploy/chaos_scenarios.yml"
RESULTS_DIR="deploy/chaos_results_$(date +%Y%m%d_%H%M%S)"
DRY_RUN=false
INTENSITY="standard"
AUTO_DETECT_PORT=true
FALLBACK_PORT=8000

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET_URL="$2"
            AUTO_DETECT_PORT=false
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
        --no-auto-detect)
            AUTO_DETECT_PORT=false
            shift
            ;;
        --fallback-port)
            FALLBACK_PORT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --target URL         Target service URL (disables auto-detection)"
            echo "  --dry-run            Simulate chaos without actual injection"
            echo "  --intensity LEVEL    Test intensity: smoke, standard, stress (default: standard)"
            echo "  --no-auto-detect     Disable automatic port detection"
            echo "  --fallback-port PORT Fallback port if auto-detection fails (default: 8000)"
            echo "  --help               Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  APP_PORT             Set Flask application port"
            echo "  CHAOS_TARGET_PORT    Override target port for chaos testing"
            echo "  TARGET_URL           Override target URL (same as --target)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Auto-detect target URL if not provided
if [ "$AUTO_DETECT_PORT" = true ] && [ -z "$TARGET_URL" ]; then
    echo -e "${YELLOW}🔍 Auto-detecting Flask service port...${NC}"
    
    # Check for environment variable override
    if [ -n "$CHAOS_TARGET_PORT" ]; then
        TARGET_URL="http://localhost:${CHAOS_TARGET_PORT}"
        echo -e "${GREEN}   Using CHAOS_TARGET_PORT: ${TARGET_URL}${NC}"
    elif [ -n "$TARGET_URL" ]; then
        echo -e "${GREEN}   Using TARGET_URL: ${TARGET_URL}${NC}"
    else
        # Use port detector
        if [ -f "deploy/port_detector.py" ]; then
            DETECTED_URL=$(python3 deploy/port_detector.py --fallback-port "$FALLBACK_PORT" --url-only --quiet 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "$DETECTED_URL" ]; then
                TARGET_URL="$DETECTED_URL"
                echo -e "${GREEN}   ✅ Auto-detected: ${TARGET_URL}${NC}"
            else
                TARGET_URL="http://localhost:${FALLBACK_PORT}"
                echo -e "${YELLOW}   ⚠️  Using fallback: ${TARGET_URL}${NC}"
            fi
        else
            TARGET_URL="http://localhost:${FALLBACK_PORT}"
            echo -e "${YELLOW}   ⚠️  Port detector not found, using fallback: ${TARGET_URL}${NC}"
        fi
    fi
else
    # Use provided target or fallback
    if [ -z "$TARGET_URL" ]; then
        TARGET_URL="http://localhost:${FALLBACK_PORT}"
    fi
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Chaos Engineering Test Suite - Stage 6.5        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Target:       ${TARGET_URL}"
echo -e "  Auto-detect:  ${AUTO_DETECT_PORT}"
echo -e "  Intensity:    ${INTENSITY}"
echo -e "  Dry Run:      ${DRY_RUN}"
echo -e "  Results:      ${RESULTS_DIR}"
echo ""

# Function to check if service is healthy
check_service_health() {
    echo -e "${YELLOW}⏳ Checking service health at ${TARGET_URL}/api/health...${NC}"
    
    # Extract port from TARGET_URL for diagnostics
    TARGET_PORT=$(echo "$TARGET_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
    
    for i in {1..10}; do
        # Try health check
        HEALTH_RESPONSE=$(curl -f -s "${TARGET_URL}/api/health" 2>&1)
        CURL_EXIT_CODE=$?
        
        if [ $CURL_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}✅ Service is healthy${NC}"
            
            # Show service info if available
            if echo "$HEALTH_RESPONSE" | grep -q "service"; then
                SERVICE_NAME=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('service', 'Unknown'))" 2>/dev/null || echo "Unknown")
                echo -e "${GREEN}   Service: ${SERVICE_NAME}${NC}"
            fi
            return 0
        fi
        
        echo -e "  Attempt $i/10 failed..."
        
        # Provide helpful diagnostics on last attempt
        if [ $i -eq 10 ]; then
            echo ""
            echo -e "${RED}❌ Service health check failed after 10 attempts${NC}"
            echo -e "${YELLOW}Diagnostic Information:${NC}"
            
            # Check if port is open
            if command -v nc >/dev/null 2>&1; then
                if nc -z localhost "$TARGET_PORT" 2>/dev/null; then
                    echo -e "  ✅ Port ${TARGET_PORT} is open"
                    echo -e "  ❌ But /api/health endpoint is not responding correctly"
                    echo -e "     This might indicate:"
                    echo -e "     - Flask app is running but health endpoint is missing"
                    echo -e "     - Flask app is not fully initialized"
                    echo -e "     - Different service running on this port"
                else
                    echo -e "  ❌ Port ${TARGET_PORT} is not open"
                    echo -e "     This might indicate:"
                    echo -e "     - Flask app is not running"
                    echo -e "     - Flask app is running on a different port"
                    echo -e "     - Firewall blocking the connection"
                fi
            fi
            
            # Show what's running on common ports
            echo -e "  ${YELLOW}Checking common Flask ports:${NC}"
            for port in 8000 5000 5001 3000; do
                if command -v nc >/dev/null 2>&1 && nc -z localhost "$port" 2>/dev/null; then
                    echo -e "    Port ${port}: ✅ Open"
                    # Try to get service info
                    SERVICE_INFO=$(curl -s "http://localhost:${port}/api/health" 2>/dev/null | head -c 100)
                    if [ -n "$SERVICE_INFO" ]; then
                        echo -e "      Response: ${SERVICE_INFO}..."
                    fi
                else
                    echo -e "    Port ${port}: ❌ Closed"
                fi
            done
            
            echo ""
            echo -e "${YELLOW}Troubleshooting Steps:${NC}"
            echo -e "  1. Verify Flask app is running:"
            echo -e "     cd src && python main.py"
            echo -e "  2. Check if running on different port:"
            echo -e "     python3 deploy/port_detector.py"
            echo -e "  3. Set correct port manually:"
            echo -e "     export APP_PORT=5001  # or your actual port"
            echo -e "     ./deploy/run_chaos_tests.sh"
            echo -e "  4. Override target URL:"
            echo -e "     ./deploy/run_chaos_tests.sh --target http://localhost:5001"
            echo ""
        fi
        
        sleep 2
    done
    
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

