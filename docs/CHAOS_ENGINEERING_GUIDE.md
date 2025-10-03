# Chaos Engineering Guide - MAGSASA-CARD-ERP

## Overview

This guide provides comprehensive documentation for the Chaos Engineering & Fault Injection Automation suite implemented in Stage 6.5. The system automatically injects failure scenarios, validates SLO compliance, exports metrics, and fails CI/CD pipelines on violations to ensure production-grade resilience.

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [SLO Validation](#slo-validation)
7. [CI/CD Integration](#cicd-integration)
8. [Monitoring & Metrics](#monitoring--metrics)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Introduction

Chaos Engineering is the practice of deliberately introducing failures and faults into a system to test its resilience and ability to recover. This implementation provides:

- **7 Failure Types**: CPU exhaustion, memory leaks, network delays, packet loss, container crashes, database failures, and disk stress
- **3 Intensity Levels**: Light, medium, and heavy scenarios
- **5 SLO Metrics**: MTTR, error rate, availability, latency degradation, and recovery time
- **Automated Validation**: CI/CD pipeline integration with automatic failure on SLO violations
- **Comprehensive Reporting**: Markdown and JSON reports with detailed metrics

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chaos         │    │   Resilience     │    │   Metrics       │
│   Injector      │───▶│   Validator      │───▶│   Exporter      │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scenarios     │    │   SLO            │    │   Prometheus    │
│   Config        │    │   Validation     │    │   Metrics       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Chaos Injector (`deploy/chaos_injector.py`)

The main chaos injection engine that simulates various failure scenarios.

**Features:**
- 7 different failure types
- 3 intensity levels (light, medium, heavy)
- Graceful cleanup and signal handling
- Dry-run mode for testing
- Comprehensive logging

**Usage:**
```bash
# Run all scenarios
python deploy/chaos_injector.py --config deploy/chaos_scenarios.yml

# Dry run (simulation only)
python deploy/chaos_injector.py --dry-run

# Run specific scenario
python deploy/chaos_injector.py --scenario "Heavy Network Delay"
```

### 2. Resilience Validator (`deploy/resilience_validator.py`)

Validates system resilience against SLO targets during and after chaos injection.

**Features:**
- 5 SLO metrics validation
- Baseline and post-chaos latency measurement
- Recovery time calculation
- Availability monitoring
- Violation detection and reporting

**Usage:**
```bash
# Validate against chaos results
python deploy/resilience_validator.py --chaos-results deploy/chaos_results.json

# Fail on SLO violations
python deploy/resilience_validator.py --fail-on-violation
```

### 3. Metrics Exporter (`deploy/chaos_metrics_exporter.py`)

Exports chaos engineering metrics to Prometheus format for monitoring.

**Features:**
- Prometheus-compatible metrics
- Pushgateway support
- Comprehensive metric coverage
- Historical data retention

**Usage:**
```bash
# Export to file
python deploy/chaos_metrics_exporter.py --output deploy/chaos_metrics.prom

# Push to Prometheus
python deploy/chaos_metrics_exporter.py --push --pushgateway-url http://prometheus:9091
```

### 4. Test Runner (`deploy/run_chaos_tests.sh`)

One-command automation script for running the complete chaos engineering suite.

**Features:**
- Automated test execution
- Health checks
- Result summarization
- Error handling

**Usage:**
```bash
# Standard test
./deploy/run_chaos_tests.sh

# Dry run
./deploy/run_chaos_tests.sh --dry-run

# Different intensity
./deploy/run_chaos_tests.sh --intensity stress
```

## Configuration

### Chaos Scenarios (`deploy/chaos_scenarios.yml`)

The main configuration file defining chaos scenarios and SLO targets.

```yaml
# SLO Targets
slo_targets:
  mttr_seconds: 30
  max_error_rate_percent: 5.0
  min_availability_percent: 95.0
  max_latency_degradation_ms: 500

# Chaos Scenarios
scenarios:
  - name: "Light CPU Stress"
    type: "cpu_exhaust"
    intensity: "light"
    duration: 30
    description: "Moderate CPU load to test graceful degradation"
```

### Scenario Groups

Predefined groups for different testing levels:

- **smoke_test**: Quick validation with light scenarios
- **standard_test**: Balanced test suite for regular validation
- **stress_test**: Heavy scenarios for production readiness
- **infrastructure_test**: Infrastructure failure scenarios
- **production_readiness**: Full production validation

### Environment-Specific SLOs

Different SLO targets for different environments:

```yaml
environments:
  development:
    slo_targets:
      mttr_seconds: 60
      max_error_rate_percent: 10.0
  
  production:
    slo_targets:
      mttr_seconds: 30
      max_error_rate_percent: 1.0
```

## Usage

### Basic Usage

1. **Start your application**:
   ```bash
   cd src
   python main.py
   ```

2. **Run chaos tests**:
   ```bash
   ./deploy/run_chaos_tests.sh
   ```

3. **Review results**:
   ```bash
   cat deploy/chaos_report.md
   ```

### Advanced Usage

#### Custom Scenarios

Create custom scenarios by editing `deploy/chaos_scenarios.yml`:

```yaml
scenarios:
  - name: "Custom Network Chaos"
    type: "network_delay"
    intensity: "heavy"
    duration: 120
    parameters:
      delay_ms: 1000
      interface: "eth0"
```

#### Integration Testing

Run chaos tests as part of your testing pipeline:

```bash
# In your test script
python deploy/chaos_injector.py --dry-run
python deploy/resilience_validator.py --fail-on-violation
```

#### Monitoring Integration

Export metrics to your monitoring stack:

```bash
python deploy/chaos_metrics_exporter.py --push \
  --pushgateway-url http://prometheus:9091 \
  --job-name "magsasa-chaos"
```

## SLO Validation

### Supported SLO Metrics

1. **Mean Time To Recovery (MTTR)**
   - Target: ≤ 30 seconds
   - Measures how quickly the system recovers from failures

2. **Error Rate**
   - Target: ≤ 5% during chaos
   - Measures system stability under stress

3. **Availability**
   - Target: ≥ 95% during chaos
   - Measures system uptime during failures

4. **Latency Degradation**
   - Target: ≤ 500ms increase
   - Measures performance impact of failures

5. **Recovery Time**
   - Target: ≤ 10 seconds
   - Measures time to return to normal operation

### Validation Process

1. **Baseline Measurement**: Measure normal system performance
2. **Chaos Injection**: Inject failures while monitoring
3. **Recovery Validation**: Verify system returns to normal
4. **SLO Compliance**: Check all metrics against targets
5. **Reporting**: Generate detailed reports

## CI/CD Integration

### GitHub Actions Workflow

The system includes a comprehensive GitHub Actions workflow (`.github/workflows/chaos.yml`) that:

- Runs on pull requests and scheduled intervals
- Supports manual triggers with custom parameters
- Validates all chaos scenarios
- Enforces SLO compliance
- Generates detailed reports
- Comments on pull requests with results

### Workflow Triggers

```yaml
on:
  pull_request:
    branches: [main, develop]
  workflow_dispatch:  # Manual trigger
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM UTC
```

### Pipeline Integration

To integrate with your existing pipeline:

1. **Add chaos tests to your workflow**:
   ```yaml
   - name: Chaos Engineering Tests
     uses: ./.github/workflows/chaos.yml
   ```

2. **Fail on SLO violations**:
   ```yaml
   - name: Validate SLOs
     run: python deploy/resilience_validator.py --fail-on-violation
   ```

## Monitoring & Metrics

### Prometheus Metrics

The system exports comprehensive Prometheus metrics:

```
# Scenario execution metrics
chaos_scenarios_total 19
chaos_scenarios_successful 17
chaos_scenarios_failed 2

# SLO compliance metrics
chaos_mttr_seconds 25.5
chaos_error_rate_percent 3.2
chaos_availability_percent 97.8

# Recovery metrics
chaos_recovery_time_seconds 8.2
chaos_latency_degradation_ms 150.5
```

### Grafana Dashboards

Create dashboards using the exported metrics:

- **Chaos Engineering Overview**: High-level metrics and trends
- **SLO Compliance**: SLO targets vs. actual performance
- **Recovery Analysis**: Recovery times and patterns
- **Failure Impact**: Impact of different failure types

### Alerting Rules

Set up alerts for SLO violations:

```yaml
groups:
  - name: chaos_engineering
    rules:
      - alert: SLOViolation
        expr: chaos_slo_passed == 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Chaos engineering SLO violation detected"
```

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Make scripts executable
chmod +x deploy/*.py deploy/*.sh
```

#### 2. Missing Dependencies
```bash
# Install required packages
pip install aiohttp pyyaml requests psutil
```

#### 3. Service Not Responding
```bash
# Check service health
curl http://localhost:8000/api/health
```

#### 4. Dry Run Failures
```bash
# Run validation
python validate_chaos_suite.py
```

### Debug Mode

Enable verbose logging:

```bash
python deploy/chaos_injector.py --verbose
python deploy/resilience_validator.py --verbose
```

### Log Files

Check log files for detailed information:

- Application logs: `app.log`
- Chaos results: `deploy/chaos_results.json`
- Validation results: `deploy/resilience_validation.json`

## Best Practices

### 1. Start Small

Begin with light intensity scenarios and gradually increase:

```bash
# Start with smoke tests
./deploy/run_chaos_tests.sh --intensity smoke

# Progress to standard tests
./deploy/run_chaos_tests.sh --intensity standard
```

### 2. Regular Testing

Run chaos tests regularly:

- **Development**: After each major change
- **Staging**: Before each release
- **Production**: Weekly during maintenance windows

### 3. Monitor Trends

Track metrics over time to identify patterns:

- Recovery times getting longer?
- Error rates increasing?
- Availability declining?

### 4. Team Training

Ensure your team understands:

- What chaos engineering is
- How to interpret results
- When to act on violations
- How to improve resilience

### 5. Continuous Improvement

Use results to improve system resilience:

- Fix identified weaknesses
- Adjust SLO targets
- Add new scenarios
- Improve monitoring

## Conclusion

This chaos engineering suite provides comprehensive fault injection and resilience validation for the MAGSASA-CARD-ERP system. By following this guide and best practices, you can ensure your system is production-ready and resilient to failures.

For additional support or questions, refer to:
- `CHAOS_QUICK_START.md` for quick setup
- `STAGE_6.5_README.md` for project overview
- `STAGE_6.5_VERIFICATION_CHECKLIST.md` for validation checklist