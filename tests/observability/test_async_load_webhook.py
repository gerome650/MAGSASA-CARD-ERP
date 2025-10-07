"""
🚀 Async Load & Throughput Testing for Webhook Endpoints

Tests burst load handling, concurrent request processing, and throughput for
observability webhook endpoints. Validates that the system can handle high
concurrency without failures or degraded performance.

Requirements:
- pytest
- pytest-asyncio
- httpx
- statistics
"""

import asyncio
import time
from statistics import mean, median, stdev
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
        "receiver": "test-receiver",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighCPU",
                    "service": "magsasa-card-erp",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "CPU usage above 90%",
                    "description": "CPU has been above 90% for 5 minutes",
                },
            }
        ],
        "groupLabels": {"alertname": "HighCPU"},
        "commonLabels": {"service": "magsasa-card-erp"},
        "commonAnnotations": {"summary": "CPU usage above 90%"},
        "externalURL": "http://localhost:9093",
        "version": "4",
        "groupKey": "{}:{}",
    }


@pytest.mark.asyncio
@pytest.mark.performance
async def test_webhook_burst_load_and_throughput(sample_webhook_payload):
    """
    🚀 Simulate 100 concurrent webhook POST requests and validate:
    - All requests complete successfully
    - No failures or timeouts
    - Average latency meets SLO
    - P50/P95 latency thresholds
    """
    from observability.ai_agent.webhook_server import app

    latencies = []
    errors = []
    start_time = time.time()

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:

        async def send_request(request_id: int) -> dict[str, Any]:
            """Send a single webhook request and measure latency"""
            try:
                req_start = time.time()
                response = await client.post(
                    "/webhook/alertmanager", json=sample_webhook_payload
                )
                req_end = time.time()

                latency = req_end - req_start

                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "latency": latency,
                    "success": response.status_code in (200, 202),
                }

            except Exception as e:
                return {
                    "request_id": request_id,
                    "error": str(e),
                    "success": False,
                    "latency": 0,
                }

        # Send 100 concurrent requests
        results = await asyncio.gather(*[send_request(i) for i in range(100)])

    total_time = time.time() - start_time

    # Collect metrics
    for result in results:
        if result["success"]:
            latencies.append(result["latency"])
        else:
            errors.append(result)

    # Assertions
    success_count = len(latencies)
    failure_count = len(errors)

    print("\n📊 Burst Load Test Results:")
    print("   Total Requests: 100")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {failure_count}")
    print(f"   Total Time: {total_time:.2f}s")
    print(f"   Throughput: {100 / total_time:.2f} req/s")

    if latencies:
        print(f"   Avg Latency: {mean(latencies):.3f}s")
        print(f"   P50 Latency: {median(latencies):.3f}s")
        if len(latencies) > 1:
            print(f"   StdDev: {stdev(latencies):.3f}s")

    # Assert all requests succeeded
    assert (
        success_count == 100
    ), f"Expected 100 successful requests, got {success_count}"
    assert failure_count == 0, f"Expected 0 failures, got {failure_count}: {errors[:3]}"

    # Assert latency SLOs
    avg_latency = mean(latencies)
    p50_latency = median(latencies)

    assert (
        avg_latency < 1.0
    ), f"Average latency too high: {avg_latency:.3f}s (threshold: 1.0s)"
    assert (
        p50_latency < 0.5
    ), f"P50 latency too high: {p50_latency:.3f}s (threshold: 0.5s)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_webhook_sequential_vs_parallel_performance(sample_webhook_payload):
    """
    📈 Compare sequential vs parallel request processing to validate
    async benefits and identify potential bottlenecks.
    """
    from observability.ai_agent.webhook_server import app

    n_requests = 20

    # Sequential processing
    sequential_start = time.time()
    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        for _i in range(n_requests):
            await client.post("/webhook/alertmanager", json=sample_webhook_payload)
    sequential_time = time.time() - sequential_start

    # Parallel processing
    parallel_start = time.time()
    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:

        async def send_request(_i: int):
            return await client.post(
                "/webhook/alertmanager", json=sample_webhook_payload
            )

        await asyncio.gather(*[send_request(i) for i in range(n_requests)])
    parallel_time = time.time() - parallel_start

    speedup = sequential_time / parallel_time

    print("\n⚡ Sequential vs Parallel Performance:")
    print(
        f"   Sequential: {sequential_time:.3f}s ({n_requests/sequential_time:.1f} req/s)"
    )
    print(f"   Parallel: {parallel_time:.3f}s ({n_requests/parallel_time:.1f} req/s)")
    print(f"   Speedup: {speedup:.2f}x")

    # Parallel should be faster (at least 2x for async)
    assert (
        speedup >= 2.0
    ), f"Parallel processing should be at least 2x faster, got {speedup:.2f}x"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_webhook_sustained_load(sample_webhook_payload):
    """
    🔄 Test sustained load over multiple waves to check for:
    - Resource leaks
    - Performance degradation over time
    - Stability under continuous load
    """
    from observability.ai_agent.webhook_server import app

    n_waves = 5
    requests_per_wave = 20
    wave_latencies = []

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:
        for wave in range(n_waves):
            wave_start = time.time()

            async def send_request(_i: int):
                req_start = time.time()
                response = await client.post(
                    "/webhook/alertmanager", json=sample_webhook_payload
                )
                return time.time() - req_start, response.status_code

            results = await asyncio.gather(
                *[send_request(i) for i in range(requests_per_wave)]
            )

            wave_time = time.time() - wave_start
            latencies = [r[0] for r in results]
            avg_latency = mean(latencies)

            wave_latencies.append(avg_latency)

            print(
                f"   Wave {wave + 1}: {wave_time:.2f}s, avg latency: {avg_latency:.3f}s"
            )

            # Brief pause between waves
            await asyncio.sleep(0.5)

    # Check for performance degradation
    first_wave_latency = wave_latencies[0]
    last_wave_latency = wave_latencies[-1]

    degradation = (last_wave_latency - first_wave_latency) / first_wave_latency

    print("\n🔍 Sustained Load Analysis:")
    print(f"   First Wave Latency: {first_wave_latency:.3f}s")
    print(f"   Last Wave Latency: {last_wave_latency:.3f}s")
    print(f"   Degradation: {degradation * 100:.1f}%")

    # Assert no significant degradation (allow up to 50% increase)
    assert (
        degradation < 0.5
    ), f"Performance degraded by {degradation * 100:.1f}% (threshold: 50%)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_webhook_error_rate_under_load(sample_webhook_payload):
    """
    ❌ Test error rate remains low under high concurrency.
    Simulates realistic failure scenarios.
    """
    from observability.ai_agent.webhook_server import app

    n_requests = 50
    success_count = 0
    error_count = 0

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:

        async def send_request(i: int):
            try:
                response = await client.post(
                    "/webhook/alertmanager", json=sample_webhook_payload
                )
                return response.status_code in (200, 202)
            except Exception:
                return False

        results = await asyncio.gather(*[send_request(i) for i in range(n_requests)])

    success_count = sum(results)
    error_count = n_requests - success_count
    error_rate = error_count / n_requests

    print("\n📉 Error Rate Analysis:")
    print(f"   Total Requests: {n_requests}")
    print(f"   Successful: {success_count}")
    print(f"   Errors: {error_count}")
    print(f"   Error Rate: {error_rate * 100:.2f}%")

    # Assert error rate below threshold
    assert (
        error_rate < 0.01
    ), f"Error rate too high: {error_rate * 100:.2f}% (threshold: 1%)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_webhook_mixed_payload_sizes(sample_webhook_payload):
    """
    📦 Test performance with varying payload sizes to ensure consistent handling.
    """
    from observability.ai_agent.webhook_server import app

    async with AsyncClient(app=app, base_url="http://test", timeout=30.0) as client:

        async def send_request(alert_count: int):
            payload = sample_webhook_payload.copy()
            # Duplicate alerts to vary payload size
            payload["alerts"] = payload["alerts"] * alert_count

            start = time.time()
            response = await client.post("/webhook/alertmanager", json=payload)
            latency = time.time() - start

            return {
                "alert_count": alert_count,
                "latency": latency,
                "status": response.status_code,
            }

        # Test with 1, 5, 10, 20 alerts per request
        sizes = [1, 5, 10, 20]
        results = await asyncio.gather(*[send_request(size) for size in sizes])

    print("\n📦 Payload Size Impact:")
    for result in results:
        print(
            f"   {result['alert_count']} alerts: {result['latency']:.3f}s (status: {result['status']})"
        )

    # All should succeed
    assert all(r["status"] in (200, 202) for r in results), "Some requests failed"

    # Larger payloads should not cause excessive latency increase
    max_latency = max(r["latency"] for r in results)
    assert (
        max_latency < 2.0
    ), f"Latency too high for large payload: {max_latency:.3f}s (threshold: 2.0s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
