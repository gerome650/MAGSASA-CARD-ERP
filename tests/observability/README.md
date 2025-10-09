# 🧪 Observability Load & Concurrency Test Suite

Comprehensive async load testing, concurrency validation, and latency benchmarking for the MAGSASA-CARD-ERP observability system.

## 📋 Overview

This test suite implements **Step 2 of the CI Readiness Plan**, focusing on:

- **Concurrency Testing**: Validate thread-safety and race condition handling
- **Throughput Testing**: Measure request handling capacity under load
- **Latency Benchmarking**: Enforce SLO thresholds for P50/P95/P99 latency
- **Race Safety**: Ensure data consistency under concurrent operations

## 🎯 Test Categories

### 1. Webhook Load Testing (`test_async_load_webhook.py`)

Tests the FastAPI webhook server's ability to handle high concurrency:

- ✅ **Burst Load**: 100+ concurrent POST requests
- ✅ **Throughput**: Requests per second measurement
- ✅ **Sequential vs Parallel**: Performance comparison
- ✅ **Sustained Load**: Multi-wave stress testing
- ✅ **Error Rates**: Failure rate under load
- ✅ **Payload Sizes**: Variable payload handling

**Key Metrics:**
- Success Rate: 100%
- Avg Latency: < 1.0s
- P50 Latency: < 0.5s
- Error Rate: < 1%

### 2. Agent Concurrency Testing (`test_concurrent_agent_processing.py`)

Validates AI Incident Agent's concurrent processing safety:

- ✅ **Thread Safety**: 100 concurrent `analyze_incident()` calls
- ✅ **Parallel Notifications**: Concurrent Slack + PagerDuty sends
- ✅ **Context Collection**: Multi-source data gathering concurrency
- ✅ **Postmortem Generation**: Concurrent file operations
- ✅ **Mixed Workloads**: Realistic mixed operation patterns
- ✅ **Memory Stability**: Multi-wave leak detection

**Key Validations:**
- No race conditions
- No data corruption
- No resource leaks
- Consistent results across concurrent operations

### 3. Latency Metrics Testing (`test_latency_metrics.py`)

Performance benchmarking and SLO enforcement:

- ✅ **Distribution Testing**: P50/P95/P99 at different loads (10, 50, 100 req)
- ✅ **Consistency**: Cross-wave latency stability
- ✅ **Stress Testing**: 200 concurrent request handling
- ✅ **Health Check Comparison**: Processing overhead analysis
- ✅ **Metrics Endpoint**: Monitoring performance impact
- ✅ **Cold Start**: Initialization overhead measurement
- ✅ **Throughput Tradeoffs**: Optimal operating point analysis

**SLO Thresholds:**
- P50 < 300ms
- P95 < 700ms (load), < 3.0s (stress)
- P99 < 1000ms (load)
- Health Check < 100ms

## 🚀 Running the Tests

### Run All Performance Tests

```bash
# Run all performance tests
pytest tests/observability/ -v -m performance

# Run with coverage
pytest tests/observability/ -v -m performance --cov=observability

# Run parallel (faster)
pytest tests/observability/ -v -m performance -n auto
```

### Run Specific Test Suites

```bash
# Webhook load tests only
pytest tests/observability/test_async_load_webhook.py -v

# Agent concurrency tests only
pytest tests/observability/test_concurrent_agent_processing.py -v

# Latency metrics only
pytest tests/observability/test_latency_metrics.py -v
```

### Run Specific Tests

```bash
# Run burst load test
pytest tests/observability/test_async_load_webhook.py::test_webhook_burst_load_and_throughput -v

# Run latency distribution at 100 req
pytest tests/observability/test_latency_metrics.py::test_latency_distribution_under_load[100] -v

# Run thread safety test
pytest tests/observability/test_concurrent_agent_processing.py::test_agent_concurrent_processing_is_threadsafe -v
```

## 📊 Sample Output

```
📊 Burst Load Test Results:
   Total Requests: 100
   Successful: 100
   Failed: 0
   Total Time: 2.45s
   Throughput: 40.8 req/s
   Avg Latency: 0.234s
   P50 Latency: 0.215s
   StdDev: 0.045s

📈 Latency Distribution (n=100):
   Min:  124.5ms
   Avg:  234.2ms
   P50:  215.3ms
   P95:  456.7ms
   P99:  678.9ms
   Max:  723.1ms

🔄 Concurrent Processing Results:
   Total Tasks: 100
   Successful: 100
   Failed: 0
```

## 🔧 Configuration

### Pytest Markers

Tests are marked with `@pytest.mark.performance` for selective execution:

```ini
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "performance: Performance and load tests (long-running)"
]
```

### Skip Performance Tests in CI

```bash
# Run all tests except performance
pytest -v -m "not performance"

# Or in CI configuration
pytest --maxfail=1 -m "not performance"
```

## 📦 Dependencies

Required packages (already in `requirements-dev.txt`):

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
aiohttp>=3.9.0
```

## 🎯 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Performance Tests
  run: |
    pytest tests/observability/ \
      -v \
      -m performance \
      --junit-xml=reports/performance-tests.xml \
      --html=reports/performance-tests.html
```

### Scheduled Nightly Run

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Run at 2 AM daily

jobs:
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Performance Suite
        run: pytest tests/observability/ -v -m performance
```

## 📈 Metrics & Thresholds

| Metric | Target | Threshold |
|--------|--------|-----------|
| Success Rate | 100% | ≥ 95% |
| P50 Latency | < 300ms | < 500ms |
| P95 Latency | < 700ms | < 1000ms |
| P99 Latency | < 1000ms | < 2000ms |
| Throughput | > 40 req/s | > 20 req/s |
| Error Rate | 0% | < 1% |
| Concurrent Safety | 100% | 100% |

## 🐛 Troubleshooting

### Tests Timing Out

If tests timeout, increase the httpx timeout:

```python
async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
    # ... tests
```

### Import Errors

Ensure observability modules are importable:

```bash
# Add to PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:${PWD}"
pytest tests/observability/ -v
```

### Slow Tests

Run tests in parallel:

```bash
pytest tests/observability/ -v -m performance -n 4
```

## 🚦 Success Criteria

The test suite passes if:

1. ✅ All requests complete successfully (100% success rate)
2. ✅ Average latency meets SLO (< 1.0s under load)
3. ✅ P95 latency acceptable (< 1.0s normal, < 3.0s stress)
4. ✅ No race conditions or data corruption detected
5. ✅ No memory leaks across multiple waves
6. ✅ Error rate below 1% under all conditions
7. ✅ Throughput meets minimum requirements (> 20 req/s)

## 📝 Notes

- **Performance Markers**: All tests use `@pytest.mark.performance` for selective execution
- **Skip Logic**: Tests automatically skip if `httpx` is not installed
- **Async Testing**: All tests use `pytest-asyncio` for proper async handling
- **Mock Safety**: Agent tests mock external dependencies to avoid network calls

## 🔗 Related Documentation

- [CI Readiness Plan](../../docs/ci-readiness-plan.md)
- [Observability Architecture](../../observability/README.md)
- [Test Strategy](../../docs/test-strategy.md)

## 🏆 Best Practices

1. **Run Locally First**: Validate performance on local before CI
2. **Monitor Trends**: Track latency metrics over time
3. **Adjust Thresholds**: Update SLOs based on production requirements
4. **Parallel Execution**: Use `-n auto` for faster local runs
5. **Selective Testing**: Use markers to run subsets during development

---

**Implemented by:** AI Assistant  
**Date:** October 7, 2025  
**Status:** ✅ Complete

