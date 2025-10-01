# Load Test Automation Guide

**Version:** 1.0  
**Last Updated:** 2025-01-27  

## 📖 Overview

This guide provides comprehensive documentation for the automated load testing system implemented in Stage 6.4. The system includes load simulation, performance validation, SLO monitoring, and automatic rollback capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Required packages: `aiohttp`, `pyyaml`, `requests`
- Target service running and accessible

### Installation

```bash
# Install required dependencies
pip install aiohttp pyyaml requests

# Optional: Install monitoring dependencies
pip install psutil docker
```

### Basic Load Test

```bash
# Run a basic load test
python3 deploy/load_test.py --target http://localhost:8000 --concurrency 100 --duration 300

# Run with custom configuration
python3 deploy/load_test.py \
  --target http://your-service.com \
  --concurrency 500 \
  --duration 600 \
  --pattern burst \
  --config deploy/performance_config.yml \
  --output deploy/reports/performance_report.md
```

## 🔧 Configuration

### Performance Configuration

Edit `deploy/performance_config.yml` to customize SLO thresholds:

```yaml
thresholds:
  latency:
    p50: 100    # 50th percentile latency in ms
    p95: 250    # 95th percentile latency in ms
    p99: 400    # 99th percentile latency in ms
  error_rate: 0.5  # Maximum acceptable error rate (%)
  throughput: 1000 # Minimum requests per second

environments:
  staging:
    thresholds:
      latency:
        p50: 150
        p95: 300
        p99: 500
      error_rate: 1.0
      throughput: 500
  
  production:
    thresholds:
      latency:
        p50: 80
        p95: 200
        p99: 350
      error_rate: 0.1
      throughput: 2000
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PROMETHEUS_PUSHGATEWAY_URL` | Prometheus Pushgateway endpoint | No | - |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | No | - |
| `ENVIRONMENT` | Environment name (staging/production) | No | staging |

## 📊 Load Test Patterns

### Sustained Load (Default)

```bash
python3 deploy/load_test.py --pattern sustained --concurrency 100 --duration 300
```

**Characteristics:**
- Consistent load over time
- Random inter-request delays (0.01-0.1s)
- Best for: Capacity testing, baseline performance

### Burst Load

```bash
python3 deploy/load_test.py --pattern burst --concurrency 500 --duration 180
```

**Characteristics:**
- Rapid bursts of requests followed by pauses
- Burst size: 10 requests
- Pause duration: 0.5-2.0s
- Best for: Traffic spike simulation, cache warming

### Ramp-up Load

```bash
python3 deploy/load_test.py --pattern ramp-up --concurrency 1000 --duration 600
```

**Characteristics:**
- Gradual increase in concurrent users
- Ramp duration: 30 seconds
- Best for: Gradual load increase testing

## 📈 Understanding Load Test Metrics

### Latency Metrics

| Metric | Description | Typical Values |
|--------|-------------|----------------|
| **P50 (Median)** | 50% of requests complete within this time | 50-150ms |
| **P95** | 95% of requests complete within this time | 200-500ms |
| **P99** | 99% of requests complete within this time | 500-1000ms |

### Performance Metrics

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Throughput** | Requests per second | Total requests / Test duration |
| **Error Rate** | Percentage of failed requests | (Failed requests / Total requests) × 100 |
| **Response Time** | Time to complete a request | End time - Start time |

### Resource Metrics

| Metric | Description | Monitoring |
|--------|-------------|------------|
| **CPU Usage** | CPU utilization during test | Docker stats / system monitoring |
| **Memory Usage** | Memory consumption during test | Docker stats / system monitoring |

## 🎯 SLO Validation

### Service Level Objectives (SLOs)

The system validates performance against configurable SLO thresholds:

```yaml
# Example SLO configuration
thresholds:
  latency:
    p50: 100    # Median response time < 100ms
    p95: 250    # 95% of requests < 250ms
    p99: 400    # 99% of requests < 400ms
  error_rate: 0.5  # Error rate < 0.5%
  throughput: 1000 # Handle > 1000 req/sec
```

### SLO Violations

When SLOs are violated, the system:

1. **Logs violations** with specific metrics
2. **Triggers alerts** (Slack notifications)
3. **Exports metrics** to Prometheus
4. **Can trigger rollback** (if auto-rollback enabled)

