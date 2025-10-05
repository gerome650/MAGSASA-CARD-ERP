#!/usr/bin/env python3
"""
Load Testing Engine for Backend-v2 Performance Validation
Generates synthetic traffic based on real API usage patterns.
"""

import argparse
import asyncio
import logging
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiohttp
import yaml


@dataclass
class LoadTestConfig:
    """Configuration for load testing parameters."""

    concurrency: int = 100
    duration: int = 300  # seconds
    ramp_up_time: int = 30  # seconds
    target_url: str = "http://localhost:8000"
    endpoints: dict[str, float] = None  # endpoint -> weight
    request_patterns: str = "sustained"  # burst, sustained, ramp-up
    request_timeout: float = 30.0  # seconds
    min_sample_size: int = 100  # minimum requests for valid test

    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {
                "/api/health": 0.1,
                "/api/users": 0.3,
                "/api/orders": 0.25,
                "/api/products": 0.2,
                "/api/analytics": 0.15,
            }


@dataclass
class PerformanceMetrics:
    """Container for performance test results."""

    latencies: list[float]
    errors: int
    total_requests: int
    duration: float
    throughput: float
    error_rate: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    cpu_usage: float | None = None
    memory_usage: float | None = None


class LoadTestEngine:
    """Main load testing engine."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.session = None
        self.results = []
        self.start_time = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        return logging.getLogger(__name__)

    async def _make_request(self, endpoint: str) -> tuple[float, bool]:
        """Make a single HTTP request and return latency and success status."""
        url = f"{self.config.target_url.rstrip('/')}{endpoint}"
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            async with self.session.get(url, timeout=timeout) as response:
                await response.text()
                latency = time.time() - start_time
                success = 200 <= response.status < 400
                return latency, success
        except Exception as e:
            latency = time.time() - start_time
            self.logger.debug(f"Request failed: {e}")
            return latency, False

    def _select_endpoint(self) -> str:
        """Select an endpoint based on configured weights."""
        endpoints = list(self.config.endpoints.keys())
        weights = list(self.config.endpoints.values())
        return random.choices(endpoints, weights=weights)[0]

    async def _worker(self, worker_id: int) -> list[tuple[float, bool]]:
        """Worker coroutine that generates load for the specified duration."""
        results = []
        end_time = self.start_time + self.config.duration

        # Implement ramp-up
        if self.config.request_patterns == "ramp-up":
            ramp_delay = (
                self.config.ramp_up_time / self.config.concurrency
            ) * worker_id
            await asyncio.sleep(ramp_delay)

        while time.time() < end_time:
            endpoint = self._select_endpoint()
            latency, success = await self._make_request(endpoint)
            results.append((latency, success))

            # Implement different request patterns
            if self.config.request_patterns == "burst":
                # Burst pattern: rapid requests followed by pause
                if len(results) % 10 == 0:
                    await asyncio.sleep(random.uniform(0.5, 2.0))
            elif self.config.request_patterns == "sustained":
                # Sustained pattern: consistent rate
                await asyncio.sleep(random.uniform(0.01, 0.1))

        return results

    async def run_load_test(self) -> PerformanceMetrics:
        """Execute the load test with configured parameters."""
        self.logger.info(
            f"Starting load test with {self.config.concurrency} concurrent users"
        )
        self.logger.info(
            f"Target: {self.config.target_url}, Duration: {self.config.duration}s"
        )

        # Create aiohttp session
        connector = aiohttp.TCPConnector(limit=self.config.concurrency * 2)
        self.session = aiohttp.ClientSession(connector=connector)

        try:
            self.start_time = time.time()

            # Create and run worker tasks
            tasks = [self._worker(i) for i in range(self.config.concurrency)]

            worker_results = await asyncio.gather(*tasks)

            # Aggregate results
            all_latencies = []
            total_errors = 0
            total_requests = 0

            for worker_result in worker_results:
                for latency, success in worker_result:
                    all_latencies.append(latency)
                    total_requests += 1
                    if not success:
                        total_errors += 1

            actual_duration = time.time() - self.start_time

            # Validate minimum sample size
            if total_requests < self.config.min_sample_size:
                self.logger.warning(
                    f"Low sample size: {total_requests} requests (minimum: {self.config.min_sample_size})"
                )
                self.logger.warning("Results may not be statistically significant")

            # Calculate metrics
            if (
                all_latencies and len(all_latencies) >= 10
            ):  # Ensure we have enough samples for percentiles
                p50_latency = statistics.median(all_latencies)
                if len(all_latencies) >= 20:
                    p95_latency = statistics.quantiles(all_latencies, n=20)[
                        18
                    ]  # 95th percentile
                else:
                    # Use 95th percentile approximation for small samples
                    p95_latency = sorted(all_latencies)[int(len(all_latencies) * 0.95)]

                if len(all_latencies) >= 100:
                    p99_latency = statistics.quantiles(all_latencies, n=100)[
                        98
                    ]  # 99th percentile
                else:
                    # Use 99th percentile approximation for small samples
                    p99_latency = sorted(all_latencies)[int(len(all_latencies) * 0.99)]
            else:
                p50_latency = p95_latency = p99_latency = 0
                self.logger.warning(
                    "Insufficient data for reliable percentile calculations"
                )

            throughput = total_requests / actual_duration if actual_duration > 0 else 0
            error_rate = (
                (total_errors / total_requests * 100) if total_requests > 0 else 0
            )

            metrics = PerformanceMetrics(
                latencies=all_latencies,
                errors=total_errors,
                total_requests=total_requests,
                duration=actual_duration,
                throughput=throughput,
                error_rate=error_rate,
                p50_latency=p50_latency * 1000,  # Convert to ms
                p95_latency=p95_latency * 1000,
                p99_latency=p99_latency * 1000,
            )

            # Get resource usage if possible
            try:
                metrics.cpu_usage, metrics.memory_usage = self._get_resource_usage()
            except Exception as e:
                self.logger.debug(f"Could not get resource usage: {e}")

            return metrics

        finally:
            await self.session.close()

    def _get_resource_usage(self) -> tuple[float | None, float | None]:
        """Get CPU and memory usage from Docker stats or system metrics."""
        try:
            # Try to get Docker stats first
            import subprocess

            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "table {{.CPUPerc}}\t{{.MemUsage}}",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                if lines:
                    # Parse first container stats
                    parts = lines[0].split("\t")
                    cpu_percent = float(parts[0].rstrip("%"))
                    mem_usage = parts[1].split("/")[0].strip()

                    # Convert memory to MB
                    if "GiB" in mem_usage:
                        memory_mb = float(mem_usage.replace("GiB", "")) * 1024
                    elif "MiB" in mem_usage:
                        memory_mb = float(mem_usage.replace("MiB", ""))
                    else:
                        memory_mb = None

                    return cpu_percent, memory_mb
        except Exception:
            pass

        # Fallback to system monitoring using psutil
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)  # Convert to MB
            return cpu_percent, memory_mb
        except ImportError:
            self.logger.debug("psutil not available for system monitoring")
        except Exception as e:
            self.logger.debug(f"System monitoring failed: {e}")

        # Final fallback - try top command
        try:
            result = subprocess.run(
                ["top", "-l", "1", "-n", "0"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse CPU usage from top output (macOS/Linux)
                lines = result.stdout.split("\n")
                for line in lines:
                    if "CPU usage:" in line or "Cpu(s):" in line:
                        # Extract CPU percentage (simplified parsing)
                        import re

                        cpu_match = re.search(r"(\d+\.?\d*)%", line)
                        if cpu_match:
                            cpu_percent = float(cpu_match.group(1))
                            return cpu_percent, None
        except Exception:
            pass

        return None, None


class PerformanceValidator:
    """Validates performance metrics against SLO thresholds."""

    def __init__(self, config_path: str = "deploy/performance_config.yml"):
        self.config_path = config_path
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> dict:
        """Load performance thresholds from configuration file."""
        default_thresholds = {
            "latency": {"p50": 100, "p95": 250, "p99": 400},  # ms  # ms  # ms
            "error_rate": 0.5,  # %
            "throughput": 1000,  # req/sec
        }

        try:
            if Path(self.config_path).exists():
                with open(self.config_path) as f:
                    config = yaml.safe_load(f)
                    return config.get("thresholds", default_thresholds)
        except Exception as e:
            logging.warning(f"Could not load config from {self.config_path}: {e}")

        return default_thresholds

    def validate_metrics(self, metrics: PerformanceMetrics) -> tuple[bool, list[str]]:
        """Validate metrics against thresholds. Returns (passed, violations)."""
        violations = []

        # Check latency thresholds
        if metrics.p50_latency > self.thresholds["latency"]["p50"]:
            violations.append(
                f"P50 latency {metrics.p50_latency:.1f}ms exceeds threshold "
                f"{self.thresholds['latency']['p50']}ms"
            )

        if metrics.p95_latency > self.thresholds["latency"]["p95"]:
            violations.append(
                f"P95 latency {metrics.p95_latency:.1f}ms exceeds threshold "
                f"{self.thresholds['latency']['p95']}ms"
            )

        if metrics.p99_latency > self.thresholds["latency"]["p99"]:
            violations.append(
                f"P99 latency {metrics.p99_latency:.1f}ms exceeds threshold "
                f"{self.thresholds['latency']['p99']}ms"
            )

        # Check error rate
        if metrics.error_rate > self.thresholds["error_rate"]:
            violations.append(
                f"Error rate {metrics.error_rate:.2f}% exceeds threshold "
                f"{self.thresholds['error_rate']}%"
            )

        # Check throughput (minimum required)
        if metrics.throughput < self.thresholds["throughput"]:
            violations.append(
                f"Throughput {metrics.throughput:.1f} req/sec below threshold "
                f"{self.thresholds['throughput']} req/sec"
            )

        return len(violations) == 0, violations


def generate_performance_report(
    metrics: PerformanceMetrics,
    violations: list[str],
    passed: bool,
    config: LoadTestConfig,
) -> str:
    """Generate a performance test report in Markdown format."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "✅ PASSED" if passed else "❌ FAILED"

    report = f"""# Performance Test Report

**Timestamp:** {timestamp}
**Status:** {status}
**Target:** {config.target_url}
**Duration:** {config.duration}s
**Concurrency:** {config.concurrency}

## Test Results

| Metric | Value | Unit |
|--------|-------|------|
| Total Requests | {metrics.total_requests:,} | requests |
| Duration | {metrics.duration:.1f} | seconds |
| Throughput | {metrics.throughput:.1f} | req/sec |
| Error Rate | {metrics.error_rate:.2f} | % |
| P50 Latency | {metrics.p50_latency:.1f} | ms |
| P95 Latency | {metrics.p95_latency:.1f} | ms |
| P99 Latency | {metrics.p99_latency:.1f} | ms |
"""

    if metrics.cpu_usage is not None:
        report += f"| CPU Usage | {metrics.cpu_usage:.1f} | % |\n"

    if metrics.memory_usage is not None:
        report += f"| Memory Usage | {metrics.memory_usage:.1f} | MB |\n"

    if violations:
        report += "\n## ❌ SLO Violations\n\n"
        for violation in violations:
            report += f"- {violation}\n"
    else:
        report += "\n## ✅ All SLOs Met\n\nNo performance violations detected.\n"

    return report


