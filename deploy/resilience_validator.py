#!/usr/bin/env python3
"""
Resilience Validator - Stage 6.5
Measures and enforces SLO compliance for chaos engineering tests.
"""

import argparse
import asyncio
import json
import logging
import os
import statistics
import sys
import time
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp


@dataclass
class SLOTargets:
    """SLO target thresholds."""
    mttr_seconds: float = 30.0
    max_error_rate_percent: float = 5.0
    min_availability_percent: float = 95.0
    max_latency_degradation_ms: float = 500.0
    max_recovery_time_seconds: float = 10.0
    required_health_checks: int = 3
    health_check_interval_seconds: float = 2.0


@dataclass
class ResilienceMetrics:
    """Collected resilience metrics."""
    # Recovery metrics
    mttr: Optional[float] = None  # Mean Time To Recovery in seconds
    recovery_time: Optional[float] = None  # Time to full recovery
    
    # Error metrics
    total_requests: int = 0
    failed_requests: int = 0
    error_rate_percent: float = 0.0
    
    # Availability metrics
    uptime_seconds: float = 0.0
    downtime_seconds: float = 0.0
    availability_percent: float = 0.0
    
    # Latency metrics
    baseline_latency_ms: Optional[float] = None
    chaos_latency_ms: Optional[float] = None
    post_chaos_latency_ms: Optional[float] = None
    latency_degradation_ms: Optional[float] = None
    
    # Additional metrics
    health_check_failures: int = 0
    consecutive_successes: int = 0
    first_success_after_chaos: Optional[float] = None


@dataclass
class ValidationResult:
    """Result of SLO validation."""
    passed: bool
    metrics: ResilienceMetrics
    violations: List[str]
    slo_targets: SLOTargets
    timestamp: str
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            'passed': self.passed,
            'timestamp': self.timestamp,
            'slo_targets': asdict(self.slo_targets),
            'metrics': asdict(self.metrics),
            'violations': self.violations
        }


