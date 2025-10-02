# Chaos Engineering Guide - Stage 6.5

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Getting Started](#getting-started)
5. [Usage Examples](#usage-examples)
6. [Scenario Types](#scenario-types)
7. [SLO Targets](#slo-targets)
8. [CI/CD Integration](#cicd-integration)
9. [Metrics and Interpretation](#metrics-and-interpretation)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)
12. [Advanced Topics](#advanced-topics)

## Overview

### What is Chaos Engineering?

Chaos Engineering is the discipline of experimenting on a system to build confidence in its capability to withstand turbulent conditions in production. This suite implements automated chaos injection and resilience validation for the MAGSASA-CARD-ERP system.

### Purpose

The Chaos Engineering Suite (Stage 6.5) provides:

- **Automated Fault Injection**: Simulate real-world failure scenarios
- **Resilience Validation**: Measure system recovery and SLO compliance
- **CI/CD Integration**: Automated testing in the deployment pipeline
- **Comprehensive Reporting**: Actionable insights and recommendations

### Key Benefits

✅ **Proactive Risk Identification**: Discover weaknesses before production  
✅ **Improved Reliability**: Build systems that gracefully handle failures  
✅ **Confidence**: Validate that SLOs are met under adverse conditions  
✅ **Documentation**: Understand system behavior under stress  

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chaos Engineering Suite                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ Chaos Injector   │─────▶│   Target System  │            │
│  │                  │      │                  │            │
│  │ - CPU Stress     │      │ - Backend API    │            │
│  │ - Memory Leak    │      │ - Database       │            │
│  │ - Network Delay  │      │ - Services       │            │
│  │ - Container Crash│      └──────────────────┘            │
│  │ - DB Downtime    │              │                        │
│  └──────────────────┘              │                        │
│           │                         │                        │
│           │                         ▼                        │
│           │              ┌──────────────────┐                │
│           └─────────────▶│ Resilience       │                │
│                          │ Validator        │                │
│                          │                  │                │
│                          │ - MTTR           │                │
│                          │ - Error Rate     │                │
│                          │ - Availability   │                │
│                          │ - Latency        │                │
│                          └──────────────────┘                │
│                                   │                           │
│                                   ▼                           │
│                          ┌──────────────────┐                │
│                          │   Reports &      │                │
│                          │   Artifacts      │                │
│                          │                  │                │
│                          │ - chaos_report.md│                │
│                          │ - JSON metrics   │                │
│                          └──────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Chaos Injector (`deploy/chaos_injector.py`)

The main chaos injection engine that simulates failure scenarios.

**Features:**
- Modular failure injection
- Multiple intensity levels (light, medium, heavy)
- Safety mechanisms and cleanup
- Dry-run mode for testing
- Graceful signal handling

**Supported Failure Types:**
- CPU exhaustion
- Memory leaks/pressure
- Network latency
- Packet loss
- Container crashes
- Database downtime
- Disk I/O stress

### 2. Chaos Scenarios (`deploy/chaos_scenarios.yml`)

YAML configuration defining test scenarios and SLO targets.

**Configuration Structure:**
- Scenario definitions with parameters
- SLO target thresholds
- Scenario groups (smoke, standard, stress)
- Environment-specific settings
- Safety configurations

### 3. Resilience Validator (`deploy/resilience_validator.py`)

SLO compliance validator that measures recovery metrics.

**Measured Metrics:**
- **MTTR** (Mean Time To Recovery)
- **Error Rate** (percentage of failed requests)
- **Availability** (uptime percentage)
- **Latency Degradation** (performance impact)
- **Recovery Time** (time to full recovery)

### 4. CI/CD Workflow (`.github/workflows/chaos.yml`)

Automated GitHub Actions workflow for chaos testing.

**Features:**
- Triggered on PRs, manual dispatch, or schedule
- Service deployment and health checks
- Chaos injection execution
- Resilience validation
- Artifact uploads and PR comments

## Getting Started

### Prerequisites

```bash
# Python 3.11+
python --version

# Required packages
pip install -r requirements.txt

# Optional (for better chaos simulation)
sudo apt-get install stress-ng  # Linux
brew install stress-ng          # macOS
```

### Installation

```bash
# Clone repository
git clone <repository-url>
cd MAGSASA-CARD-ERP

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x deploy/chaos_injector.py
chmod +x deploy/resilience_validator.py
```

### Quick Start

```bash
# 1. Start your application
cd src
python main.py &

# Wait for it to be ready
sleep 5

# 2. Run chaos tests (dry run first)
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --dry-run

# 3. Run actual chaos test
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --output deploy/chaos_results.json

# 4. Validate resilience
python deploy/resilience_validator.py \
  --target http://localhost:8000 \
  --chaos-results deploy/chaos_results.json \
  --report deploy/chaos_report.md \
  --fail-on-violation

# 5. View report
cat deploy/chaos_report.md
```

## Usage Examples

### Example 1: Run Specific Scenario

```bash
# Run only CPU stress test
python deploy/chaos_injector.py \
  --scenario "Medium CPU Stress" \
  --target http://localhost:8000
```

### Example 2: Custom Configuration

```bash
# Use custom scenarios file
python deploy/chaos_injector.py \
  --config custom_scenarios.yml \
  --target http://staging.example.com \
  --output results/chaos_$(date +%Y%m%d).json
```

### Example 3: Verbose Debugging

```bash
# Run with verbose logging
python deploy/chaos_injector.py \
  --verbose \
  --target http://localhost:8000
```

### Example 4: CI/CD Integration

```bash
# Run in CI pipeline with strict validation
python deploy/chaos_injector.py \
  --config deploy/chaos_scenarios.yml \
  --target http://localhost:8000 \
  --output deploy/chaos_results.json

python deploy/resilience_validator.py \
  --chaos-results deploy/chaos_results.json \
  --fail-on-violation
```

## Scenario Types

### CPU Exhaustion

Stresses CPU cores to test system behavior under high CPU load.

**Intensity Levels:**
- **Light**: 2 CPU workers (minimal impact)
- **Medium**: 4 CPU workers (moderate impact)
- **Heavy**: 8 CPU workers (severe impact)

**Expected Behavior:**
- Request latency may increase
- Throughput may decrease
- System should not crash or become unresponsive

### Memory Stress

Allocates memory to test memory management and swapping.

**Intensity Levels:**
- **Light**: 256MB allocation
- **Medium**: 512MB allocation
- **Heavy**: 1GB allocation

**Expected Behavior:**
- Memory usage increases
- System may start swapping
- OOM killer should not be triggered

### Network Delay

Injects latency into network requests.

**Intensity Levels:**
- **Light**: 50ms delay
- **Medium**: 200ms delay
- **Heavy**: 500ms delay

**Expected Behavior:**
- Request latency increases proportionally
- Timeouts should be handled gracefully
- Retries should work correctly

### Packet Loss

Simulates unreliable network conditions.

**Intensity Levels:**
- **Light**: 5% packet loss
- **Medium**: 15% packet loss
- **Heavy**: 30% packet loss

**Expected Behavior:**
- Retry mechanisms should activate
- Connection pooling should handle failures
- Error rates may increase slightly

### Container Crash

Restarts application container to test recovery.

**Expected Behavior:**
- Brief downtime during restart
- Service should recover automatically
- Connections should be re-established
- No data loss

### Database Downtime

Simulates database failure and recovery.

**Intensity Levels:**
- **Light**: 10s downtime (brief outage)
- **Heavy**: 30s downtime (extended outage)

**Expected Behavior:**
- Connection pool should handle disconnections
- Retries should be attempted
- Graceful degradation of dependent services
- Full recovery after database restart

## SLO Targets

### Default Thresholds

| Metric | Target | Description |
|--------|--------|-------------|
| **MTTR** | ≤ 30s | Mean Time To Recovery |
| **Error Rate** | ≤ 5% | Percentage of failed requests |
| **Availability** | ≥ 95% | Uptime percentage during chaos |
| **Latency Degradation** | ≤ 500ms | Increase in response time |
| **Recovery Time** | ≤ 10s | Time to full recovery |

### Environment-Specific Targets

#### Development
```yaml
mttr_seconds: 60
max_error_rate_percent: 10.0
min_availability_percent: 90.0
```

#### Staging
```yaml
mttr_seconds: 45
max_error_rate_percent: 5.0
min_availability_percent: 95.0
```

#### Production
```yaml
mttr_seconds: 30
max_error_rate_percent: 1.0
min_availability_percent: 99.0
```

### Customizing SLO Targets

Edit `deploy/chaos_scenarios.yml`:

```yaml
slo_targets:
  mttr_seconds: 20  # More strict MTTR
  max_error_rate_percent: 2.0
  min_availability_percent: 98.0
  max_latency_degradation_ms: 300
```

## CI/CD Integration

### GitHub Actions

The chaos workflow runs automatically on:

1. **Pull Requests**: Validates resilience before merging
2. **Manual Dispatch**: On-demand testing with custom parameters
3. **Scheduled**: Nightly regression testing

### Workflow Configuration

```yaml
# .github/workflows/chaos.yml
on:
  pull_request:
    branches: [main, develop]
  workflow_dispatch:
    inputs:
      intensity:
        type: choice
        options: [smoke_test, standard_test, stress_test]
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
```

### Manual Trigger

1. Go to GitHub Actions tab
2. Select "Chaos Engineering Tests"
3. Click "Run workflow"
4. Choose intensity level
5. Optionally specify target URL

### Artifacts

The workflow uploads:
- `chaos-results`: JSON results from chaos injection
- `resilience-validation`: Validation results and report
- Retention: 30 days

### PR Comments

Workflow automatically comments on PRs with:
- Test status (passed/failed)
- SLO compliance summary
- Violations (if any)
- Links to detailed reports

## Metrics and Interpretation

### MTTR (Mean Time To Recovery)

**Definition**: Average time for system to recover from failures.

**Interpretation:**
- ✅ **Good**: ≤ 30s - System recovers quickly
- ⚠️ **Warning**: 30-60s - Consider optimization
- ❌ **Poor**: > 60s - Requires immediate attention

**Improvement Strategies:**
- Implement health checks
- Add automated restart mechanisms
- Optimize startup time
- Pre-warm caches and connections

### Error Rate

**Definition**: Percentage of requests that fail during chaos.

**Interpretation:**
- ✅ **Good**: ≤ 5% - Graceful degradation
- ⚠️ **Warning**: 5-10% - Review error handling
- ❌ **Poor**: > 10% - Insufficient resilience

**Improvement Strategies:**
- Add retry logic with exponential backoff
- Implement circuit breakers
- Use bulkheads for isolation
- Add fallback mechanisms

### Availability

**Definition**: Percentage of time system is operational during chaos.

**Interpretation:**
- ✅ **Good**: ≥ 95% - High availability
- ⚠️ **Warning**: 90-95% - Acceptable for non-critical
- ❌ **Poor**: < 90% - Critical issues

**Improvement Strategies:**
- Add redundancy (multiple instances)
- Implement load balancing
- Use health checks for routing
- Enable automatic failover

### Latency Degradation

**Definition**: Increase in response time during chaos vs baseline.

**Interpretation:**
- ✅ **Good**: ≤ 500ms - Acceptable impact
- ⚠️ **Warning**: 500-1000ms - User experience affected
- ❌ **Poor**: > 1000ms - Severe degradation

**Improvement Strategies:**
- Add caching layers
- Optimize database queries
- Implement request queuing
- Use asynchronous processing

## Troubleshooting

### Common Issues

#### 1. Service Not Starting

**Symptoms**: Health checks fail during setup

**Solutions:**
```bash
# Check if port is in use
lsof -i :8000

# Check application logs
tail -f logs/app.log

# Verify dependencies
pip list | grep -E "aiohttp|flask"
```

#### 2. Stress-ng Not Available

**Symptoms**: Warning about stress-ng not found

**Solutions:**
```bash
# Linux
sudo apt-get install stress-ng

# macOS
brew install stress-ng

# Or rely on Python fallback (automatic)
```

#### 3. Permission Denied for Network Chaos

**Symptoms**: Network delay/loss scenarios fail

**Solutions:**
```bash
# Linux: Add capability (preferred)
sudo setcap cap_net_admin+ep /path/to/python

# Or run with sudo (not recommended for production)
sudo python deploy/chaos_injector.py ...

# Or use --dry-run to simulate
python deploy/chaos_injector.py --dry-run
```

#### 4. Container Not Found

**Symptoms**: Container chaos scenarios fail

**Solutions:**
```bash
# List running containers
docker ps

# Update container name in scenarios
# Edit deploy/chaos_scenarios.yml
target: "your-container-name"
```

#### 5. SLO Violations

**Symptoms**: Tests fail with SLO violations

**Solutions:**
1. Review the chaos report for specific violations
2. Check if violations are legitimate system issues
3. Consider adjusting SLO targets if expectations are too strict
4. Implement recommended improvements from report

### Debug Mode

```bash
# Enable verbose logging
python deploy/chaos_injector.py --verbose

# Enable Python debugging
python -m pdb deploy/chaos_injector.py
```

### Log Analysis

```bash
# View chaos injection logs
grep "chaos" logs/*.log

# Check for errors
grep "ERROR" deploy/chaos_results.json

# Monitor system during chaos
watch -n 1 'ps aux | grep python'
```

## Best Practices

### 1. Start Small

Begin with light intensity scenarios:

```bash
# Run smoke test first
python deploy/chaos_injector.py \
  --scenario "Light CPU Stress"
```

### 2. Use Dry Run

Test configurations without actual injection:

```bash
python deploy/chaos_injector.py --dry-run
```

### 3. Monitor Actively

Watch system metrics during chaos:

```bash
# Terminal 1: Run chaos
python deploy/chaos_injector.py

# Terminal 2: Monitor
watch -n 1 'docker stats'

# Terminal 3: Check health
watch -n 1 'curl http://localhost:8000/api/health'
```

### 4. Progressive Rollout

Increase intensity gradually:

1. **Week 1**: Smoke tests (light scenarios)
2. **Week 2**: Standard tests (medium scenarios)
3. **Week 3**: Stress tests (heavy scenarios)
4. **Week 4**: Infrastructure tests (containers, database)

### 5. Schedule Wisely

Run chaos tests during low-traffic periods:

```yaml
# .github/workflows/chaos.yml
schedule:
  - cron: '0 2 * * *'  # 2 AM daily
```

### 6. Document Results

Keep a chaos engineering log:

```bash
# Create log entry
echo "$(date): Ran heavy CPU stress - MTTR: 25s" >> chaos_log.txt
```

### 7. Integrate with Monitoring

Export metrics to your monitoring system:

```python
# Example: Send to Prometheus
from prometheus_client import Gauge

mttr_gauge = Gauge('chaos_mttr_seconds', 'Mean Time To Recovery')
mttr_gauge.set(metrics.mttr)
```

### 8. Team Communication

Notify team before running chaos in shared environments:

```bash
# Slack notification example
curl -X POST $SLACK_WEBHOOK \
  -d '{"text": "🔥 Starting chaos tests in staging"}'
```

## Advanced Topics

### Custom Scenario Development

Create custom chaos scenarios:

```python
# custom_chaos.py
async def inject_custom_chaos(scenario: ChaosScenario) -> bool:
    """Your custom chaos logic."""
    # Implement custom failure injection
    return True

# Register with injector
injector.register_scenario_type("custom", inject_custom_chaos)
```

### Chaos Mesh Integration

For Kubernetes environments:

```yaml
# chaos-mesh-experiment.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure
spec:
  action: pod-failure
  mode: one
  selector:
    namespaces:
      - default
  duration: '30s'
```

### Prometheus Integration

Export chaos metrics:

```python
from prometheus_client import start_http_server, Gauge

# Start Prometheus endpoint
start_http_server(8001)

# Define metrics
chaos_mttr = Gauge('chaos_mttr_seconds', 'Mean Time To Recovery')
chaos_error_rate = Gauge('chaos_error_rate', 'Error rate during chaos')

# Update metrics
chaos_mttr.set(validator.metrics.mttr)
chaos_error_rate.set(validator.metrics.error_rate_percent)
```

### Grafana Dashboards

Create dashboards to visualize chaos metrics:

```json
{
  "dashboard": {
    "title": "Chaos Engineering Metrics",
    "panels": [
      {
        "title": "MTTR Trend",
        "targets": [{
          "expr": "chaos_mttr_seconds"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "chaos_error_rate"
        }]
      }
    ]
  }
}
```

### Machine Learning Integration

Auto-adjust chaos intensity based on system performance:

```python
from sklearn.linear_model import LinearRegression

# Train model on historical data
model = LinearRegression()
model.fit(historical_chaos_intensity, historical_mttr)

# Predict optimal intensity
optimal_intensity = model.predict([[current_system_capacity]])
```

### Multi-Region Chaos

Test cross-region resilience:

```yaml
scenarios:
  - name: "Region Failure"
    type: "region_outage"
    target_region: "us-west-2"
    duration: 300
    parameters:
      failover_region: "us-east-1"
```

## Additional Resources

### Documentation
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Netflix Chaos Engineering](https://netflix.github.io/chaosmonkey/)
- [Chaos Toolkit](https://chaostoolkit.org/)

### Tools
- [Chaos Mesh](https://chaos-mesh.org/) - Kubernetes chaos engineering
- [Litmus](https://litmuschaos.io/) - Cloud-native chaos engineering
- [Gremlin](https://www.gremlin.com/) - Enterprise chaos engineering

### Community
- [Chaos Engineering Slack](https://chaos-engineering.slack.com)
- [CNCF Chaos Engineering WG](https://github.com/cncf/tag-app-delivery/tree/main/chaos-engineering)

## Support

For questions or issues:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [GitHub Issues](https://github.com/your-repo/issues)
3. Contact DevOps team: devops@company.com

---

**Last Updated**: October 2025  
**Version**: Stage 6.5  
**Maintainer**: DevOps Team