def export_prometheus_metrics(metrics: PerformanceMetrics, output_file: str = None):
    """Export metrics in Prometheus format."""
    prometheus_metrics = f"""# HELP loadtest_latency_p95 95th percentile latency in milliseconds
# TYPE loadtest_latency_p95 gauge
loadtest_latency_p95 {metrics.p95_latency}

# HELP loadtest_throughput_rps Throughput in requests per second
# TYPE loadtest_throughput_rps gauge
loadtest_throughput_rps {metrics.throughput}

# HELP loadtest_error_rate Error rate as percentage
# TYPE loadtest_error_rate gauge
loadtest_error_rate {metrics.error_rate}

# HELP loadtest_total_requests Total number of requests made
# TYPE loadtest_total_requests counter
loadtest_total_requests {metrics.total_requests}
"""

    if output_file:
        with open(output_file, "w") as f:
            f.write(prometheus_metrics)
    else:
        print(prometheus_metrics)


async def main():
    """Main entry point for the load testing script."""
    parser = argparse.ArgumentParser(description="Load Testing Engine for Backend-v2")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=100,
        help="Number of concurrent users (default: 100)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Test duration in seconds (default: 300)",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="http://localhost:8000",
        help="Target URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--pattern",
        choices=["burst", "sustained", "ramp-up"],
        default="sustained",
        help="Request pattern (default: sustained)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="deploy/performance_config.yml",
        help="Performance config file path",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="deploy/performance_report.md",
        help="Output report file path",
    )
    parser.add_argument(
        "--prometheus-output", type=str, help="Output file for Prometheus metrics"
    )
    parser.add_argument(
        "--fail-on-violation",
        action="store_true",
        help="Exit with non-zero code if SLOs are violated",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: 30.0)",
    )
    parser.add_argument(
        "--min-sample-size",
        type=int,
        default=100,
        help="Minimum sample size for valid test (default: 100)",
    )

    args = parser.parse_args()

    # Create load test configuration
    config = LoadTestConfig(
        concurrency=args.concurrency,
        duration=args.duration,
        target_url=args.target,
        request_patterns=args.pattern,
        request_timeout=args.timeout,
        min_sample_size=args.min_sample_size,
    )

    # Run load test
    engine = LoadTestEngine(config)
    print(f"🚀 Starting load test against {args.target}")

    try:
        metrics = await engine.run_load_test()

        # Validate performance
        validator = PerformanceValidator(args.config)
        passed, violations = validator.validate_metrics(metrics)

        # Generate report
        report = generate_performance_report(metrics, violations, passed, config)

        # Save report
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)

        # Export Prometheus metrics if requested
        if args.prometheus_output:
            export_prometheus_metrics(metrics, args.prometheus_output)

        # Print summary
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\n{status} Load test completed")
        print(f"📊 Throughput: {metrics.throughput:.1f} req/sec")
        print(f"⏱️  P95 Latency: {metrics.p95_latency:.1f}ms")
        print(f"❌ Error Rate: {metrics.error_rate:.2f}%")
        print(f"📄 Report saved to: {args.output}")

        if violations:
            print("\n⚠️  SLO Violations:")
            for violation in violations:
                print(f"   - {violation}")

        # Exit with appropriate code
        if args.fail_on_violation and not passed:
            exit(1)

    except Exception as e:
        print(f"❌ Load test failed: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
