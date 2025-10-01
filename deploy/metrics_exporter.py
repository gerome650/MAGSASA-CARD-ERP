#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for Load Testing Observability
Exports performance metrics to Prometheus for monitoring and alerting.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests


class PrometheusMetricsExporter:
    """Exports load testing metrics to Prometheus."""
    
    def __init__(self, pushgateway_url: Optional[str] = None,
                 job_name: str = "loadtest",
                 instance_name: Optional[str] = None):
        self.pushgateway_url = pushgateway_url or os.getenv('PROMETHEUS_PUSHGATEWAY_URL')
        self.job_name = job_name
        self.instance_name = instance_name or f"loadtest-{int(time.time())}"
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def format_prometheus_metrics(self, metrics_data: Dict, 
                                labels: Optional[Dict[str, str]] = None) -> str:
        """Format metrics data into Prometheus exposition format."""
        if labels is None:
            labels = {}
        
        # Add default labels
        default_labels = {
            'job': self.job_name,
            'instance': self.instance_name,
            'service': 'backend-v2',
            'environment': os.getenv('ENVIRONMENT', 'staging')
        }
        labels.update(default_labels)
        
        # Format labels for Prometheus
        label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
        label_suffix = f'{{{label_str}}}' if label_str else ''
        
        prometheus_metrics = []
        
        # Core performance metrics
        if 'p95_latency' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_latency_p95_ms 95th percentile latency in milliseconds",
                f"# TYPE loadtest_latency_p95_ms gauge",
                f"loadtest_latency_p95_ms{label_suffix} {metrics_data['p95_latency']}"
            ])
        
        if 'p50_latency' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_latency_p50_ms 50th percentile latency in milliseconds",
                f"# TYPE loadtest_latency_p50_ms gauge",
                f"loadtest_latency_p50_ms{label_suffix} {metrics_data['p50_latency']}"
            ])
        
        if 'p99_latency' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_latency_p99_ms 99th percentile latency in milliseconds",
                f"# TYPE loadtest_latency_p99_ms gauge",
                f"loadtest_latency_p99_ms{label_suffix} {metrics_data['p99_latency']}"
            ])
        
        if 'throughput' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_throughput_rps Throughput in requests per second",
                f"# TYPE loadtest_throughput_rps gauge",
                f"loadtest_throughput_rps{label_suffix} {metrics_data['throughput']}"
            ])
        
        if 'error_rate' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_error_rate_percent Error rate as percentage",
                f"# TYPE loadtest_error_rate_percent gauge",
                f"loadtest_error_rate_percent{label_suffix} {metrics_data['error_rate']}"
            ])
        
        if 'total_requests' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_total_requests_count Total number of requests made",
                f"# TYPE loadtest_total_requests_count counter",
                f"loadtest_total_requests_count{label_suffix} {metrics_data['total_requests']}"
            ])
        
        if 'duration' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_duration_seconds Test duration in seconds",
                f"# TYPE loadtest_duration_seconds gauge",
                f"loadtest_duration_seconds{label_suffix} {metrics_data['duration']}"
            ])
        
        # SLO compliance metrics
        if 'slo_violations' in metrics_data:
            prometheus_metrics.extend([
                f"# HELP loadtest_slo_violations_count Number of SLO violations",
                f"# TYPE loadtest_slo_violations_count gauge",
                f"loadtest_slo_violations_count{label_suffix} {len(metrics_data['slo_violations'])}"
            ])
        
        if 'slo_passed' in metrics_data:
            slo_passed_value = 1 if metrics_data['slo_passed'] else 0
            prometheus_metrics.extend([
                f"# HELP loadtest_slo_passed SLO compliance (1=passed, 0=failed)",
                f"# TYPE loadtest_slo_passed gauge",
                f"loadtest_slo_passed{label_suffix} {slo_passed_value}"
            ])
        
        # Resource usage metrics
        if 'cpu_usage' in metrics_data and metrics_data['cpu_usage'] is not None:
            prometheus_metrics.extend([
                f"# HELP loadtest_cpu_usage_percent CPU usage percentage during test",
                f"# TYPE loadtest_cpu_usage_percent gauge",
                f"loadtest_cpu_usage_percent{label_suffix} {metrics_data['cpu_usage']}"
            ])
        
        if 'memory_usage' in metrics_data and metrics_data['memory_usage'] is not None:
            prometheus_metrics.extend([
                f"# HELP loadtest_memory_usage_mb Memory usage in MB during test",
                f"# TYPE loadtest_memory_usage_mb gauge",
                f"loadtest_memory_usage_mb{label_suffix} {metrics_data['memory_usage']}"
            ])
        
        # Test metadata
        prometheus_metrics.extend([
            f"# HELP loadtest_timestamp_seconds Unix timestamp when test was run",
            f"# TYPE loadtest_timestamp_seconds gauge",
            f"loadtest_timestamp_seconds{label_suffix} {int(time.time())}"
        ])
        
        return '\n'.join(prometheus_metrics) + '\n'
    
    def push_metrics(self, metrics_data: Dict, 
                    labels: Optional[Dict[str, str]] = None) -> bool:
        """Push metrics to Prometheus Pushgateway."""
        if not self.pushgateway_url:
            self.logger.warning("No Pushgateway URL configured, skipping metrics push")
            return False
        
        try:
            # Format metrics
            prometheus_data = self.format_prometheus_metrics(metrics_data, labels)
            
            # Construct push URL
            push_url = f"{self.pushgateway_url.rstrip('/')}/metrics/job/{self.job_name}/instance/{self.instance_name}"
            
            # Push to Pushgateway
            response = requests.post(
                push_url,
                data=prometheus_data,
                headers={'Content-Type': 'text/plain'},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Metrics pushed to Prometheus: {push_url}")
                return True
            else:
                self.logger.error(f"❌ Failed to push metrics: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error pushing metrics to Prometheus: {e}")
            return False
    
    def save_metrics_file(self, metrics_data: Dict, 
                         output_path: str,
                         labels: Optional[Dict[str, str]] = None) -> bool:
        """Save metrics to a file in Prometheus format."""
        try:
            prometheus_data = self.format_prometheus_metrics(metrics_data, labels)
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(prometheus_data)
            
            self.logger.info(f"✅ Metrics saved to file: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error saving metrics file: {e}")
            return False


class DeploymentReportManager:
    """Manages deployment reports with performance metrics."""
    
    def __init__(self, report_path: str = "deploy/deployment_report.md"):
        self.report_path = Path(report_path)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def append_performance_results(self, test_type: str, metrics_data: Dict,
                                 slo_violations: List[str], passed: bool,
                                 auto_rollback_triggered: bool = False) -> bool:
        """Append performance test results to deployment report."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "✅ PASSED" if passed else "❌ FAILED"
            
            report_section = f"""
## 📊 {test_type} Performance Results

**Timestamp:** {timestamp}  
**Status:** {status}  
**Auto-rollback Triggered:** {'Yes' if auto_rollback_triggered else 'No'}  

### Performance Metrics

| Metric | Value | Unit |
|--------|-------|------|
| Total Requests | {metrics_data.get('total_requests', 'N/A'):,} | requests |
| Duration | {metrics_data.get('duration', 'N/A'):.1f} | seconds |
| Throughput | {metrics_data.get('throughput', 'N/A'):.1f} | req/sec |
| Error Rate | {metrics_data.get('error_rate', 'N/A'):.2f} | % |
| P50 Latency | {metrics_data.get('p50_latency', 'N/A'):.1f} | ms |
| P95 Latency | {metrics_data.get('p95_latency', 'N/A'):.1f} | ms |
| P99 Latency | {metrics_data.get('p99_latency', 'N/A'):.1f} | ms |
"""
            
            if metrics_data.get('cpu_usage') is not None:
                report_section += f"| CPU Usage | {metrics_data['cpu_usage']:.1f} | % |\n"
            
            if metrics_data.get('memory_usage') is not None:
                report_section += f"| Memory Usage | {metrics_data['memory_usage']:.1f} | MB |\n"
            
            if slo_violations:
                report_section += f"\n### ❌ SLO Violations\n\n"
                for violation in slo_violations:
                    report_section += f"- {violation}\n"
            else:
                report_section += f"\n### ✅ SLO Compliance\n\nAll performance thresholds were met.\n"
            
            # Ensure report directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to report
            if self.report_path.exists():
                with open(self.report_path, 'a') as f:
                    f.write(report_section)
            else:
                with open(self.report_path, 'w') as f:
                    f.write(f"# Deployment Report\n{report_section}")
            
            self.logger.info(f"✅ Performance results appended to {self.report_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error appending to deployment report: {e}")
            return False
    
    def create_summary_report(self, deployment_info: Dict) -> bool:
        """Create a summary deployment report."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            summary = f"""# Deployment Report - Backend-v2

**Generated:** {timestamp}  
**Deployment ID:** {deployment_info.get('deployment_id', 'N/A')}  
**Version:** {deployment_info.get('version', 'N/A')}  
**Environment:** {deployment_info.get('environment', 'N/A')}  
**Pipeline Stage:** Stage 6.4 - Automated Load Simulation & Performance Validation  

## 🎯 Deployment Overview

This report contains the results of automated performance validation for the backend-v2 deployment pipeline. The system includes comprehensive load testing, SLO validation, and auto-rollback capabilities.

### 🔧 Configuration

- **Load Testing:** {'Enabled' if deployment_info.get('load_testing_enabled') else 'Disabled'}
- **Auto-rollback:** {'Enabled' if deployment_info.get('auto_rollback_enabled') else 'Disabled'}
- **Shadow Testing:** {'Enabled' if deployment_info.get('shadow_testing_enabled') else 'Disabled'}
- **Progressive Rollout:** {'Enabled' if deployment_info.get('progressive_rollout_enabled') else 'Disabled'}

---

"""
            
            # Ensure report directory exists
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.report_path, 'w') as f:
                f.write(summary)
            
            self.logger.info(f"✅ Summary report created: {self.report_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating summary report: {e}")
            return False


class AlertManager:
    """Manages alerts and notifications for performance issues."""
    
    def __init__(self):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def send_performance_alert(self, test_type: str, violations: List[str],
                             metrics_data: Dict, rollback_triggered: bool = False) -> bool:
        """Send performance alert notification."""
        if not self.slack_webhook:
            self.logger.warning("No Slack webhook configured, skipping alert")
            return False
        
        try:
            # Prepare alert message
            alert_color = "danger" if violations else "warning"
            alert_title = f"🚨 Performance Alert - {test_type}"
            
            if rollback_triggered:
                alert_title += " (Rollback Triggered)"
            
            # Format violations
            violations_text = "\n".join([f"• {v}" for v in violations]) if violations else "No violations"
            
            # Create Slack message
            slack_message = {
                "attachments": [{
                    "color": alert_color,
                    "title": alert_title,
                    "fields": [
                        {
                            "title": "Environment",
                            "value": os.getenv('ENVIRONMENT', 'staging'),
                            "short": True
                        },
                        {
                            "title": "Test Type",
                            "value": test_type,
                            "short": True
                        },
                        {
                            "title": "P95 Latency",
                            "value": f"{metrics_data.get('p95_latency', 'N/A'):.1f}ms",
                            "short": True
                        },
                        {
                            "title": "Error Rate",
                            "value": f"{metrics_data.get('error_rate', 'N/A'):.2f}%",
                            "short": True
                        },
                        {
                            "title": "SLO Violations",
                            "value": violations_text,
                            "short": False
                        }
                    ],
                    "footer": "Backend-v2 Performance Monitoring",
                    "ts": int(time.time())
                }]
            }
            
            # Send to Slack
            response = requests.post(
                self.slack_webhook,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("✅ Performance alert sent to Slack")
                return True
            else:
                self.logger.error(f"❌ Failed to send Slack alert: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error sending performance alert: {e}")
            return False


def export_metrics_from_file(metrics_file: str, output_file: str = None,
                           pushgateway_url: str = None) -> bool:
    """Export metrics from a JSON file to Prometheus format."""
    try:
        # Load metrics from file
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)
        
        # Create exporter
        exporter = PrometheusMetricsExporter(pushgateway_url=pushgateway_url)
        
        # Export to file if specified
        if output_file:
            success = exporter.save_metrics_file(metrics_data, output_file)
            if not success:
                return False
        
        # Push to Prometheus if configured
        if pushgateway_url:
            success = exporter.push_metrics(metrics_data)
            if not success:
                return False
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error exporting metrics: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export load testing metrics")
    parser.add_argument("--metrics-file", required=True,
                       help="JSON file containing metrics data")
    parser.add_argument("--output-file", 
                       help="Output file for Prometheus metrics")
    parser.add_argument("--pushgateway-url",
                       help="Prometheus Pushgateway URL")
    
    args = parser.parse_args()
    
    success = export_metrics_from_file(
        metrics_file=args.metrics_file,
        output_file=args.output_file,
        pushgateway_url=args.pushgateway_url
    )
    
    exit(0 if success else 1)
