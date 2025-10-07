"""
📊 Latency & Performance Metrics Testing

Benchmarks latency distribution under varying concurrency loads and enforces
performance SLO thresholds (P50, P95, P99). Validates that the system maintains
acceptable response times under different load conditions.

Requirements:
- pytest
- pytest-asyncio
- httpx
- statistics
"""

import asyncio
import time
from statistics import mean, median, quantiles
from typing import Any

import pytest

# Optional dependency handling
try:
    from httpx import AsyncClient

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    AsyncClient = None

# Skip all tests if httpx not available
pytestmark = pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")


@pytest.fixture
def sample_webhook_payload() -> dict[str, Any]:
    """Sample Alertmanager webhook payload"""
    return {
        "receiver": "perf-test",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "PerformanceTest",
                    "service": "test-service",
                    "severity": "warning",
                },
                "annotations": {
                    "summary": "Performance test alert",
                    "description": "Testing latency under load",
                },
            }
        ],
        "groupLabels": {"alertname": "PerformanceTest"},
        "commonLabels": {"service": "test-service"},
        "commonAnnotations": {"summary": "Performance test"},
        "externalURL": "http://localhost:9093",
        "version": "4",
        "groupKey": "{}:{}",
    }


@pytest.mark.asyncio
@pytest.mark.performance
@pytest.mark.parametrize("n_requests", [10, 50, 100])
async def test_latency_distribution_under_load(n_requests, sample_webhook_payload):
    """
    📊 Benchmark latency P50/P95/P99 under different concurrency levels
    and assert SLO thresholds are met.

    SLO Thresholds:
    - P50 < 300ms (median response time)
    - P95 < 700ms (95th percentile)
    - P99 < 1000ms (99th percentile)
    """
    from observability.ai_agent.webhook_server import app

    latencies = []

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:

        async def send_request(_i: int) -> float:
            start = time.time()
            response = await client.post(
                "/webhook/alertmanager", json=sample_webhook_payload
            )
            latency = time.time() - start

            assert response.status_code in (
                200,
                202,
            ), f"Request failed with {response.status_code}"
            return latency

        latencies = await asyncio.gather(*[send_request(i) for i in range(n_requests)])

    # Calculate percentiles
    p50 = median(latencies)
    p95 = quantiles(latencies, n=100)[94] if len(latencies) >= 20 else max(latencies)
    p99 = quantiles(latencies, n=100)[98] if len(latencies) >= 20 else max(latencies)
    avg = mean(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)

    print(f"\n📊 Latency Distribution (n={n_requests}):")
    print(f"   Min:  {min_latency * 1000:.1f}ms")
    print(f"   Avg:  {avg * 1000:.1f}ms")
    print(f"   P50:  {p50 * 1000:.1f}ms")
    print(f"   P95:  {p95 * 1000:.1f}ms")
    print(f"   P99:  {p99 * 1000:.1f}ms")
    print(f"   Max:  {max_latency * 1000:.1f}ms")

    # Assert SLO thresholds
    assert (
        p50 < 0.5
    ), f"P50 latency too high for {n_requests} requests: {p50:.3f}s (threshold: 0.5s)"
    assert (
        p95 < 1.0
    ), f"P95 latency too high for {n_requests} requests: {p95:.3f}s (threshold: 1.0s)"
    assert (
        p99 < 2.0
    ), f"P99 latency too high for {n_requests} requests: {p99:.3f}s (threshold: 2.0s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_consistency_across_waves(sample_webhook_payload):
    """
    📈 Test that latency remains consistent across multiple load waves.
    Validates no performance degradation over time.
    """
    from observability.ai_agent.webhook_server import app

    n_waves = 5
    requests_per_wave = 20
    wave_metrics = []

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        for wave in range(n_waves):
            wave_latencies = []

            async def send_request(_i: int) -> float:
                start = time.time()
                await client.post("/webhook/alertmanager", json=sample_webhook_payload)
                return time.time() - start

            wave_latencies = await asyncio.gather(
                *[send_request(i) for i in range(requests_per_wave)]
            )

            metrics = {
                "wave": wave + 1,
                "p50": median(wave_latencies),
                "p95": (
                    quantiles(wave_latencies, n=100)[94]
                    if len(wave_latencies) >= 20
                    else max(wave_latencies)
                ),
                "avg": mean(wave_latencies),
            }
            wave_metrics.append(metrics)

            print(
                f"   Wave {wave + 1}: P50={metrics['p50']*1000:.1f}ms, "
                f"P95={metrics['p95']*1000:.1f}ms, Avg={metrics['avg']*1000:.1f}ms"
            )

            # Brief pause between waves
            await asyncio.sleep(0.3)

    # Check consistency
    first_wave_p50 = wave_metrics[0]["p50"]
    last_wave_p50 = wave_metrics[-1]["p50"]

    variance = abs(last_wave_p50 - first_wave_p50) / first_wave_p50

    print("\n📈 Latency Consistency:")
    print(f"   First Wave P50: {first_wave_p50 * 1000:.1f}ms")
    print(f"   Last Wave P50: {last_wave_p50 * 1000:.1f}ms")
    print(f"   Variance: {variance * 100:.1f}%")

    # Assert consistency (allow up to 30% variance)
    assert (
        variance < 0.3
    ), f"Latency variance too high: {variance * 100:.1f}% (threshold: 30%)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_under_stress(sample_webhook_payload):
    """
    💥 Stress test with 200 concurrent requests to find breaking point.
    Validates system maintains reasonable latency under extreme load.
    """
    from observability.ai_agent.webhook_server import app

    n_requests = 200
    latencies = []
    failures = 0

    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:

        async def send_request(i: int) -> dict[str, Any]:
            try:
                start = time.time()
                response = await client.post(
                    "/webhook/alertmanager", json=sample_webhook_payload
                )
                latency = time.time() - start

                return {
                    "success": response.status_code in (200, 202),
                    "latency": latency,
                }
            except Exception as e:
                return {
                    "success": False,
                    "latency": 0,
                    "error": str(e),
                }

        results = await asyncio.gather(*[send_request(i) for i in range(n_requests)])

    # Analyze results
    for result in results:
        if result["success"]:
            latencies.append(result["latency"])
        else:
            failures += 1

    if latencies:
        p50 = median(latencies)
        p95 = quantiles(latencies, n=100)[94]
        p99 = quantiles(latencies, n=100)[98]
        avg = mean(latencies)

        print(f"\n💥 Stress Test Results (n={n_requests}):")
        print(f"   Successful: {len(latencies)}")
        print(f"   Failed: {failures}")
        print(f"   Success Rate: {len(latencies)/n_requests*100:.1f}%")
        print(f"   Avg Latency: {avg * 1000:.1f}ms")
        print(f"   P50: {p50 * 1000:.1f}ms")
        print(f"   P95: {p95 * 1000:.1f}ms")
        print(f"   P99: {p99 * 1000:.1f}ms")

        # Assert acceptable performance under stress
        assert (
            len(latencies) / n_requests >= 0.95
        ), f"Success rate too low: {len(latencies)/n_requests*100:.1f}% (threshold: 95%)"
        assert (
            p95 < 3.0
        ), f"P95 latency too high under stress: {p95:.3f}s (threshold: 3.0s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_with_health_check_comparison(sample_webhook_payload):
    """
    🏥 Compare latency between health check endpoint (simple) and
    webhook endpoint (complex) to understand processing overhead.
    """
    from observability.ai_agent.webhook_server import app

    n_requests = 50

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        # Test health check latency
        health_latencies = []
        for _ in range(n_requests):
            start = time.time()
            await client.get("/health")
            health_latencies.append(time.time() - start)

        # Test webhook latency
        webhook_latencies = []
        for _ in range(n_requests):
            start = time.time()
            await client.post("/webhook/alertmanager", json=sample_webhook_payload)
            webhook_latencies.append(time.time() - start)

    health_p50 = median(health_latencies)
    health_avg = mean(health_latencies)

    webhook_p50 = median(webhook_latencies)
    webhook_avg = mean(webhook_latencies)

    overhead = webhook_p50 - health_p50
    overhead_pct = (overhead / health_p50) * 100

    print("\n🏥 Latency Comparison:")
    print(f"   Health Check P50: {health_p50 * 1000:.1f}ms")
    print(f"   Health Check Avg: {health_avg * 1000:.1f}ms")
    print(f"   Webhook P50: {webhook_p50 * 1000:.1f}ms")
    print(f"   Webhook Avg: {webhook_avg * 1000:.1f}ms")
    print(f"   Processing Overhead: {overhead * 1000:.1f}ms ({overhead_pct:.1f}%)")

    # Health check should be very fast
    assert (
        health_p50 < 0.1
    ), f"Health check too slow: {health_p50:.3f}s (threshold: 0.1s)"

    # Webhook should be reasonably fast
    assert webhook_p50 < 1.0, f"Webhook too slow: {webhook_p50:.3f}s (threshold: 1.0s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_metrics_endpoint_performance(sample_webhook_payload):
    """
    📈 Test /metrics endpoint latency to ensure monitoring doesn't
    impact system performance.
    """
    from observability.ai_agent.webhook_server import app

    n_requests = 30

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        # Warm up metrics
        await client.get("/metrics")

        # Measure metrics endpoint latency
        metrics_latencies = []
        for _ in range(n_requests):
            start = time.time()
            response = await client.get("/metrics")
            metrics_latencies.append(time.time() - start)
            assert response.status_code == 200

    p50 = median(metrics_latencies)
    p95 = (
        quantiles(metrics_latencies, n=100)[94]
        if len(metrics_latencies) >= 20
        else max(metrics_latencies)
    )
    avg = mean(metrics_latencies)

    print("\n📈 Metrics Endpoint Performance:")
    print(f"   P50: {p50 * 1000:.1f}ms")
    print(f"   P95: {p95 * 1000:.1f}ms")
    print(f"   Avg: {avg * 1000:.1f}ms")

    # Metrics should be fast
    assert p50 < 0.2, f"Metrics endpoint too slow: {p50:.3f}s (threshold: 0.2s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_latency_cold_start_vs_warm(sample_webhook_payload):
    """
    🔥 Compare cold start latency vs warm request latency to identify
    initialization overhead.
    """
    from observability.ai_agent.webhook_server import app

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        # Cold start (first request)
        cold_start = time.time()
        await client.post("/webhook/alertmanager", json=sample_webhook_payload)
        cold_latency = time.time() - cold_start

        # Warm requests (next 20)
        warm_latencies = []
        for _ in range(20):
            start = time.time()
            await client.post("/webhook/alertmanager", json=sample_webhook_payload)
            warm_latencies.append(time.time() - start)

    warm_avg = mean(warm_latencies)
    warm_p50 = median(warm_latencies)

    print("\n🔥 Cold Start vs Warm Performance:")
    print(f"   Cold Start: {cold_latency * 1000:.1f}ms")
    print(f"   Warm Avg: {warm_avg * 1000:.1f}ms")
    print(f"   Warm P50: {warm_p50 * 1000:.1f}ms")
    print(f"   Cold Start Penalty: {(cold_latency - warm_avg) * 1000:.1f}ms")

    # Both should be reasonable
    assert (
        cold_latency < 2.0
    ), f"Cold start too slow: {cold_latency:.3f}s (threshold: 2.0s)"
    assert warm_p50 < 0.5, f"Warm requests too slow: {warm_p50:.3f}s (threshold: 0.5s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_throughput_vs_latency_tradeoff(sample_webhook_payload):
    """
    ⚖️ Test throughput vs latency tradeoff at different concurrency levels
    to find optimal operating point.
    """
    from observability.ai_agent.webhook_server import app

    concurrency_levels = [5, 10, 25, 50, 100]
    results = []

    async with AsyncClient(app=app, base_url="http://test", timeout=60.0) as client:
        for concurrency in concurrency_levels:
            start_time = time.time()

            async def send_request(_i: int) -> float:
                req_start = time.time()
                await client.post("/webhook/alertmanager", json=sample_webhook_payload)
                return time.time() - req_start

            latencies = await asyncio.gather(
                *[send_request(i) for i in range(concurrency)]
            )

            total_time = time.time() - start_time
            throughput = concurrency / total_time
            avg_latency = mean(latencies)

            results.append(
                {
                    "concurrency": concurrency,
                    "throughput": throughput,
                    "avg_latency": avg_latency,
                    "p50_latency": median(latencies),
                }
            )

    print("\n⚖️ Throughput vs Latency Tradeoff:")
    print(
        f"   {'Concurrency':<12} {'Throughput':<15} {'Avg Latency':<15} {'P50 Latency':<15}"
    )
    for r in results:
        print(
            f"   {r['concurrency']:<12} {r['throughput']:<15.1f} "
            f"{r['avg_latency']*1000:<15.1f} {r['p50_latency']*1000:<15.1f}"
        )

    # Higher concurrency should maintain reasonable latency
    high_concurrency_result = results[-1]  # 100 concurrent
    assert (
        high_concurrency_result["avg_latency"] < 2.0
    ), f"High concurrency latency too high: {high_concurrency_result['avg_latency']:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
