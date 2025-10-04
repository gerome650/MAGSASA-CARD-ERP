"""
Runtime Intelligence: ML/Statistical Anomaly Detection Strategies
Stage 6.8 - Advanced anomaly detection for MAGSASA-CARD-ERP

This module implements various anomaly detection algorithms that complement
Prometheus alerting with more sophisticated pattern recognition.
"""

import time
import json
import logging
import statistics
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque
import requests
import numpy as np
from scipy import stats
from threading import Thread, Lock
import schedule

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection analysis"""
    metric_name: str
    current_value: float
    baseline_value: float
    deviation_factor: float
    anomaly_score: float
    is_anomaly: bool
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime
    context: Dict[str, Any]


class EWMAAnomalyDetector:
    """
    Exponentially Weighted Moving Average anomaly detector.
    Good for detecting gradual changes in metrics over time.
    """
    
    def __init__(self, alpha: float = 0.3, threshold: float = 2.0):
        """
        Initialize EWMA detector.
        
        Args:
            alpha: Smoothing factor (0 < alpha < 1), higher = more responsive
            threshold: Standard deviations from mean to consider anomaly
        """
        self.alpha = alpha
        self.threshold = threshold
        self.ewma = None
        self.ewma_var = None
        self.data_points = deque(maxlen=100)  # Keep last 100 points for baseline
        
    def update(self, value: float) -> AnomalyDetectionResult:
        """
        Update the detector with a new value and check for anomalies.
        
        Args:
            value: New metric value
            
        Returns:
            AnomalyDetectionResult if anomaly detected, None otherwise
        """
        self.data_points.append(value)
        
        if self.ewma is None:
            # Initialize with first value
            self.ewma = value
            self.ewma_var = 0.0
            return None
            
        # Update EWMA
        prev_ewma = self.ewma
        self.ewma = self.alpha * value + (1 - self.alpha) * prev_ewma
        
        # Update EWMA variance
        if self.ewma_var is None:
            self.ewma_var = 0.0
        else:
            self.ewma_var = self.alpha * (value - prev_ewma) ** 2 + (1 - self.alpha) * self.ewma_var
        
        # Calculate anomaly score
        if self.ewma_var > 0:
            std_dev = np.sqrt(self.ewma_var)
            anomaly_score = abs(value - self.ewma) / std_dev if std_dev > 0 else 0
        else:
            anomaly_score = 0
            
        is_anomaly = anomaly_score > self.threshold
        
        if is_anomaly:
            severity = self._determine_severity(anomaly_score)
            return AnomalyDetectionResult(
                metric_name="ewma_anomaly",
                current_value=value,
                baseline_value=self.ewma,
                deviation_factor=anomaly_score,
                anomaly_score=anomaly_score,
                is_anomaly=True,
                severity=severity,
                timestamp=datetime.now(),
                context={
                    "alpha": self.alpha,
                    "threshold": self.threshold,
                    "std_dev": std_dev if self.ewma_var > 0 else 0,
                    "data_points": len(self.data_points)
                }
            )
        
        return None
    
    def _determine_severity(self, score: float) -> str:
        """Determine anomaly severity based on score"""
        if score >= 4.0:
            return "critical"
        elif score >= 3.0:
            return "high"
        elif score >= 2.5:
            return "medium"
        else:
            return "low"


class ZScoreAnomalyDetector:
    """
    Z-Score based anomaly detector.
    Good for detecting sudden spikes or drops in metrics.
    """
    
    def __init__(self, window_size: int = 50, threshold: float = 2.5):
        """
        Initialize Z-Score detector.
        
        Args:
            window_size: Number of recent values to use for baseline
            threshold: Z-score threshold for anomaly detection
        """
        self.window_size = window_size
        self.threshold = threshold
        self.values = deque(maxlen=window_size)
        
    def update(self, value: float) -> AnomalyDetectionResult:
        """
        Update detector with new value and check for anomalies.
        
        Args:
            value: New metric value
            
        Returns:
            AnomalyDetectionResult if anomaly detected, None otherwise
        """
        self.values.append(value)
        
        # Need at least 10 values for reliable baseline
        if len(self.values) < 10:
            return None
            
        # Calculate z-score
        mean_val = statistics.mean(self.values)
        std_val = statistics.stdev(self.values) if len(self.values) > 1 else 0
        
        if std_val == 0:
            return None
            
        z_score = abs(value - mean_val) / std_val
        is_anomaly = z_score > self.threshold
        
        if is_anomaly:
            severity = self._determine_severity(z_score)
            return AnomalyDetectionResult(
                metric_name="zscore_anomaly",
                current_value=value,
                baseline_value=mean_val,
                deviation_factor=z_score,
                anomaly_score=z_score,
                is_anomaly=True,
                severity=severity,
                timestamp=datetime.now(),
                context={
                    "window_size": len(self.values),
                    "threshold": self.threshold,
                    "mean": mean_val,
                    "std_dev": std_val
                }
            )
        
        return None
    
    def _determine_severity(self, z_score: float) -> str:
        """Determine anomaly severity based on z-score"""
        if z_score >= 4.0:
            return "critical"
        elif z_score >= 3.5:
            return "high"
        elif z_score >= 3.0:
            return "medium"
        else:
            return "low"


class RollingPercentileDetector:
    """
    Rolling percentile-based anomaly detector.
    Good for detecting tail latency anomalies and distribution changes.
    """
    
    def __init__(self, window_size: int = 100, percentile: float = 95.0, threshold_multiplier: float = 2.0):
        """
        Initialize rolling percentile detector.
        
        Args:
            window_size: Number of values to keep in rolling window
            percentile: Percentile to monitor (e.g., 95.0 for p95)
            threshold_multiplier: Multiple of historical percentile for threshold
        """
        self.window_size = window_size
        self.percentile = percentile
        self.threshold_multiplier = threshold_multiplier
        self.values = deque(maxlen=window_size)
        self.historical_percentiles = deque(maxlen=50)  # Keep last 50 percentile values
        
    def update(self, value: float) -> AnomalyDetectionResult:
        """
        Update detector with new value and check for anomalies.
        
        Args:
            value: New metric value
            
        Returns:
            AnomalyDetectionResult if anomaly detected, None otherwise
        """
        self.values.append(value)
        
        # Need at least 20 values for reliable percentile calculation
        if len(self.values) < 20:
            return None
            
        # Calculate current percentile
        current_percentile = np.percentile(self.values, self.percentile)
        self.historical_percentiles.append(current_percentile)
        
        # Need at least 10 historical percentiles for baseline
        if len(self.historical_percentiles) < 10:
            return None
            
        # Calculate threshold based on historical percentiles
        historical_mean = statistics.mean(self.historical_percentiles)
        threshold = historical_mean * self.threshold_multiplier
        
        # Check if current percentile exceeds threshold
        is_anomaly = current_percentile > threshold
        
        if is_anomaly:
            severity = self._determine_severity(current_percentile, historical_mean)
            return AnomalyDetectionResult(
                metric_name="percentile_anomaly",
                current_value=current_percentile,
                baseline_value=historical_mean,
                deviation_factor=current_percentile / historical_mean,
                anomaly_score=current_percentile / historical_mean,
                is_anomaly=True,
                severity=severity,
                timestamp=datetime.now(),
                context={
                    "percentile": self.percentile,
                    "threshold_multiplier": self.threshold_multiplier,
                    "window_size": len(self.values),
                    "historical_samples": len(self.historical_percentiles),
                    "threshold": threshold
                }
            )
        
        return None
    
    def _determine_severity(self, current: float, baseline: float) -> str:
        """Determine anomaly severity based on ratio to baseline"""
        ratio = current / baseline
        if ratio >= 5.0:
            return "critical"
        elif ratio >= 3.0:
            return "high"
        elif ratio >= 2.5:
            return "medium"
        else:
            return "low"


class RuntimeIntelligenceEngine:
    """
    Main runtime intelligence engine that orchestrates anomaly detection
    and alert routing for the MAGSASA-CARD-ERP system.
    """
    
    def __init__(self, prometheus_url: str = "http://localhost:9090", 
                 alertmanager_url: str = "http://localhost:9093"):
        """
        Initialize the runtime intelligence engine.
        
        Args:
            prometheus_url: Prometheus server URL
            alertmanager_url: Alertmanager webhook URL
        """
        self.prometheus_url = prometheus_url
        self.alertmanager_url = alertmanager_url
        
        # Initialize detectors for different metrics
        self.detectors = {
            "request_rate": ZScoreAnomalyDetector(window_size=50, threshold=2.5),
            "response_time": RollingPercentileDetector(window_size=100, percentile=95.0, threshold_multiplier=2.0),
            "error_rate": EWMAAnomalyDetector(alpha=0.3, threshold=2.0),
            "cpu_usage": EWMAAnomalyDetector(alpha=0.2, threshold=2.5),
            "memory_usage": EWMAAnomalyDetector(alpha=0.2, threshold=2.5),
        }
        
        # Alert suppression to prevent spam
        self.alert_suppression = {}
        self.suppression_lock = Lock()
        
        # Metrics to monitor
        self.metrics_queries = {
            "request_rate": 'sum(rate(http_requests_total[5m]))',
            "response_time": 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))',
            "error_rate": 'sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))',
            "cpu_usage": '1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m]))',
            "memory_usage": '1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)',
        }
        
        logger.info("Runtime Intelligence Engine initialized")
    
    def fetch_metric_value(self, query: str) -> Optional[float]:
        """
        Fetch metric value from Prometheus.
        
        Args:
            query: PromQL query
            
        Returns:
            Metric value or None if error
        """
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
            
        except Exception as e:
            logger.error(f"Error fetching metric {query}: {e}")
            
        return None
    
    def check_anomalies(self) -> List[AnomalyDetectionResult]:
        """
        Check all monitored metrics for anomalies.
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        for metric_name, query in self.metrics_queries.items():
            value = self.fetch_metric_value(query)
            if value is None:
                continue
                
            detector = self.detectors.get(metric_name)
            if detector is None:
                continue
                
            result = detector.update(value)
            if result and result.is_anomaly:
                # Check suppression
                if not self._is_suppressed(metric_name, result.severity):
                    anomalies.append(result)
                    self._suppress_alert(metric_name, result.severity)
                    logger.warning(f"Anomaly detected: {metric_name} = {value}, severity: {result.severity}")
        
        return anomalies
    
    def _is_suppressed(self, metric_name: str, severity: str) -> bool:
        """Check if alert is currently suppressed to prevent spam"""
        with self.suppression_lock:
            key = f"{metric_name}:{severity}"
            if key in self.alert_suppression:
                # Suppress for 10 minutes for critical, 5 minutes for others
                suppress_duration = 600 if severity == "critical" else 300
                if time.time() - self.alert_suppression[key] < suppress_duration:
                    return True
        return False
    
    def _suppress_alert(self, metric_name: str, severity: str):
        """Mark alert as suppressed"""
        with self.suppression_lock:
            key = f"{metric_name}:{severity}"
            self.alert_suppression[key] = time.time()
    
    def send_anomaly_alert(self, anomaly: AnomalyDetectionResult):
        """
        Send anomaly alert to Alertmanager.
        
        Args:
            anomaly: Detected anomaly result
        """
        alert_payload = {
            "labels": {
                "alertname": f"MLAnomaly_{anomaly.metric_name}",
                "severity": anomaly.severity,
                "service": "magsasa-card-erp",
                "team": "backend",
                "category": "ml-anomaly",
                "anomaly_type": anomaly.metric_name,
                "detector": type(anomaly).__name__
            },
            "annotations": {
                "summary": f"🤖 ML Anomaly Detected: {anomaly.metric_name}",
                "description": (
                    f"Anomaly detected in {anomaly.metric_name}: "
                    f"current={anomaly.current_value:.3f}, "
                    f"baseline={anomaly.baseline_value:.3f}, "
                    f"deviation={anomaly.deviation_factor:.2f}x"
                ),
                "current_value": str(anomaly.current_value),
                "baseline_value": str(anomaly.baseline_value),
                "deviation_factor": str(anomaly.deviation_factor),
                "anomaly_score": str(anomaly.anomaly_score),
                "timestamp": anomaly.timestamp.isoformat(),
                "context": json.dumps(anomaly.context)
            },
            "generatorURL": f"{self.prometheus_url}/graph?g0.expr={self.metrics_queries.get(anomaly.metric_name, '')}",
            "startsAt": anomaly.timestamp.isoformat() + "Z"
        }
        
        try:
            response = requests.post(
                f"{self.alertmanager_url}/api/v1/alerts",
                json=[alert_payload],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"Anomaly alert sent: {anomaly.metric_name}")
            
        except Exception as e:
            logger.error(f"Failed to send anomaly alert: {e}")
    
    def run_continuous_monitoring(self):
        """Run continuous anomaly monitoring in a separate thread"""
        def monitor_loop():
            logger.info("Starting continuous anomaly monitoring")
            while True:
                try:
                    anomalies = self.check_anomalies()
                    for anomaly in anomalies:
                        self.send_anomaly_alert(anomaly)
                    
                    # Sleep for 30 seconds between checks
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info("Continuous monitoring thread started")
    
    def get_detector_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all detectors.
        
        Returns:
            Dictionary with detector statistics
        """
        stats = {}
        for name, detector in self.detectors.items():
            if hasattr(detector, 'values'):
                stats[name] = {
                    "type": type(detector).__name__,
                    "data_points": len(detector.values),
                    "current_value": detector.values[-1] if detector.values else None
                }
            elif hasattr(detector, 'data_points'):
                stats[name] = {
                    "type": type(detector).__name__,
                    "data_points": len(detector.data_points),
                    "current_ewma": detector.ewma,
                    "current_var": detector.ewma_var
                }
        
        return stats


# Global instance for easy access
runtime_intelligence = RuntimeIntelligenceEngine()


def start_runtime_intelligence():
    """Start the runtime intelligence monitoring"""
    runtime_intelligence.run_continuous_monitoring()
    logger.info("Runtime Intelligence started")


def get_anomaly_stats():
    """Get current anomaly detection statistics"""
    return runtime_intelligence.get_detector_stats()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Start monitoring
    start_runtime_intelligence()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Runtime Intelligence stopped")