class ResilienceValidator:
    """Validates system resilience against SLO targets."""
    
    def __init__(self, target_url: str = None,
                 config_path: str = "deploy/chaos_scenarios.yml"):
        # Auto-detect target URL if not provided
        if target_url is None:
            target_url = self._auto_detect_target_url()
        
        self.target_url = target_url
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.slo_targets = self._load_slo_targets()
        self.metrics = ResilienceMetrics()
    
    def _auto_detect_target_url(self) -> str:
        """Auto-detect target URL using port detector."""
        import subprocess
        
        # Check environment variables first
        target_url = os.getenv('TARGET_URL')
        if target_url:
            return target_url
        
        chaos_port = os.getenv('CHAOS_TARGET_PORT')
        if chaos_port:
            return f"http://localhost:{chaos_port}"
        
        # Try to use port detector
        try:
            result = subprocess.run([
                'python3', 'deploy/port_detector.py', 
                '--url-only', '--quiet'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                detected_url = result.stdout.strip()
                print(f"🔍 Auto-detected target: {detected_url}")
                return detected_url
        except Exception as e:
            print(f"Warning: Port auto-detection failed: {e}")
        
        # Fallback to default
        fallback_url = "http://localhost:8000"
        print(f"⚠️  Using fallback target: {fallback_url}")
        return fallback_url
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_slo_targets(self) -> SLOTargets:
        """Load SLO targets from configuration file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    targets = config.get('slo_targets', {})
                    recovery = targets.get('recovery', {})
                    
                    return SLOTargets(
                        mttr_seconds=targets.get('mttr_seconds', 30.0),
                        max_error_rate_percent=targets.get('max_error_rate_percent', 5.0),
                        min_availability_percent=targets.get('min_availability_percent', 95.0),
                        max_latency_degradation_ms=targets.get('max_latency_degradation_ms', 500.0),
                        max_recovery_time_seconds=recovery.get('max_recovery_time_seconds', 10.0),
                        required_health_checks=recovery.get('required_health_checks', 3),
                        health_check_interval_seconds=recovery.get('health_check_interval_seconds', 2.0)
                    )
        except Exception as e:
            self.logger.warning(f"Could not load SLO targets from {self.config_path}: {e}")
        
        return SLOTargets()
    
    async def measure_baseline_latency(self, samples: int = 10) -> float:
        """Measure baseline latency before chaos."""
        self.logger.info(f"📊 Measuring baseline latency ({samples} samples)")
        
        latencies = []
        async with aiohttp.ClientSession() as session:
            for i in range(samples):
                try:
                    start = time.time()
                    async with session.get(
                        f"{self.target_url}/api/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        await resp.text()
                        latency = (time.time() - start) * 1000
                        if resp.status == 200:
                            latencies.append(latency)
                except Exception as e:
                    self.logger.debug(f"Baseline measurement failed: {e}")
                
                await asyncio.sleep(0.5)
        
        if latencies:
            baseline = statistics.median(latencies)
            self.metrics.baseline_latency_ms = baseline
            self.logger.info(f"   Baseline latency: {baseline:.1f}ms")
            return baseline
        else:
            self.logger.warning("   Could not establish baseline")
            return 0.0
    
    async def monitor_during_chaos(self, duration: int = 60, 
                                   interval: float = 2.0) -> Dict:
        """Monitor system metrics during chaos injection."""
        self.logger.info(f"🔍 Monitoring system during chaos ({duration}s)")
        
        start_time = time.time()
        end_time = start_time + duration
        
        latencies = []
        failures = 0
        successes = 0
        downtime_start = None
        total_downtime = 0.0
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                check_start = time.time()
                is_available = False
                
                try:
                    async with session.get(
                        f"{self.target_url}/api/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        latency = (time.time() - check_start) * 1000
                        
                        if resp.status == 200:
                            latencies.append(latency)
                            successes += 1
                            is_available = True
                            
                            # If we were down, record downtime
                            if downtime_start is not None:
                                downtime = time.time() - downtime_start
                                total_downtime += downtime
                                downtime_start = None
                        else:
                            failures += 1
                            
                except Exception as e:
                    self.logger.debug(f"Health check failed: {e}")
                    failures += 1
                
                # Track downtime
                if not is_available and downtime_start is None:
                    downtime_start = time.time()
                
                await asyncio.sleep(interval)
        
        # If still down at end, add remaining downtime
        if downtime_start is not None:
            total_downtime += time.time() - downtime_start
        
        # Calculate metrics
        total_checks = successes + failures
        actual_duration = time.time() - start_time
        uptime = actual_duration - total_downtime
        
        self.metrics.total_requests += total_checks
        self.metrics.failed_requests += failures
        self.metrics.error_rate_percent = (failures / total_checks * 100) if total_checks > 0 else 0
        self.metrics.uptime_seconds = uptime
        self.metrics.downtime_seconds = total_downtime
        self.metrics.availability_percent = (uptime / actual_duration * 100) if actual_duration > 0 else 0
        self.metrics.health_check_failures = failures
        
        if latencies:
            self.metrics.chaos_latency_ms = statistics.median(latencies)
        
        self.logger.info(f"   Availability: {self.metrics.availability_percent:.1f}%")
        self.logger.info(f"   Error rate: {self.metrics.error_rate_percent:.1f}%")
        self.logger.info(f"   Downtime: {total_downtime:.1f}s")
        
        return {
            'availability_percent': self.metrics.availability_percent,
            'error_rate_percent': self.metrics.error_rate_percent,
            'downtime_seconds': total_downtime,
            'median_latency_ms': self.metrics.chaos_latency_ms
        }
    
    async def measure_recovery_time(self, max_wait: int = 60) -> float:
        """Measure time for system to recover after chaos."""
        self.logger.info("⏱️  Measuring recovery time")
        
        recovery_start = time.time()
        consecutive_successes = 0
        required_successes = self.slo_targets.required_health_checks
        
        async with aiohttp.ClientSession() as session:
            while time.time() - recovery_start < max_wait:
                try:
                    start = time.time()
                    async with session.get(
                        f"{self.target_url}/api/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        latency = (time.time() - start) * 1000
                        
                        if resp.status == 200:
                            consecutive_successes += 1
                            
                            # Record first success
                            if self.metrics.first_success_after_chaos is None:
                                self.metrics.first_success_after_chaos = time.time() - recovery_start
                            
                            # Check if fully recovered
                            if consecutive_successes >= required_successes:
                                recovery_time = time.time() - recovery_start
                                self.metrics.recovery_time = recovery_time
                                self.metrics.consecutive_successes = consecutive_successes
                                
                                self.logger.info(f"   ✓ System recovered in {recovery_time:.1f}s")
                                return recovery_time
                        else:
                            consecutive_successes = 0
                            
                except Exception as e:
                    self.logger.debug(f"Recovery check failed: {e}")
                    consecutive_successes = 0
                
                await asyncio.sleep(self.slo_targets.health_check_interval_seconds)
        
        # Recovery not achieved
        recovery_time = time.time() - recovery_start
        self.metrics.recovery_time = recovery_time
        self.logger.warning(f"   ⚠️  System did not fully recover within {max_wait}s")
        return recovery_time
    
    async def measure_post_chaos_latency(self, samples: int = 10) -> float:
        """Measure latency after chaos to verify full recovery."""
        self.logger.info(f"📊 Measuring post-chaos latency ({samples} samples)")
        
        latencies = []
        async with aiohttp.ClientSession() as session:
            for i in range(samples):
                try:
                    start = time.time()
                    async with session.get(
                        f"{self.target_url}/api/health",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        await resp.text()
                        latency = (time.time() - start) * 1000
                        if resp.status == 200:
                            latencies.append(latency)
                except Exception as e:
                    self.logger.debug(f"Post-chaos measurement failed: {e}")
                
                await asyncio.sleep(0.5)
        
        if latencies:
            post_latency = statistics.median(latencies)
            self.metrics.post_chaos_latency_ms = post_latency
            
            # Calculate degradation
            if self.metrics.baseline_latency_ms:
                self.metrics.latency_degradation_ms = post_latency - self.metrics.baseline_latency_ms
            
            self.logger.info(f"   Post-chaos latency: {post_latency:.1f}ms")
            return post_latency
        else:
            self.logger.warning("   Could not measure post-chaos latency")
            return 0.0
    
    def calculate_mttr(self, chaos_results_file: str = "deploy/chaos_results.json") -> Optional[float]:
        """Calculate Mean Time To Recovery from chaos test results."""
        try:
            with open(chaos_results_file, 'r') as f:
                results = json.load(f)
            
            recovery_times = []
            
            for result in results.get('results', []):
                metrics = result.get('metrics', {})
                
                # Check if service recovered
                if metrics.get('service_available', False):
                    # Estimate recovery time based on scenario duration
                    # This is a simplified calculation
                    duration = result.get('duration', 0)
                    recovery_times.append(duration)
            
            if recovery_times:
                mttr = statistics.mean(recovery_times)
                self.metrics.mttr = mttr
                self.logger.info(f"📈 Calculated MTTR: {mttr:.1f}s")
                return mttr
            
        except Exception as e:
            self.logger.warning(f"Could not calculate MTTR: {e}")
        
        return None
    
    def validate_slos(self) -> ValidationResult:
        """Validate metrics against SLO targets."""
        self.logger.info("\n🎯 Validating SLO compliance")
        
        violations = []
        
        # Validate MTTR
        if self.metrics.mttr is not None:
            if self.metrics.mttr > self.slo_targets.mttr_seconds:
                violations.append(
                    f"MTTR {self.metrics.mttr:.1f}s exceeds target "
                    f"{self.slo_targets.mttr_seconds:.1f}s"
                )
            self.logger.info(f"   MTTR: {self.metrics.mttr:.1f}s / {self.slo_targets.mttr_seconds:.1f}s target")
        
        # Validate recovery time
        if self.metrics.recovery_time is not None:
            if self.metrics.recovery_time > self.slo_targets.max_recovery_time_seconds:
                violations.append(
                    f"Recovery time {self.metrics.recovery_time:.1f}s exceeds target "
                    f"{self.slo_targets.max_recovery_time_seconds:.1f}s"
                )
            self.logger.info(
                f"   Recovery time: {self.metrics.recovery_time:.1f}s / "
                f"{self.slo_targets.max_recovery_time_seconds:.1f}s target"
            )
        
        # Validate error rate
        if self.metrics.error_rate_percent > self.slo_targets.max_error_rate_percent:
            violations.append(
                f"Error rate {self.metrics.error_rate_percent:.1f}% exceeds target "
                f"{self.slo_targets.max_error_rate_percent:.1f}%"
            )
        self.logger.info(
            f"   Error rate: {self.metrics.error_rate_percent:.1f}% / "
            f"{self.slo_targets.max_error_rate_percent:.1f}% target"
        )
        
        # Validate availability
        if self.metrics.availability_percent < self.slo_targets.min_availability_percent:
            violations.append(
                f"Availability {self.metrics.availability_percent:.1f}% below target "
                f"{self.slo_targets.min_availability_percent:.1f}%"
            )
        self.logger.info(
            f"   Availability: {self.metrics.availability_percent:.1f}% / "
            f"{self.slo_targets.min_availability_percent:.1f}% target"
        )
        
        # Validate latency degradation
        if self.metrics.latency_degradation_ms is not None:
            if self.metrics.latency_degradation_ms > self.slo_targets.max_latency_degradation_ms:
                violations.append(
                    f"Latency degradation {self.metrics.latency_degradation_ms:.1f}ms exceeds target "
                    f"{self.slo_targets.max_latency_degradation_ms:.1f}ms"
                )
            self.logger.info(
                f"   Latency degradation: {self.metrics.latency_degradation_ms:.1f}ms / "
                f"{self.slo_targets.max_latency_degradation_ms:.1f}ms target"
            )
        
        passed = len(violations) == 0
        
        result = ValidationResult(
            passed=passed,
            metrics=self.metrics,
            violations=violations,
            slo_targets=self.slo_targets,
            timestamp=datetime.now().isoformat()
        )
        
        if passed:
            self.logger.info("\n✅ All SLOs met!")
        else:
            self.logger.error(f"\n❌ {len(violations)} SLO violation(s) detected")
        
        return result
    
    def save_validation_results(self, result: ValidationResult, 
                                output_file: str = "deploy/resilience_validation.json"):
        """Save validation results to file."""
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            self.logger.info(f"📊 Validation results saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation results: {e}")
    
    def generate_report(self, result: ValidationResult, 
                       output_file: str = "deploy/chaos_report.md") -> str:
        """Generate markdown report of resilience validation."""
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        
        report = f"""# Chaos Engineering Resilience Report

**Timestamp:** {result.timestamp}  
**Status:** {status}  
**Target:** {self.target_url}  

## SLO Validation Summary

| Metric | Measured | Target | Status |
|--------|----------|--------|--------|
"""
        
        # MTTR
        if result.metrics.mttr is not None:
            mttr_status = "✅" if result.metrics.mttr <= result.slo_targets.mttr_seconds else "❌"
            report += f"| MTTR | {result.metrics.mttr:.1f}s | {result.slo_targets.mttr_seconds:.1f}s | {mttr_status} |\n"
        
        # Recovery Time
        if result.metrics.recovery_time is not None:
            recovery_status = "✅" if result.metrics.recovery_time <= result.slo_targets.max_recovery_time_seconds else "❌"
            report += f"| Recovery Time | {result.metrics.recovery_time:.1f}s | {result.slo_targets.max_recovery_time_seconds:.1f}s | {recovery_status} |\n"
        
        # Error Rate
        error_status = "✅" if result.metrics.error_rate_percent <= result.slo_targets.max_error_rate_percent else "❌"
        report += f"| Error Rate | {result.metrics.error_rate_percent:.1f}% | {result.slo_targets.max_error_rate_percent:.1f}% | {error_status} |\n"
        
        # Availability
        avail_status = "✅" if result.metrics.availability_percent >= result.slo_targets.min_availability_percent else "❌"
        report += f"| Availability | {result.metrics.availability_percent:.1f}% | {result.slo_targets.min_availability_percent:.1f}% | {avail_status} |\n"
        
        # Latency Degradation
        if result.metrics.latency_degradation_ms is not None:
            latency_status = "✅" if result.metrics.latency_degradation_ms <= result.slo_targets.max_latency_degradation_ms else "❌"
            report += f"| Latency Degradation | {result.metrics.latency_degradation_ms:.1f}ms | {result.slo_targets.max_latency_degradation_ms:.1f}ms | {latency_status} |\n"
        
        # Detailed Metrics
        baseline_latency = result.metrics.baseline_latency_ms or 0
        chaos_latency = result.metrics.chaos_latency_ms or 0
        post_chaos_latency = result.metrics.post_chaos_latency_ms or 0
        degradation = result.metrics.latency_degradation_ms or 0
        
        report += f"""
## Detailed Metrics

### Latency Analysis
- **Baseline Latency:** {baseline_latency:.1f}ms
- **Chaos Latency:** {chaos_latency:.1f}ms
- **Post-Chaos Latency:** {post_chaos_latency:.1f}ms
- **Degradation:** {degradation:.1f}ms

### Availability Analysis
- **Uptime:** {result.metrics.uptime_seconds:.1f}s
- **Downtime:** {result.metrics.downtime_seconds:.1f}s
- **Availability:** {result.metrics.availability_percent:.1f}%

### Error Analysis
- **Total Requests:** {result.metrics.total_requests}
- **Failed Requests:** {result.metrics.failed_requests}
- **Error Rate:** {result.metrics.error_rate_percent:.2f}%
- **Health Check Failures:** {result.metrics.health_check_failures}

### Recovery Analysis
- **First Success After Chaos:** {result.metrics.first_success_after_chaos or 0:.1f}s
- **Full Recovery Time:** {result.metrics.recovery_time or 0:.1f}s
- **Consecutive Successes:** {result.metrics.consecutive_successes}
"""
        
        # Violations
        if result.violations:
            report += "\n## ❌ SLO Violations\n\n"
            for violation in result.violations:
                report += f"- {violation}\n"
        else:
            report += "\n## ✅ All SLOs Met\n\nNo violations detected. System demonstrates excellent resilience.\n"
        
        # Recommendations
        report += "\n## Recommendations\n\n"
        
        if result.passed:
            report += "- ✅ System shows good resilience characteristics\n"
            report += "- Continue monitoring in production\n"
            report += "- Consider increasing chaos intensity for future tests\n"
        else:
            report += "### Priority Actions\n\n"
            
            if result.metrics.mttr and result.metrics.mttr > result.slo_targets.mttr_seconds:
                report += "- **Improve Recovery Time:** Implement faster failure detection and automated recovery\n"
            
            if result.metrics.error_rate_percent > result.slo_targets.max_error_rate_percent:
                report += "- **Reduce Error Rate:** Add circuit breakers and better error handling\n"
            
            if result.metrics.availability_percent < result.slo_targets.min_availability_percent:
                report += "- **Increase Availability:** Implement redundancy and failover mechanisms\n"
            
            if result.metrics.latency_degradation_ms and result.metrics.latency_degradation_ms > result.slo_targets.max_latency_degradation_ms:
                report += "- **Optimize Performance:** Reduce degradation under stress with caching and load balancing\n"
        
        # Save report
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
            self.logger.info(f"📄 Report saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")
        
        return report


async def main():
    """Main entry point for resilience validator."""
    parser = argparse.ArgumentParser(
        description="Resilience Validator - Stage 6.5"
    )
    parser.add_argument("--target", type=str,
                       default=None,
                       help="Target service URL (auto-detected if not provided)")
    parser.add_argument("--config", type=str,
                       default="deploy/chaos_scenarios.yml",
                       help="Chaos scenarios configuration file")
    parser.add_argument("--chaos-results", type=str,
                       default="deploy/chaos_results.json",
                       help="Chaos injection results file")
    parser.add_argument("--output", type=str,
                       default="deploy/resilience_validation.json",
                       help="Output file for validation results")
    parser.add_argument("--report", type=str,
                       default="deploy/chaos_report.md",
                       help="Output file for markdown report")
    parser.add_argument("--monitor-duration", type=int, default=60,
                       help="Duration to monitor during chaos (seconds)")
    parser.add_argument("--baseline-samples", type=int, default=10,
                       help="Number of samples for baseline measurement")
    parser.add_argument("--fail-on-violation", action="store_true",
                       help="Exit with non-zero code if SLOs are violated")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create validator
    validator = ResilienceValidator(
        target_url=args.target,
        config_path=args.config
    )
    
    print(f"🧪 Starting resilience validation")
    print(f"Target: {args.target}")
    
    try:
        # Measure baseline
        await validator.measure_baseline_latency(samples=args.baseline_samples)
        
        # Monitor during chaos (if currently running)
        # In practice, this would be called during actual chaos injection
        # await validator.monitor_during_chaos(duration=args.monitor_duration)
        
        # Measure recovery
        await validator.measure_recovery_time()
        
        # Measure post-chaos latency
        await validator.measure_post_chaos_latency(samples=args.baseline_samples)
        
        # Calculate MTTR from chaos results
        validator.calculate_mttr(args.chaos_results)
        
        # Validate SLOs
        result = validator.validate_slos()
        
        # Save results
        validator.save_validation_results(result, args.output)
        
        # Generate report
        validator.generate_report(result, args.report)
        
        # Print summary
        print(f"\n{'='*60}")
        print("🎯 Resilience Validation Summary")
        print(f"{'='*60}")
        
        status = "✅ PASSED" if result.passed else "❌ FAILED"
        print(f"Status: {status}")
        print(f"Violations: {len(result.violations)}")
        print(f"📊 Results: {args.output}")
        print(f"📄 Report: {args.report}")
        
        if result.violations:
            print(f"\n⚠️  SLO Violations:")
            for violation in result.violations:
                print(f"   - {violation}")
        
        # Exit with appropriate code
        if args.fail_on_violation and not result.passed:
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