### Example SLO Violation Report

```markdown
## ❌ SLO Violations

- P95 latency 350.2ms exceeds threshold 250ms
- Error rate 1.2% exceeds threshold 0.5%
- Throughput 850.5 req/sec below threshold 1000 req/sec
```

## 🔄 Canary Testing

### Running Canary Verification

```bash
# Basic canary verification
python3 canary_verify.py \
  --canary-url http://canary.example.com \
  --production-url http://prod.example.com

# With load testing enabled
python3 canary_verify.py \
  --canary-url http://canary.example.com \
  --production-url http://prod.example.com \
  --load-test \
  --auto-rollback-on-loadfail \
  --load-concurrency 200 \
  --load-duration 300
```

### Canary Verification Steps

1. **Shadow Testing** - Mirror production traffic to canary
2. **Load Testing** - Run controlled load tests against canary
3. **Production Comparison** - Compare canary vs production performance

## 🚀 Progressive Rollout

### Running Progressive Rollout

```bash
# Basic progressive rollout
python3 progressive_rollout.py --deployment backend-v2

# With load testing at each stage
python3 progressive_rollout.py \
  --deployment backend-v2 \
  --namespace production \
  --load-test \
  --auto-rollback-on-loadfail
```

### Rollout Stages

| Stage | Traffic % | Duration | Load Test |
|-------|-----------|----------|-----------|
| 1 | 5% | 5 minutes | Optional |
| 2 | 25% | 10 minutes | Optional |
| 3 | 50% | 15 minutes | Optional |
| 4 | 100% | 5 minutes | Optional |

## 📊 Monitoring & Observability

### Prometheus Metrics

The system exports the following metrics:

```
# Latency metrics
loadtest_latency_p50_ms{job="loadtest",instance="loadtest-1234567890"} 95.5
loadtest_latency_p95_ms{job="loadtest",instance="loadtest-1234567890"} 245.2
loadtest_latency_p99_ms{job="loadtest",instance="loadtest-1234567890"} 398.7

# Performance metrics
loadtest_throughput_rps{job="loadtest",instance="loadtest-1234567890"} 1050.3
loadtest_error_rate_percent{job="loadtest",instance="loadtest-1234567890"} 0.2

# SLO compliance
loadtest_slo_passed{job="loadtest",instance="loadtest-1234567890"} 1
loadtest_slo_violations_count{job="loadtest",instance="loadtest-1234567890"} 0
```

### Deployment Reports

Performance results are logged to `deploy/deployment_report.md`:

```markdown
## 📊 Load Test Performance Results

**Timestamp:** 2025-01-27 10:30:00  
**Status:** ✅ PASSED  
**Auto-rollback Triggered:** No  

### Performance Metrics

| Metric | Value | Unit |
|--------|-------|------|
| Total Requests | 15,750 | requests |
| Duration | 300.0 | seconds |
| Throughput | 1,050.3 | req/sec |
| Error Rate | 0.15 | % |
| P50 Latency | 95.5 | ms |
| P95 Latency | 245.2 | ms |
| P99 Latency | 398.7 | ms |
```

## 🔧 CI/CD Integration

### GitHub Actions Workflow

The system integrates with GitHub Actions via `loadtest.yml`:

```yaml
jobs:
  load-test:
    uses: ./.github/workflows/loadtest.yml
    with:
      target_url: "http://your-service.com"
      concurrency: 500
      duration: 300
      environment: "staging"
      fail_on_violation: true
```

### Workflow Integration

```yaml
# Example integration in your main workflow
jobs:
  shadow-test:
    uses: ./.github/workflows/shadow-test.yml
  
  load-test:
    needs: shadow-test
    uses: ./.github/workflows/loadtest.yml
    with:
      target_url: ${{ needs.shadow-test.outputs.canary_url }}
      concurrency: 500
      duration: 300
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. High Latency

**Symptoms:**
- P95 latency > 500ms
- P99 latency > 1000ms

**Causes:**
- Resource contention (CPU/Memory)
- Database performance issues
- Network latency
- Application bottlenecks

**Solutions:**
```bash
# Check resource usage
docker stats

