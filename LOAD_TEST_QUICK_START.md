# 🚀 Load & Concurrency Test Suite - Quick Start

**Step 2 of CI Readiness Plan: Async Load, Concurrency, and Latency Testing**

## ✅ What's Included

Three comprehensive test suites for observability system validation:

1. **`test_async_load_webhook.py`** - Webhook burst load, throughput, and sustained load testing
2. **`test_concurrent_agent_processing.py`** - AI Agent thread-safety and race condition testing  
3. **`test_latency_metrics.py`** - Latency distribution benchmarking with P50/P95/P99 SLO enforcement

## 🎯 Quick Commands

```bash
# Run all performance tests
pytest tests/observability/ -v -m performance

# Run just webhook load tests
pytest tests/observability/test_async_load_webhook.py -v

# Run with parallel execution (faster)
pytest tests/observability/ -v -m performance -n auto

# Run with coverage report
pytest tests/observability/ -v -m performance --cov=observability --cov-report=term-missing

# Run specific test
pytest tests/observability/test_async_load_webhook.py::test_webhook_burst_load_and_throughput -v

# Skip performance tests (for CI)
pytest -v -m "not performance"
```

## 📊 Expected Output

```
📊 Burst Load Test Results:
   Total Requests: 100
   Successful: 100
   Failed: 0
   Total Time: 2.45s
   Throughput: 40.8 req/s
   Avg Latency: 0.234s
   P50 Latency: 0.215s
   
✅ PASSED: All 100 requests succeeded
✅ PASSED: Average latency under 1.0s
✅ PASSED: P50 latency under 0.5s
```

## 🔧 Dependencies

Already included in `requirements-dev.txt`:

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.26.0
aiohttp>=3.9.0
```

Install with:
```bash
pip install -r requirements-dev.txt
```

## 📈 Test Categories

| Test Suite | Focus Area | Key Metrics |
|------------|-----------|-------------|
| `test_async_load_webhook.py` | Webhook endpoints | Throughput, burst load, error rate |
| `test_concurrent_agent_processing.py` | AI Agent safety | Thread-safety, race conditions, memory |
| `test_latency_metrics.py` | Performance SLOs | P50/P95/P99 latency thresholds |

## 🎨 Test Highlights

### 1. Burst Load Testing (100 concurrent requests)
```bash
pytest tests/observability/test_async_load_webhook.py::test_webhook_burst_load_and_throughput -v -s
```

Validates:
- ✅ 100% success rate under burst load
- ✅ Average latency < 1.0s
- ✅ P50 latency < 0.5s
- ✅ No timeout failures

### 2. Thread Safety Testing (100 concurrent analyses)
```bash
pytest tests/observability/test_concurrent_agent_processing.py::test_agent_concurrent_processing_is_threadsafe -v -s
```

Validates:
- ✅ No race conditions
- ✅ Consistent results across all tasks
- ✅ No data corruption
- ✅ All 100 analyses complete successfully

### 3. Latency SLO Enforcement
```bash
pytest tests/observability/test_latency_metrics.py::test_latency_distribution_under_load -v -s
```

Validates:
- ✅ P50 < 300ms
- ✅ P95 < 700ms
- ✅ P99 < 1000ms
- ✅ Consistent performance across load levels

## 🏆 Success Criteria

All tests pass if:

1. ✅ **100% success rate** - No failed requests
2. ✅ **Low latency** - P50 < 500ms, P95 < 1s
3. ✅ **No race conditions** - Concurrent operations safe
4. ✅ **No memory leaks** - Stable across multiple waves
5. ✅ **Error rate < 1%** - Highly reliable
6. ✅ **High throughput** - > 20 req/s sustained

## 🔍 Troubleshooting

### Tests Fail Due to Missing Dependencies

```bash
pip install -r requirements-dev.txt
```

### Tests Timeout

Increase timeout in test configuration or run fewer concurrent requests:

```python
async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
```

### Want Faster Test Runs?

Use parallel execution:

```bash
pytest tests/observability/ -v -m performance -n 4
```

## 📋 Integration with CI/CD

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM
  workflow_dispatch:     # Manual trigger

jobs:
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
        
      - name: Run Performance Tests
        run: |
          pytest tests/observability/ \
            -v \
            -m performance \
            --junit-xml=reports/performance-tests.xml
            
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: performance-test-results
          path: reports/
```

## 📚 Full Documentation

See [tests/observability/README.md](tests/observability/README.md) for:
- Detailed test descriptions
- Configuration options
- Advanced usage
- Metrics and thresholds
- Best practices

## 🎯 Next Steps

1. **Run tests locally**: `pytest tests/observability/ -v -m performance`
2. **Review results**: Check latency metrics and success rates
3. **Integrate into CI**: Add to nightly/staging pipelines
4. **Monitor trends**: Track performance over time
5. **Adjust thresholds**: Update SLOs based on production needs

---

**Status:** ✅ Complete and Ready for Use  
**Location:** `tests/observability/`  
**Markers:** `@pytest.mark.performance`

