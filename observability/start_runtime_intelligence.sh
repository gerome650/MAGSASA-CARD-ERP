#!/bin/bash
# Runtime Intelligence Startup Script
# Stage 6.8 - Production startup script for runtime intelligence system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_ROOT/venv"

# Default values
WEBHOOK_HOST=${WEBHOOK_HOST:-"0.0.0.0"}
WEBHOOK_PORT=${WEBHOOK_PORT:-"5001"}
PROMETHEUS_URL=${PROMETHEUS_URL:-"http://localhost:9090"}
ALERTMANAGER_URL=${ALERTMANAGER_URL:-"http://localhost:9093"}
GRAFANA_URL=${GRAFANA_URL:-"http://localhost:3000"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🧩 RUNTIME INTELLIGENCE SYSTEM               ║"
    echo "║              Stage 6.8 - Anomaly Detection + Alert Routing  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    print_status "Virtual environment activated"
    
    # Install/update dependencies
    print_status "Installing runtime intelligence dependencies..."
    pip install -q -r "$SCRIPT_DIR/observability_requirements.txt"
}

check_services() {
    print_status "Checking external services..."
    
    # Check Prometheus
    if curl -s "$PROMETHEUS_URL/api/v1/query?query=up" > /dev/null 2>&1; then
        print_status "✓ Prometheus is accessible at $PROMETHEUS_URL"
    else
        print_warning "⚠ Prometheus not accessible at $PROMETHEUS_URL (will use mock data)"
    fi
    
    # Check Alertmanager
    if curl -s "$ALERTMANAGER_URL/api/v1/status" > /dev/null 2>&1; then
        print_status "✓ Alertmanager is accessible at $ALERTMANAGER_URL"
    else
        print_warning "⚠ Alertmanager not accessible at $ALERTMANAGER_URL"
    fi
    
    # Check Grafana
    if curl -s "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        print_status "✓ Grafana is accessible at $GRAFANA_URL"
    else
        print_warning "⚠ Grafana not accessible at $GRAFANA_URL (annotations will be disabled)"
    fi
}

validate_configuration() {
    print_status "Validating configuration..."
    
    # Check alert rules
    if [ -f "$SCRIPT_DIR/alerts/promql_rules.yml" ]; then
        print_status "✓ Alert rules file found"
        
        # Run validation if script is available
        if [ -f "$PROJECT_ROOT/scripts/validate_alert_rules.py" ]; then
            print_status "Validating alert rules..."
            python "$PROJECT_ROOT/scripts/validate_alert_rules.py" "$SCRIPT_DIR/alerts/promql_rules.yml" || {
                print_warning "Alert rules validation failed, but continuing..."
            }
        fi
    else
        print_error "Alert rules file not found: $SCRIPT_DIR/alerts/promql_rules.yml"
        exit 1
    fi
    
    # Check webhook server
    if [ -f "$SCRIPT_DIR/alerts/webhook_server.py" ]; then
        print_status "✓ Webhook server found"
    else
        print_error "Webhook server not found: $SCRIPT_DIR/alerts/webhook_server.py"
        exit 1
    fi
}

setup_environment() {
    print_status "Setting up environment variables..."
    
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export PROMETHEUS_URL="$PROMETHEUS_URL"
    export ALERTMANAGER_URL="$ALERTMANAGER_URL"
    export GRAFANA_URL="$GRAFANA_URL"
    export WEBHOOK_HOST="$WEBHOOK_HOST"
    export WEBHOOK_PORT="$WEBHOOK_PORT"
    export LOG_LEVEL="$LOG_LEVEL"
    
    # Optional notification channels
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        export SLACK_ENABLED="true"
        print_status "✓ Slack notifications enabled"
    fi
    
    if [ -n "$PAGERDUTY_INTEGRATION_KEY" ]; then
        export PAGERDUTY_ENABLED="true"
        print_status "✓ PagerDuty notifications enabled"
    fi
    
    if [ -n "$GRAFANA_API_KEY" ]; then
        print_status "✓ Grafana annotations enabled"
    else
        print_warning "GRAFANA_API_KEY not set - annotations will be disabled"
    fi
}

start_webhook_server() {
    print_status "Starting Runtime Intelligence Webhook Server..."
    print_status "Host: $WEBHOOK_HOST"
    print_status "Port: $WEBHOOK_PORT"
    print_status "Log Level: $LOG_LEVEL"
    
    # Change to observability directory
    cd "$SCRIPT_DIR"
    
    # Start the webhook server
    python -m alerts.webhook_server \
        --host "$WEBHOOK_HOST" \
        --port "$WEBHOOK_PORT" \
        --log-level "$LOG_LEVEL"
}

run_tests() {
    print_status "Running runtime intelligence tests..."
    
    if [ -f "$SCRIPT_DIR/test_runtime_intelligence.py" ]; then
        python "$SCRIPT_DIR/test_runtime_intelligence.py" \
            --prometheus-url "$PROMETHEUS_URL" \
            --alertmanager-url "$ALERTMANAGER_URL" \
            --grafana-url "$GRAFANA_URL" \
            --webhook-url "http://$WEBHOOK_HOST:$WEBHOOK_PORT"
    else
        print_warning "Test script not found, skipping tests"
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS] [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the runtime intelligence system (default)"
    echo "  test      Run the test suite"
    echo "  validate  Validate alert rules only"
    echo "  help      Show this help message"
    echo ""
    echo "Options:"
    echo "  --host HOST           Webhook server host (default: 0.0.0.0)"
    echo "  --port PORT           Webhook server port (default: 5001)"
    echo "  --prometheus-url URL  Prometheus URL (default: http://localhost:9090)"
    echo "  --grafana-url URL     Grafana URL (default: http://localhost:3000)"
    echo "  --log-level LEVEL     Log level (default: INFO)"
    echo "  --no-deps             Skip dependency installation"
    echo "  --no-checks           Skip service connectivity checks"
    echo ""
    echo "Environment Variables:"
    echo "  SLACK_WEBHOOK_URL         Slack webhook URL for notifications"
    echo "  PAGERDUTY_INTEGRATION_KEY PagerDuty integration key"
    echo "  GRAFANA_API_KEY           Grafana API key for annotations"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 test --prometheus-url http://prometheus:9090"
    echo "  SLACK_WEBHOOK_URL=https://hooks.slack.com/... $0 start"
}

# Parse command line arguments
COMMAND="start"
SKIP_DEPS=false
SKIP_CHECKS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        start|test|validate|help)
            COMMAND="$1"
            shift
            ;;
        --host)
            WEBHOOK_HOST="$2"
            shift 2
            ;;
        --port)
            WEBHOOK_PORT="$2"
            shift 2
            ;;
        --prometheus-url)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        --grafana-url)
            GRAFANA_URL="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --no-deps)
            SKIP_DEPS=true
            shift
            ;;
        --no-checks)
            SKIP_CHECKS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    case $COMMAND in
        start)
            if [ "$SKIP_DEPS" = false ]; then
                check_dependencies
            fi
            
            if [ "$SKIP_CHECKS" = false ]; then
                check_services
                validate_configuration
            fi
            
            setup_environment
            start_webhook_server
            ;;
        test)
            if [ "$SKIP_DEPS" = false ]; then
                check_dependencies
            fi
            
            setup_environment
            run_tests
            ;;
        validate)
            check_dependencies
            validate_configuration
            print_status "✓ Configuration validation completed"
            ;;
        help)
            show_usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Handle signals
trap 'print_status "Shutting down runtime intelligence system..."; exit 0' INT TERM

# Run main function
main "$@"
