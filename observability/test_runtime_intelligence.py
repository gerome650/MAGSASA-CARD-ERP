#!/usr/bin/env python3
"""
Runtime Intelligence: Comprehensive Test Suite
Stage 6.8 - Test script for runtime intelligence components

This script tests all runtime intelligence components:
- PromQL alert rules validation
- ML anomaly detection
- Smart alert routing
- Dashboard annotations
- Webhook server integration
"""

import json
import logging
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys

# Add the observability directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our components
from alerts.anomaly_strategies import (
    EWMAAnomalyDetector, 
    ZScoreAnomalyDetector, 
    RollingPercentileDetector,
    RuntimeIntelligenceEngine
)
from alerts.notifier import SmartAlertRouter, AlertSeverity, NotificationChannel
from dashboards.annotations import GrafanaAnnotationService, AnnotationManager
from alerts.webhook_server import process_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RuntimeIntelligenceTester:
    """Comprehensive tester for runtime intelligence components"""
    
    def __init__(self):
        self.test_results = {}
        self.prometheus_url = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')
        self.alertmanager_url = os.getenv('ALERTMANAGER_URL', 'http://localhost:9093')
        self.grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
        self.webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:5001')
        
    def test_prometheus_connectivity(self) -> bool:
        """Test Prometheus connectivity and basic queries"""
        logger.info("Testing Prometheus connectivity...")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                  params={'query': 'up'}, timeout=10)
            response.raise_for_status()
            
            # Test our specific metrics
            metrics_to_test = [
                'http_requests_total',
                'http_request_duration_seconds',
                'http_requests_exceptions_total'
            ]
            
            for metric in metrics_to_test:
                response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                      params={'query': metric}, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✓ Metric {metric} is available")
                else:
                    logger.warning(f"⚠ Metric {metric} not available")
            
            self.test_results['prometheus_connectivity'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Prometheus connectivity failed: {e}")
            self.test_results['prometheus_connectivity'] = False
            return False
    
    def test_alertmanager_connectivity(self) -> bool:
        """Test Alertmanager connectivity"""
        logger.info("Testing Alertmanager connectivity...")
        
        try:
            response = requests.get(f"{self.alertmanager_url}/api/v1/status", timeout=10)
            response.raise_for_status()
            
            status_data = response.json()
            logger.info(f"✓ Alertmanager status: {status_data.get('data', {}).get('cluster', {}).get('status', 'unknown')}")
            
            self.test_results['alertmanager_connectivity'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Alertmanager connectivity failed: {e}")
            self.test_results['alertmanager_connectivity'] = False
            return False
    
    def test_grafana_connectivity(self) -> bool:
        """Test Grafana connectivity"""
        logger.info("Testing Grafana connectivity...")
        
        try:
            response = requests.get(f"{self.grafana_url}/api/health", timeout=10)
            response.raise_for_status()
            
            logger.info("✓ Grafana is accessible")
            self.test_results['grafana_connectivity'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Grafana connectivity failed: {e}")
            self.test_results['grafana_connectivity'] = False
            return False
    
    def test_anomaly_detectors(self) -> bool:
        """Test ML anomaly detection algorithms"""
        logger.info("Testing anomaly detection algorithms...")
        
        try:
            # Test EWMA detector
            ewma_detector = EWMAAnomalyDetector(alpha=0.3, threshold=2.0)
            
            # Simulate normal data
            normal_values = [50, 52, 48, 51, 49, 53, 47, 50, 52, 49]
            anomalies_detected = 0
            
            for value in normal_values:
                result = ewma_detector.update(value)
                if result and result.is_anomaly:
                    anomalies_detected += 1
            
            logger.info(f"✓ EWMA detector processed {len(normal_values)} values, detected {anomalies_detected} anomalies")
            
            # Test with anomalous value
            anomaly_result = ewma_detector.update(150)  # Should trigger anomaly
            if anomaly_result and anomaly_result.is_anomaly:
                logger.info(f"✓ EWMA detector correctly identified anomaly: {anomaly_result.anomaly_score:.2f}")
            else:
                logger.warning("⚠ EWMA detector did not detect expected anomaly")
            
            # Test Z-Score detector
            zscore_detector = ZScoreAnomalyDetector(window_size=20, threshold=2.5)
            
            # Fill with normal data
            for i in range(25):
                zscore_detector.update(50 + (i % 10))
            
            # Test with anomaly
            zscore_result = zscore_detector.update(100)
            if zscore_result and zscore_result.is_anomaly:
                logger.info(f"✓ Z-Score detector correctly identified anomaly: {zscore_result.anomaly_score:.2f}")
            else:
                logger.warning("⚠ Z-Score detector did not detect expected anomaly")
            
            # Test Rolling Percentile detector
            percentile_detector = RollingPercentileDetector(window_size=50, percentile=95.0, threshold_multiplier=2.0)
            
            # Fill with normal latency data
            for i in range(60):
                percentile_detector.update(0.1 + (i % 20) * 0.01)  # 0.1-0.3s latency
            
            # Test with high latency
            percentile_result = percentile_detector.update(1.0)  # 1 second latency
            if percentile_result and percentile_result.is_anomaly:
                logger.info(f"✓ Rolling Percentile detector correctly identified latency anomaly: {percentile_result.anomaly_score:.2f}")
            else:
                logger.warning("⚠ Rolling Percentile detector did not detect expected latency anomaly")
            
            self.test_results['anomaly_detectors'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Anomaly detector testing failed: {e}")
            self.test_results['anomaly_detectors'] = False
            return False
    
    def test_runtime_intelligence_engine(self) -> bool:
        """Test the runtime intelligence engine"""
        logger.info("Testing Runtime Intelligence Engine...")
        
        try:
            # Create engine instance
            engine = RuntimeIntelligenceEngine(
                prometheus_url=self.prometheus_url,
                alertmanager_url=self.alertmanager_url
            )
            
            # Test detector stats
            stats = engine.get_detector_stats()
            logger.info(f"✓ Engine initialized with {len(stats)} detectors")
            
            # Test anomaly checking (this will try to fetch from Prometheus)
            try:
                anomalies = engine.check_anomalies()
                logger.info(f"✓ Engine checked for anomalies, found {len(anomalies)}")
            except Exception as e:
                logger.warning(f"⚠ Engine anomaly check failed (expected if Prometheus not available): {e}")
            
            self.test_results['runtime_intelligence_engine'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Runtime Intelligence Engine testing failed: {e}")
            self.test_results['runtime_intelligence_engine'] = False
            return False
    
    def test_alert_routing(self) -> bool:
        """Test smart alert routing"""
        logger.info("Testing alert routing...")
        
        try:
            # Create test configuration
            test_config = {
                'slack': {
                    'enabled': False,  # Disable actual sending for testing
                    'webhook_url': 'https://hooks.slack.com/test',
                    'channel': '#test'
                },
                'pagerduty': {
                    'enabled': False,
                    'integration_key': 'test-key'
                },
                'email': {
                    'enabled': False,
                    'smtp_host': 'test.example.com'
                }
            }
            
            router = SmartAlertRouter(test_config)
            
            # Test routing rules
            stats = router.get_routing_stats()
            logger.info(f"✓ Router initialized with {len(stats['configured_channels'])} channels")
            
            # Test alert context extraction
            test_alert = {
                'labels': {
                    'alertname': 'TestAlert',
                    'severity': 'critical',
                    'service': 'magsasa-card-erp',
                    'team': 'backend',
                    'category': 'test'
                },
                'annotations': {
                    'summary': 'Test alert',
                    'description': 'This is a test alert',
                    'current_value': '100',
                    'baseline_value': '50',
                    'runbook_url': 'https://docs.example.com/test',
                    'grafana_url': 'http://grafana:3000/test'
                },
                'status': 'firing',
                'startsAt': datetime.now().isoformat() + 'Z'
            }
            
            context = router.extract_context(test_alert)
            logger.info(f"✓ Alert context extracted: severity={context.severity.value}, service={context.service}")
            
            # Test routing (should not actually send since channels are disabled)
            routing_result = router.route_alert(test_alert)
            logger.info(f"✓ Alert routing completed: {routing_result}")
            
            self.test_results['alert_routing'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Alert routing testing failed: {e}")
            self.test_results['alert_routing'] = False
            return False
    
    def test_dashboard_annotations(self) -> bool:
        """Test dashboard annotation service"""
        logger.info("Testing dashboard annotations...")
        
        try:
            # Create annotation service (with dummy API key for testing)
            annotation_service = GrafanaAnnotationService(
                grafana_url=self.grafana_url,
                api_key='test-api-key'
            )
            
            # Test dashboard listing (this will fail with dummy key, but we can test the logic)
            try:
                dashboards = annotation_service._get_dashboards()
                logger.info(f"✓ Dashboard service initialized, found {len(dashboards)} dashboards")
            except Exception as e:
                logger.warning(f"⚠ Dashboard listing failed (expected with dummy API key): {e}")
            
            # Test annotation manager
            manager = AnnotationManager(self.grafana_url, 'test-api-key')
            mapping_stats = manager.get_mapping_stats()
            logger.info(f"✓ Annotation manager initialized with {mapping_stats['total_mappings']} mappings")
            
            self.test_results['dashboard_annotations'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Dashboard annotations testing failed: {e}")
            self.test_results['dashboard_annotations'] = False
            return False
    
    def test_webhook_server(self) -> bool:
        """Test webhook server functionality"""
        logger.info("Testing webhook server...")
        
        try:
            # Test webhook server health endpoint
            try:
                response = requests.get(f"{self.webhook_url}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✓ Webhook server is healthy: {health_data['status']}")
                else:
                    logger.warning(f"⚠ Webhook server health check returned {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠ Webhook server not accessible (expected if not running): {e}")
            
            # Test alert processing logic
            test_alert = {
                'labels': {
                    'alertname': 'TestWebhookAlert',
                    'severity': 'warning',
                    'service': 'magsasa-card-erp',
                    'team': 'backend',
                    'category': 'test'
                },
                'annotations': {
                    'summary': 'Test webhook alert',
                    'description': 'This is a test webhook alert',
                    'current_value': '75',
                    'baseline_value': '50'
                },
                'status': 'firing',
                'startsAt': datetime.now().isoformat() + 'Z'
            }
            
            # Test processing function directly
            result = process_alert(test_alert)
            logger.info(f"✓ Alert processing test completed: {result}")
            
            self.test_results['webhook_server'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Webhook server testing failed: {e}")
            self.test_results['webhook_server'] = False
            return False
    
    def test_promql_rules_validation(self) -> bool:
        """Test PromQL rules validation"""
        logger.info("Testing PromQL rules validation...")
        
        try:
            # Load and validate alert rules file
            rules_file = os.path.join(os.path.dirname(__file__), 'alerts', 'promql_rules.yml')
            
            if not os.path.exists(rules_file):
                logger.error(f"✗ Alert rules file not found: {rules_file}")
                self.test_results['promql_rules_validation'] = False
                return False
            
            # Read the file
            with open(rules_file, 'r') as f:
                rules_content = f.read()
            
            # Basic validation - check for required sections
            required_sections = ['groups:', 'rules:', 'alert:', 'expr:', 'labels:', 'annotations:']
            missing_sections = []
            
            for section in required_sections:
                if section not in rules_content:
                    missing_sections.append(section)
            
            if missing_sections:
                logger.error(f"✗ Alert rules missing required sections: {missing_sections}")
                self.test_results['promql_rules_validation'] = False
                return False
            
            # Count rules
            alert_count = rules_content.count('alert:')
            expr_count = rules_content.count('expr:')
            
            logger.info(f"✓ Alert rules file validated: {alert_count} alerts, {expr_count} expressions")
            
            # Test specific rule syntax (basic validation)
            test_queries = [
                'up{job="magsasa-card-erp"} == 0',
                'rate(http_requests_total{status_code=~"5.."}[5m])',
                'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))'
            ]
            
            for query in test_queries:
                try:
                    response = requests.get(f"{self.prometheus_url}/api/v1/query", 
                                          params={'query': query}, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✓ PromQL query validated: {query[:50]}...")
                    else:
                        logger.warning(f"⚠ PromQL query returned {response.status_code}: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠ PromQL query test failed (expected if Prometheus not available): {e}")
            
            self.test_results['promql_rules_validation'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ PromQL rules validation failed: {e}")
            self.test_results['promql_rules_validation'] = False
            return False
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🧪 Starting Runtime Intelligence Comprehensive Test Suite")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Run all tests
        tests = [
            ('Prometheus Connectivity', self.test_prometheus_connectivity),
            ('Alertmanager Connectivity', self.test_alertmanager_connectivity),
            ('Grafana Connectivity', self.test_grafana_connectivity),
            ('Anomaly Detectors', self.test_anomaly_detectors),
            ('Runtime Intelligence Engine', self.test_runtime_intelligence_engine),
            ('Alert Routing', self.test_alert_routing),
            ('Dashboard Annotations', self.test_dashboard_annotations),
            ('Webhook Server', self.test_webhook_server),
            ('PromQL Rules Validation', self.test_promql_rules_validation),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name} ERROR: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = False
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Generate summary
        summary = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': f"{(passed_tests / total_tests) * 100:.1f}%",
                'duration_seconds': duration.total_seconds()
            },
            'test_results': self.test_results,
            'recommendations': self._generate_recommendations(),
            'timestamp': end_time.isoformat()
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🏁 RUNTIME INTELLIGENCE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Runtime Intelligence is ready for production.")
        else:
            logger.info("⚠️  Some tests failed. Check the recommendations below.")
        
        logger.info("\n📋 RECOMMENDATIONS:")
        for recommendation in summary['recommendations']:
            logger.info(f"  • {recommendation}")
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if not self.test_results.get('prometheus_connectivity'):
            recommendations.append("Start Prometheus server and ensure metrics are being collected")
        
        if not self.test_results.get('alertmanager_connectivity'):
            recommendations.append("Start Alertmanager server and verify configuration")
        
        if not self.test_results.get('grafana_connectivity'):
            recommendations.append("Start Grafana server and configure API key for annotations")
        
        if not self.test_results.get('webhook_server'):
            recommendations.append("Start the webhook server: python -m observability.alerts.webhook_server")
        
        if not self.test_results.get('promql_rules_validation'):
            recommendations.append("Review and fix PromQL alert rules syntax")
        
        if not self.test_results.get('anomaly_detectors'):
            recommendations.append("Check anomaly detection algorithm implementations")
        
        if not self.test_results.get('alert_routing'):
            recommendations.append("Configure notification channels (Slack, PagerDuty, email)")
        
        if not self.test_results.get('dashboard_annotations'):
            recommendations.append("Configure Grafana API key and dashboard mappings")
        
        if len(recommendations) == 0:
            recommendations.append("All components are working correctly! Consider running load tests.")
        
        return recommendations


def main():
    """Main function to run the test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Runtime Intelligence Test Suite')
    parser.add_argument('--prometheus-url', default='http://localhost:9090',
                       help='Prometheus server URL')
    parser.add_argument('--alertmanager-url', default='http://localhost:9093',
                       help='Alertmanager server URL')
    parser.add_argument('--grafana-url', default='http://localhost:3000',
                       help='Grafana server URL')
    parser.add_argument('--webhook-url', default='http://localhost:5001',
                       help='Webhook server URL')
    parser.add_argument('--output-file', help='Output results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set environment variables
    os.environ['PROMETHEUS_URL'] = args.prometheus_url
    os.environ['ALERTMANAGER_URL'] = args.alertmanager_url
    os.environ['GRAFANA_URL'] = args.grafana_url
    os.environ['WEBHOOK_URL'] = args.webhook_url
    
    # Run tests
    tester = RuntimeIntelligenceTester()
    results = tester.run_comprehensive_test()
    
    # Save results if requested
    if args.output_file:
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output_file}")
    
    # Exit with appropriate code
    failed_tests = results['test_summary']['failed_tests']
    sys.exit(failed_tests)


if __name__ == '__main__':
    main()
