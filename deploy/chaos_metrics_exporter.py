#!/usr/bin/env python3
"""
Chaos Engineering Metrics Exporter
Exports chaos testing metrics to Prometheus for monitoring and alerting.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class ChaosMetricsExporter:
    """Export chaos engineering metrics to Prometheus format."""
    
    def __init__(self, results_file: str = "deploy/chaos_results.json",
                 validation_file: str = "deploy/resilience_validation.json"):
        self.results_file = results_file
        self.validation_file = validation_file
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def load_chaos_results(self) -> Optional[Dict]:
        """Load chaos injection results."""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Chaos results file not found: {self.results_file}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load chaos results: {e}")
            return None
    
    def load_validation_results(self) -> Optional[Dict]:
        """Load resilience validation results."""
        try:
            with open(self.validation_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Validation file not found: {self.validation_file}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to load validation results: {e}")
            return None
    
    def export_to_prometheus(self, output_file: str = "deploy/chaos_metrics.prom") -> bool:
        """Export metrics in Prometheus format."""
        chaos_data = self.load_chaos_results()
        validation_data = self.load_validation_results()
        
        if not chaos_data and not validation_data:
            self.logger.error("No data available to export")
            return False
        
        metrics_lines = []
        
        # Export chaos injection metrics
        if chaos_data:
            metrics_lines.extend(self._export_chaos_metrics(chaos_data))
        
        # Export validation metrics
        if validation_data:
            metrics_lines.extend(self._export_validation_metrics(validation_data))
        
        # Write to file
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write('\n'.join(metrics_lines))
                f.write('\n')
            
            self.logger.info(f"✅ Metrics exported to: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to write metrics file: {e}")
            return False
    
    def _export_chaos_metrics(self, data: Dict) -> list:
        """Export chaos injection metrics."""
        lines = []
        
        # Header
        lines.append("# HELP chaos_scenarios_total Total number of chaos scenarios executed")
        lines.append("# TYPE chaos_scenarios_total counter")
        lines.append(f"chaos_scenarios_total {data.get('total_scenarios', 0)}")
        
        lines.append("# HELP chaos_scenarios_successful Number of successful chaos scenarios")
        lines.append("# TYPE chaos_scenarios_successful counter")
        lines.append(f"chaos_scenarios_successful {data.get('successful', 0)}")
        
        lines.append("# HELP chaos_scenarios_failed Number of failed chaos scenarios")
        lines.append("# TYPE chaos_scenarios_failed counter")
        lines.append(f"chaos_scenarios_failed {data.get('failed', 0)}")
        
        # Export individual scenario results
        lines.append("# HELP chaos_scenario_duration_seconds Duration of chaos scenario execution")
        lines.append("# TYPE chaos_scenario_duration_seconds gauge")
        
        for result in data.get('results', []):
            scenario_name = result.get('scenario_name', 'unknown').replace(' ', '_').lower()
            scenario_type = result.get('scenario_type', 'unknown')
            intensity = result.get('intensity', 'unknown')
            elapsed = result.get('elapsed_time', 0)
            
            labels = f'scenario="{scenario_name}",type="{scenario_type}",intensity="{intensity}"'
            lines.append(f"chaos_scenario_duration_seconds{{{labels}}} {elapsed}")
        
        # Export scenario success status
        lines.append("# HELP chaos_scenario_success Success status of chaos scenario (1=success, 0=failure)")
        lines.append("# TYPE chaos_scenario_success gauge")
        
        for result in data.get('results', []):
            scenario_name = result.get('scenario_name', 'unknown').replace(' ', '_').lower()
            scenario_type = result.get('scenario_type', 'unknown')
            intensity = result.get('intensity', 'unknown')
            success = 1 if result.get('success', False) else 0
            
            labels = f'scenario="{scenario_name}",type="{scenario_type}",intensity="{intensity}"'
            lines.append(f"chaos_scenario_success{{{labels}}} {success}")
        
        return lines
    
    def _export_validation_metrics(self, data: Dict) -> list:
        """Export resilience validation metrics."""
        lines = []
        
        metrics = data.get('metrics', {})
        slo_targets = data.get('slo_targets', {})
        
        # MTTR
        if metrics.get('mttr') is not None:
            lines.append("# HELP chaos_mttr_seconds Mean Time To Recovery in seconds")
            lines.append("# TYPE chaos_mttr_seconds gauge")
            lines.append(f"chaos_mttr_seconds {metrics['mttr']}")
            
            lines.append("# HELP chaos_mttr_target_seconds Target MTTR threshold")
            lines.append("# TYPE chaos_mttr_target_seconds gauge")
            lines.append(f"chaos_mttr_target_seconds {slo_targets.get('mttr_seconds', 30)}")
        
        # Error Rate
        lines.append("# HELP chaos_error_rate_percent Error rate during chaos as percentage")
        lines.append("# TYPE chaos_error_rate_percent gauge")
        lines.append(f"chaos_error_rate_percent {metrics.get('error_rate_percent', 0)}")
        
        lines.append("# HELP chaos_error_rate_target_percent Target error rate threshold")
        lines.append("# TYPE chaos_error_rate_target_percent gauge")
        lines.append(f"chaos_error_rate_target_percent {slo_targets.get('max_error_rate_percent', 5)}")
        
        # Availability
        lines.append("# HELP chaos_availability_percent System availability during chaos")
        lines.append("# TYPE chaos_availability_percent gauge")
        lines.append(f"chaos_availability_percent {metrics.get('availability_percent', 0)}")
        
        lines.append("# HELP chaos_availability_target_percent Target availability threshold")
        lines.append("# TYPE chaos_availability_target_percent gauge")
        lines.append(f"chaos_availability_target_percent {slo_targets.get('min_availability_percent', 95)}")
        
        # Latency
        if metrics.get('baseline_latency_ms') is not None:
            lines.append("# HELP chaos_latency_baseline_ms Baseline latency before chaos")
            lines.append("# TYPE chaos_latency_baseline_ms gauge")
            lines.append(f"chaos_latency_baseline_ms {metrics['baseline_latency_ms']}")
        
        if metrics.get('chaos_latency_ms') is not None:
            lines.append("# HELP chaos_latency_during_ms Latency during chaos injection")
            lines.append("# TYPE chaos_latency_during_ms gauge")
            lines.append(f"chaos_latency_during_ms {metrics['chaos_latency_ms']}")
        
        if metrics.get('post_chaos_latency_ms') is not None:
            lines.append("# HELP chaos_latency_post_ms Latency after chaos recovery")
            lines.append("# TYPE chaos_latency_post_ms gauge")
            lines.append(f"chaos_latency_post_ms {metrics['post_chaos_latency_ms']}")
        
        if metrics.get('latency_degradation_ms') is not None:
            lines.append("# HELP chaos_latency_degradation_ms Latency degradation during chaos")
            lines.append("# TYPE chaos_latency_degradation_ms gauge")
            lines.append(f"chaos_latency_degradation_ms {metrics['latency_degradation_ms']}")
            
            lines.append("# HELP chaos_latency_degradation_target_ms Target latency degradation threshold")
            lines.append("# TYPE chaos_latency_degradation_target_ms gauge")
            lines.append(f"chaos_latency_degradation_target_ms {slo_targets.get('max_latency_degradation_ms', 500)}")
        
        # Recovery Time
        if metrics.get('recovery_time') is not None:
            lines.append("# HELP chaos_recovery_time_seconds Time to full recovery after chaos")
            lines.append("# TYPE chaos_recovery_time_seconds gauge")
            lines.append(f"chaos_recovery_time_seconds {metrics['recovery_time']}")
            
            lines.append("# HELP chaos_recovery_time_target_seconds Target recovery time threshold")
            lines.append("# TYPE chaos_recovery_time_target_seconds gauge")
            lines.append(f"chaos_recovery_time_target_seconds {slo_targets.get('max_recovery_time_seconds', 10)}")
        
        # Uptime/Downtime
        lines.append("# HELP chaos_uptime_seconds System uptime during chaos")
        lines.append("# TYPE chaos_uptime_seconds gauge")
        lines.append(f"chaos_uptime_seconds {metrics.get('uptime_seconds', 0)}")
        
        lines.append("# HELP chaos_downtime_seconds System downtime during chaos")
        lines.append("# TYPE chaos_downtime_seconds gauge")
        lines.append(f"chaos_downtime_seconds {metrics.get('downtime_seconds', 0)}")
        
        # Request counts
        lines.append("# HELP chaos_requests_total Total requests during chaos")
        lines.append("# TYPE chaos_requests_total counter")
        lines.append(f"chaos_requests_total {metrics.get('total_requests', 0)}")
        
        lines.append("# HELP chaos_requests_failed Failed requests during chaos")
        lines.append("# TYPE chaos_requests_failed counter")
        lines.append(f"chaos_requests_failed {metrics.get('failed_requests', 0)}")
        
        # SLO compliance
        lines.append("# HELP chaos_slo_passed SLO validation status (1=passed, 0=failed)")
        lines.append("# TYPE chaos_slo_passed gauge")
        lines.append(f"chaos_slo_passed {1 if data.get('passed', False) else 0}")
        
        lines.append("# HELP chaos_slo_violations_count Number of SLO violations detected")
        lines.append("# TYPE chaos_slo_violations_count gauge")
        lines.append(f"chaos_slo_violations_count {len(data.get('violations', []))}")
        
        # Timestamp
        lines.append("# HELP chaos_test_timestamp_seconds Unix timestamp of chaos test execution")
        lines.append("# TYPE chaos_test_timestamp_seconds gauge")
        timestamp = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())).timestamp()
        lines.append(f"chaos_test_timestamp_seconds {timestamp}")
        
        return lines
    
    def push_to_prometheus(self, pushgateway_url: str, job_name: str = "chaos_engineering") -> bool:
        """Push metrics to Prometheus Pushgateway."""
        try:
            import requests
            
            # Export to temporary file
            temp_file = "/tmp/chaos_metrics.prom"
            if not self.export_to_prometheus(temp_file):
                return False
            
            # Read metrics
            with open(temp_file, 'r') as f:
                metrics_data = f.read()
            
            # Push to pushgateway
            url = f"{pushgateway_url}/metrics/job/{job_name}"
            response = requests.post(url, data=metrics_data, headers={'Content-Type': 'text/plain'})
            
            if response.status_code == 200:
                self.logger.info(f"✅ Metrics pushed to Prometheus: {url}")
                return True
            else:
                self.logger.error(f"Failed to push metrics: {response.status_code} - {response.text}")
                return False
                
        except ImportError:
            self.logger.error("requests library not available. Install with: pip install requests")
            return False
        except Exception as e:
            self.logger.error(f"Failed to push metrics to Prometheus: {e}")
            return False


def main():
    """Main entry point for metrics exporter."""
    parser = argparse.ArgumentParser(
        description="Chaos Engineering Metrics Exporter - Export to Prometheus"
    )
    parser.add_argument("--chaos-results", type=str,
                       default="deploy/chaos_results.json",
                       help="Chaos injection results file")
    parser.add_argument("--validation-results", type=str,
                       default="deploy/resilience_validation.json",
                       help="Resilience validation results file")
    parser.add_argument("--output", type=str,
                       default="deploy/chaos_metrics.prom",
                       help="Output file for Prometheus metrics")
    parser.add_argument("--push", action="store_true",
                       help="Push metrics to Prometheus Pushgateway")
    parser.add_argument("--pushgateway-url", type=str,
                       default="http://localhost:9091",
                       help="Prometheus Pushgateway URL")
    parser.add_argument("--job-name", type=str,
                       default="chaos_engineering",
                       help="Job name for Pushgateway")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create exporter
    exporter = ChaosMetricsExporter(
        results_file=args.chaos_results,
        validation_file=args.validation_results
    )
    
    print("📊 Exporting chaos engineering metrics...")
    
    # Export to file
    if exporter.export_to_prometheus(args.output):
        print(f"✅ Metrics exported to: {args.output}")
        
        # Optionally push to Pushgateway
        if args.push:
            print(f"📤 Pushing metrics to Prometheus Pushgateway...")
            if exporter.push_to_prometheus(args.pushgateway_url, args.job_name):
                print(f"✅ Metrics pushed successfully")
                sys.exit(0)
            else:
                print(f"❌ Failed to push metrics")
                sys.exit(1)
        
        sys.exit(0)
    else:
        print("❌ Failed to export metrics")
        sys.exit(1)


if __name__ == "__main__":
    main()