# Monitor database performance
# Check application logs for bottlenecks
# Verify network connectivity
```

#### 2. High Error Rate

**Symptoms:**
- Error rate > 1%
- HTTP 5xx responses

**Causes:**
- Application exceptions
- Dependency failures
- Resource exhaustion
- Configuration issues

**Solutions:**
```bash
# Check application logs
# Verify dependencies are healthy
# Monitor resource usage
# Review configuration
```

#### 3. Low Throughput

**Symptoms:**
- Throughput < expected threshold
- Requests queuing up

**Causes:**
- Connection pool exhaustion
- Database connection limits
- CPU/Memory bottlenecks
- Inefficient algorithms

**Solutions:**
```bash
# Increase connection pool sizes
# Optimize database queries
# Scale resources
# Profile application performance
```

### Debug Mode

Run load tests with verbose logging:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 deploy/load_test.py --target http://localhost:8000 --concurrency 10 --duration 60
```

### Performance Tuning

#### 1. Adjust SLO Thresholds

```yaml
# Staging environment (more lenient)
staging:
  thresholds:
    latency:
      p50: 150
      p95: 300
      p99: 500
    error_rate: 1.0
    throughput: 500

# Production environment (strict)
production:
  thresholds:
    latency:
      p50: 80
      p95: 200
      p99: 350
    error_rate: 0.1
    throughput: 2000
```

#### 2. Optimize Load Test Parameters

```bash
# Start with lower concurrency
python3 deploy/load_test.py --concurrency 50 --duration 180

# Gradually increase
python3 deploy/load_test.py --concurrency 100 --duration 300
python3 deploy/load_test.py --concurrency 200 --duration 300
```

#### 3. Monitor Resource Usage

```bash
# Install monitoring tools
pip install psutil

# Monitor during load test
python3 deploy/load_test.py --target http://localhost:8000 &
htop  # or top
```

## 📚 Advanced Usage

### Custom Endpoint Weights

Modify `deploy/performance_config.yml`:

```yaml
load_test:
  endpoints:
    "/api/health": 0.05      # 5% of traffic
    "/api/users": 0.25       # 25% of traffic
    "/api/orders": 0.30      # 30% of traffic (highest load)
    "/api/products": 0.20    # 20% of traffic
    "/api/analytics": 0.10   # 10% of traffic
    "/api/search": 0.10      # 10% of traffic
```

### Custom Rollout Stages

```bash
# Define custom stages
python3 progressive_rollout.py \
  --deployment backend-v2 \
  --stages '[
    {"name": "1% Traffic", "percentage": 1, "duration": 180},
    {"name": "10% Traffic", "percentage": 10, "duration": 300},
    {"name": "50% Traffic", "percentage": 50, "duration": 600},
    {"name": "100% Traffic", "percentage": 100, "duration": 300}
  ]'
```

### Environment-Specific Configuration

```bash
# Set environment
export ENVIRONMENT=production

# Run with production thresholds
python3 deploy/load_test.py --config deploy/performance_config.yml
```

## 🔒 Security Considerations

### Authentication

For authenticated endpoints, configure authentication:

```bash
# Set authentication headers
export API_KEY="your-api-key"
export AUTH_TOKEN="your-auth-token"

# Modify load test to include auth headers
# (Requires code modification)
```

### Network Security

- Use HTTPS for all load test targets
- Implement rate limiting on target services
- Monitor for DDoS-like patterns
- Use dedicated test environments

## 📞 Support

### Getting Help

1. **Check logs** in `deploy/deployment_report.md`
2. **Review metrics** in Prometheus/Grafana
3. **Test locally** with debug mode
4. **Verify configuration** in `deploy/performance_config.yml`

### Common Commands

```bash
# Test basic connectivity
curl -f http://your-service.com/api/health

# Run quick smoke test
python3 deploy/load_test.py --concurrency 10 --duration 30 --target http://your-service.com

# Check configuration
python3 -c "import yaml; print(yaml.safe_load(open('deploy/performance_config.yml')))"

# Validate imports
python3 -c "from deploy.load_test import LoadTestEngine; print('Import successful')"
```

---

**🎯 This guide covers all aspects of the load test automation system. For additional help, refer to the main Stage 6.4 documentation or contact the development team.**
