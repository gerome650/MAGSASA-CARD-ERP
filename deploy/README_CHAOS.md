# Chaos Engineering Command Reference

Quick reference for all chaos engineering commands and options.

## 🚀 Quick Commands

### Test Runner (Recommended)
```bash
# Standard test suite
./deploy/run_chaos_tests.sh

# Dry run (simulation only)
./deploy/run_chaos_tests.sh --dry-run

# Different intensity levels
./deploy/run_chaos_tests.sh --intensity smoke      # Quick test
./deploy/run_chaos_tests.sh --intensity standard   # Balanced test
./deploy/run_chaos_tests.sh --intensity stress     # Heavy test

# Custom target
./deploy/run_chaos_tests.sh --target http://staging.example.com
```

## 🔧 Individual Components

### Chaos Injector
```bash
# Basic usage
python deploy/chaos_injector.py

# With options
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --output deploy/chaos_results.json \
  --verbose

# Dry run (safe simulation)
python deploy/chaos_injector.py --dry-run

# Specific scenario
python deploy/chaos_injector.py --scenario "Heavy Network Delay"
```

**Options:**
- `--config FILE` - Chaos scenarios configuration file
- `--target URL` - Target service URL (default: http://localhost:8000)
- `--scenario NAME` - Run specific scenario by name
- `--output FILE` - Output file for results (default: deploy/chaos_results.json)
- `--dry-run` - Simulate chaos without actual injection
- `--verbose` - Enable verbose logging

### Resilience Validator
```bash
# Basic validation
python deploy/resilience_validator.py

# With chaos results
python deploy/resilience_validator.py \
  --chaos-results deploy/chaos_results.json \
  --fail-on-violation

# Custom options
python deploy/resilience_validator.py \
  --target http://localhost:8000 \
  --config deploy/chaos_scenarios.yml \
  --output deploy/resilience_validation.json \
  --report deploy/chaos_report.md \
  --monitor-duration 60 \
  --baseline-samples 10 \
  --verbose
```

**Options:**
- `--target URL` - Target service URL
- `--config FILE` - Chaos scenarios configuration file
- `--chaos-results FILE` - Chaos injection results file
- `--output FILE` - Output file for validation results
- `--report FILE` - Output file for markdown report
- `--monitor-duration SECONDS` - Duration to monitor during chaos
- `--baseline-samples N` - Number of samples for baseline measurement
- `--fail-on-violation` - Exit with non-zero code if SLOs are violated
- `--verbose` - Enable verbose logging

### Metrics Exporter
```bash
# Export to file
python deploy/chaos_metrics_exporter.py \
  --chaos-results deploy/chaos_results.json \
  --validation-results deploy/resilience_validation.json \
  --output deploy/chaos_metrics.prom

# Push to Prometheus
python deploy/chaos_metrics_exporter.py \
  --push \
  --pushgateway-url http://prometheus:9091 \
  --job-name "magsasa-chaos"
```

**Options:**
- `--chaos-results FILE` - Chaos injection results file
- `--validation-results FILE` - Resilience validation results file
- `--output FILE` - Output file for Prometheus metrics
- `--push` - Push metrics to Prometheus Pushgateway
- `--pushgateway-url URL` - Prometheus Pushgateway URL
- `--job-name NAME` - Job name for Pushgateway
- `--verbose` - Enable verbose logging

## 📊 Scenario Groups

### Available Groups
```bash
# Smoke test (quick validation)
python deploy/chaos_injector.py --scenario-group smoke_test

# Standard test (balanced scenarios)
python deploy/chaos_injector.py --scenario-group standard_test

# Stress test (heavy scenarios)
python deploy/chaos_injector.py --scenario-group stress_test

# Infrastructure test (container/database failures)
python deploy/chaos_injector.py --scenario-group infrastructure_test

# Production readiness (full validation)
python deploy/chaos_injector.py --scenario-group production_readiness
```

### Individual Scenarios
```bash
# CPU stress scenarios
python deploy/chaos_injector.py --scenario "Light CPU Stress"
python deploy/chaos_injector.py --scenario "Medium CPU Stress"
python deploy/chaos_injector.py --scenario "Heavy CPU Stress"

# Memory stress scenarios
python deploy/chaos_injector.py --scenario "Light Memory Stress"
python deploy/chaos_injector.py --scenario "Medium Memory Stress"
python deploy/chaos_injector.py --scenario "Heavy Memory Stress"

# Network scenarios
python deploy/chaos_injector.py --scenario "Light Network Delay"
python deploy/chaos_injector.py --scenario "Heavy Network Delay"
python deploy/chaos_injector.py --scenario "Medium Packet Loss"

# Infrastructure scenarios
python deploy/chaos_injector.py --scenario "Application Container Restart"
python deploy/chaos_injector.py --scenario "Database Brief Outage"
python deploy/chaos_injector.py --scenario "Database Extended Outage"

# Disk stress scenarios
python deploy/chaos_injector.py --scenario "Light Disk Stress"
python deploy/chaos_injector.py --scenario "Medium Disk Stress"
python deploy/chaos_injector.py --scenario "Heavy Disk Stress"
```

## 🎯 SLO Validation Commands

### Check SLO Compliance
```bash
# Validate against current results
python deploy/resilience_validator.py --fail-on-violation

# Generate detailed report
python deploy/resilience_validator.py \
  --report deploy/detailed_report.md \
  --verbose
```

### Export Metrics for Monitoring
```bash
# Export to Prometheus format
python deploy/chaos_metrics_exporter.py --output metrics.prom

# Push to monitoring system
python deploy/chaos_metrics_exporter.py \
  --push \
  --pushgateway-url http://prometheus:9091 \
  --job-name "magsasa-chaos"
```

## 🔍 Validation & Diagnostics

### Suite Validation
```bash
# Validate entire chaos engineering suite
python validate_chaos_suite.py

# Verbose validation
python validate_chaos_suite.py --verbose

# Skip functional tests
python validate_chaos_suite.py --skip-tests
```

### Health Checks
```bash
# Check service health
curl http://localhost:8000/api/health

# Check with timeout
curl --max-time 5 http://localhost:8000/api/health

# Check multiple endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/status
curl http://localhost:8000/api/metrics
```

### Log Analysis
```bash
# View application logs
tail -f app.log

# View chaos injection logs
python deploy/chaos_injector.py --verbose 2>&1 | tee chaos.log

# View validation logs
python deploy/resilience_validator.py --verbose 2>&1 | tee validation.log
```

## 📁 Output Files

### Generated Files
```bash
# Chaos injection results
deploy/chaos_results.json

# Resilience validation results
deploy/resilience_validation.json

# Human-readable report
deploy/chaos_report.md

# Prometheus metrics
deploy/chaos_metrics.prom

# Validation report
deploy/validation_report.md
```

### File Contents
- **chaos_results.json**: Machine-readable chaos test results
- **resilience_validation.json**: SLO validation results
- **chaos_report.md**: Human-readable summary report
- **chaos_metrics.prom**: Prometheus-compatible metrics
- **validation_report.md**: Installation validation report

## 🚨 Troubleshooting Commands

### Common Issues
```bash
# Permission errors
chmod +x deploy/*.py deploy/*.sh

# Missing dependencies
pip install aiohttp pyyaml requests psutil

# Service not responding
curl http://localhost:8000/api/health
lsof -i :8000

# Validation failures
python validate_chaos_suite.py
```

### Debug Mode
```bash
# Enable debug logging
python deploy/chaos_injector.py --verbose
python deploy/resilience_validator.py --verbose
python deploy/chaos_metrics_exporter.py --verbose

# Check system resources
htop
free -h
df -h
```

### Cleanup
```bash
# Clean up temporary files
rm -f /tmp/chaos_*.json
rm -f /tmp/test_*.json
rm -f /tmp/chaos_metrics.prom

# Kill any lingering processes
pkill -f stress-ng
pkill -f chaos_injector
```

## 🔄 CI/CD Integration

### GitHub Actions
```bash
# Trigger workflow manually
gh workflow run chaos.yml

# Check workflow status
gh run list --workflow=chaos.yml

# Download artifacts
gh run download <run-id>
```

### Local CI Simulation
```bash
# Simulate CI/CD pipeline
./deploy/run_chaos_tests.sh --intensity smoke
python deploy/resilience_validator.py --fail-on-violation
python deploy/chaos_metrics_exporter.py --push
```

## 📈 Monitoring Commands

### Prometheus Metrics
```bash
# View exported metrics
cat deploy/chaos_metrics.prom

# Query Prometheus
curl http://prometheus:9090/api/v1/query?query=chaos_scenarios_total

# Check Pushgateway
curl http://prometheus:9091/metrics
```

### Grafana Integration
```bash
# Export metrics for Grafana
python deploy/chaos_metrics_exporter.py --output grafana_metrics.prom

# Import dashboard (if available)
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @chaos_dashboard.json
```

---

## 💡 Tips

1. **Always start with dry-run** to test configuration
2. **Use smoke tests first** before running heavy scenarios
3. **Monitor system resources** during chaos injection
4. **Check logs** if tests fail unexpectedly
5. **Validate installation** with `python validate_chaos_suite.py`
6. **Export metrics regularly** for trend analysis
7. **Run tests during maintenance windows** for production
8. **Keep scenarios realistic** to your environment