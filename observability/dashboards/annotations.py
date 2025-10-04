"""
Runtime Intelligence: Automatic Dashboard Annotations Service
Stage 6.8 - Auto-annotation service for Grafana dashboards

This service automatically pushes annotations to Grafana dashboards
when anomalies are detected, providing context for incidents.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import os
import time
from threading import Thread, Lock

logger = logging.getLogger(__name__)


class AnnotationType(Enum):
    """Types of annotations"""
    ANOMALY = "anomaly"
    ALERT = "alert"
    DEPLOYMENT = "deployment"
    INCIDENT = "incident"
    MAINTENANCE = "maintenance"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class GrafanaAnnotation:
    """Grafana annotation data structure"""
    dashboard_id: int
    panel_id: int
    time: int  # Unix timestamp in milliseconds
    time_end: Optional[int] = None
    text: str = ""
    tags: List[str] = None
    is_region: bool = False
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class GrafanaAnnotationService:
    """Service for managing Grafana annotations"""
    
    def __init__(self, grafana_url: str, api_key: str):
        """
        Initialize the Grafana annotation service.
        
        Args:
            grafana_url: Grafana server URL
            api_key: Grafana API key
        """
        self.grafana_url = grafana_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # Cache for dashboard and panel mappings
        self.dashboard_cache = {}
        self.cache_lock = Lock()
        self.cache_expiry = {}
        
        logger.info(f"Grafana annotation service initialized for {grafana_url}")
    
    def _get_dashboards(self) -> List[Dict[str, Any]]:
        """Get list of all dashboards"""
        try:
            response = self.session.get(f"{self.grafana_url}/api/search", 
                                      params={'type': 'dash-db'}, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch dashboards: {e}")
            return []
    
    def _get_dashboard_details(self, dashboard_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed dashboard information including panels"""
        with self.cache_lock:
            # Check cache first
            if dashboard_id in self.dashboard_cache:
                cache_time = self.cache_expiry.get(dashboard_id, 0)
                if time.time() - cache_time < 300:  # 5 minute cache
                    return self.dashboard_cache[dashboard_id]
        
        try:
            response = self.session.get(f"{self.grafana_url}/api/dashboards/id/{dashboard_id}", timeout=10)
            response.raise_for_status()
            dashboard_data = response.json()
            
            # Cache the result
            with self.cache_lock:
                self.dashboard_cache[dashboard_id] = dashboard_data
                self.cache_expiry[dashboard_id] = time.time()
            
            return dashboard_data
        except Exception as e:
            logger.error(f"Failed to fetch dashboard {dashboard_id}: {e}")
            return None
    
    def find_panel_by_title(self, dashboard_title: str, panel_title: str) -> Optional[tuple]:
        """
        Find panel ID by dashboard and panel titles.
        
        Args:
            dashboard_title: Dashboard title
            panel_title: Panel title
            
        Returns:
            Tuple of (dashboard_id, panel_id) or None if not found
        """
        dashboards = self._get_dashboards()
        
        for dashboard in dashboards:
            if dashboard.get('title', '').lower() == dashboard_title.lower():
                dashboard_id = dashboard['id']
                dashboard_details = self._get_dashboard_details(dashboard_id)
                
                if dashboard_details and 'dashboard' in dashboard_details:
                    panels = dashboard_details['dashboard'].get('panels', [])
                    for panel in panels:
                        if panel.get('title', '').lower() == panel_title.lower():
                            return dashboard_id, panel['id']
        
        return None
    
    def create_annotation(self, annotation: GrafanaAnnotation) -> bool:
        """
        Create an annotation in Grafana.
        
        Args:
            annotation: Annotation data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                'dashboardId': annotation.dashboard_id,
                'panelId': annotation.panel_id,
                'time': annotation.time,
                'text': annotation.text,
                'tags': annotation.tags,
                'isRegion': annotation.is_region
            }
            
            if annotation.time_end:
                payload['timeEnd'] = annotation.time_end
            
            response = self.session.post(f"{self.grafana_url}/api/annotations", 
                                       json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Annotation created: {result.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create annotation: {e}")
            return False
    
    def create_anomaly_annotation(self, anomaly_data: Dict[str, Any], 
                                 dashboard_mapping: Dict[str, str]) -> bool:
        """
        Create annotation for detected anomaly.
        
        Args:
            anomaly_data: Anomaly detection result
            dashboard_mapping: Mapping of metrics to dashboard/panel titles
            
        Returns:
            True if successful, False otherwise
        """
        metric_name = anomaly_data.get('metric_name', 'unknown')
        severity = anomaly_data.get('severity', 'unknown')
        current_value = anomaly_data.get('current_value', 0)
        baseline_value = anomaly_data.get('baseline_value', 0)
        deviation = anomaly_data.get('deviation_factor', 0)
        timestamp = anomaly_data.get('timestamp', datetime.now())
        
        # Convert timestamp to milliseconds
        timestamp_ms = int(timestamp.timestamp() * 1000)
        
        # Get dashboard/panel mapping
        mapping_key = f"{metric_name}:{severity}"
        dashboard_panel = dashboard_mapping.get(mapping_key)
        
        if not dashboard_panel:
            # Try generic mapping
            dashboard_panel = dashboard_mapping.get(metric_name)
        
        if not dashboard_panel:
            logger.warning(f"No dashboard mapping found for metric: {metric_name}")
            return False
        
        dashboard_title, panel_title = dashboard_panel.split(':')
        panel_info = self.find_panel_by_title(dashboard_title, panel_title)
        
        if not panel_info:
            logger.warning(f"Panel not found: {dashboard_title}:{panel_title}")
            return False
        
        dashboard_id, panel_id = panel_info
        
        # Create annotation text
        annotation_text = (
            f"🤖 ML Anomaly Detected\n"
            f"Metric: {metric_name}\n"
            f"Severity: {severity}\n"
            f"Current: {current_value:.3f}\n"
            f"Baseline: {baseline_value:.3f}\n"
            f"Deviation: {deviation:.2f}x"
        )
        
        # Determine annotation tags
        tags = [
            'anomaly',
            'ml-detection',
            f'severity-{severity}',
            f'metric-{metric_name}',
            'runtime-intelligence'
        ]
        
        annotation = GrafanaAnnotation(
            dashboard_id=dashboard_id,
            panel_id=panel_id,
            time=timestamp_ms,
            text=annotation_text,
            tags=tags
        )
        
        return self.create_annotation(annotation)
    
    def create_alert_annotation(self, alert_data: Dict[str, Any],
                               dashboard_mapping: Dict[str, str]) -> bool:
        """
        Create annotation for Prometheus alert.
        
        Args:
            alert_data: Alert data from Alertmanager
            dashboard_mapping: Mapping of alerts to dashboard/panel titles
            
        Returns:
            True if successful, False otherwise
        """
        labels = alert_data.get('labels', {})
        annotations = alert_data.get('annotations', {})
        
        alertname = labels.get('alertname', 'unknown')
        severity = labels.get('severity', 'unknown')
        service = labels.get('service', 'unknown')
        
        # Get dashboard/panel mapping
        mapping_key = f"{alertname}:{severity}"
        dashboard_panel = dashboard_mapping.get(mapping_key)
        
        if not dashboard_panel:
            # Try service-based mapping
            dashboard_panel = dashboard_mapping.get(f"{service}:{severity}")
        
        if not dashboard_panel:
            # Try generic mapping
            dashboard_panel = dashboard_mapping.get(alertname)
        
        if not dashboard_panel:
            logger.warning(f"No dashboard mapping found for alert: {alertname}")
            return False
        
        dashboard_title, panel_title = dashboard_panel.split(':')
        panel_info = self.find_panel_by_title(dashboard_title, panel_title)
        
        if not panel_info:
            logger.warning(f"Panel not found: {dashboard_title}:{panel_title}")
            return False
        
        dashboard_id, panel_id = panel_info
        
        # Parse timestamp
        timestamp = datetime.now()
        if alert_data.get('startsAt'):
            try:
                timestamp = datetime.fromisoformat(alert_data['startsAt'].replace('Z', '+00:00'))
            except:
                pass
        
        timestamp_ms = int(timestamp.timestamp() * 1000)
        
        # Create annotation text
        summary = annotations.get('summary', f'Alert: {alertname}')
        description = annotations.get('description', 'No description')
        
        annotation_text = (
            f"🚨 {summary}\n"
            f"Service: {service}\n"
            f"Severity: {severity}\n"
            f"{description}"
        )
        
        # Add current/baseline values if available
        if annotations.get('current_value'):
            annotation_text += f"\nCurrent: {annotations['current_value']}"
        if annotations.get('baseline_value'):
            annotation_text += f"\nBaseline: {annotations['baseline_value']}"
        
        # Determine annotation tags
        tags = [
            'alert',
            f'severity-{severity}',
            f'alert-{alertname}',
            f'service-{service}',
            'prometheus'
        ]
        
        annotation = GrafanaAnnotation(
            dashboard_id=dashboard_id,
            panel_id=panel_id,
            time=timestamp_ms,
            text=annotation_text,
            tags=tags
        )
        
        return self.create_annotation(annotation)
    
    def create_deployment_annotation(self, deployment_info: Dict[str, Any],
                                   dashboard_title: str = "Service Overview") -> bool:
        """
        Create annotation for deployment events.
        
        Args:
            deployment_info: Deployment information
            dashboard_title: Target dashboard title
            
        Returns:
            True if successful, False otherwise
        """
        # Find the main service overview dashboard
        dashboards = self._get_dashboards()
        dashboard_id = None
        
        for dashboard in dashboards:
            if dashboard.get('title', '').lower() == dashboard_title.lower():
                dashboard_id = dashboard['id']
                break
        
        if not dashboard_id:
            logger.warning(f"Dashboard not found: {dashboard_title}")
            return False
        
        timestamp = datetime.now()
        timestamp_ms = int(timestamp.timestamp() * 1000)
        
        # Create annotation text
        version = deployment_info.get('version', 'unknown')
        commit = deployment_info.get('commit', 'unknown')
        author = deployment_info.get('author', 'unknown')
        
        annotation_text = (
            f"🚀 Deployment\n"
            f"Version: {version}\n"
            f"Commit: {commit[:8]}\n"
            f"Author: {author}"
        )
        
        tags = [
            'deployment',
            f'version-{version}',
            'runtime-intelligence'
        ]
        
        annotation = GrafanaAnnotation(
            dashboard_id=dashboard_id,
            panel_id=0,  # Use panel 0 for dashboard-level annotation
            time=timestamp_ms,
            text=annotation_text,
            tags=tags
        )
        
        return self.create_annotation(annotation)


class AnnotationManager:
    """Manager for handling different types of annotations"""
    
    def __init__(self, grafana_url: str, api_key: str):
        """
        Initialize the annotation manager.
        
        Args:
            grafana_url: Grafana server URL
            api_key: Grafana API key
        """
        self.grafana_service = GrafanaAnnotationService(grafana_url, api_key)
        
        # Dashboard mapping configuration
        # Format: "metric_or_alert:severity" -> "dashboard_title:panel_title"
        self.dashboard_mapping = {
            # Request rate anomalies
            "request_rate:critical": "Service Overview:Request Rate",
            "request_rate:high": "Service Overview:Request Rate",
            "request_rate:medium": "Service Overview:Request Rate",
            
            # Response time anomalies
            "response_time:critical": "Performance:Response Time",
            "response_time:high": "Performance:Response Time",
            "response_time:medium": "Performance:Response Time",
            
            # Error rate anomalies
            "error_rate:critical": "Error Rates:5xx Error Rate",
            "error_rate:high": "Error Rates:5xx Error Rate",
            "error_rate:medium": "Error Rates:5xx Error Rate",
            
            # System metrics
            "cpu_usage:critical": "System Resources:CPU Usage",
            "cpu_usage:high": "System Resources:CPU Usage",
            "memory_usage:critical": "System Resources:Memory Usage",
            "memory_usage:high": "System Resources:Memory Usage",
            
            # Prometheus alerts
            "ServiceDown:critical": "Service Overview:Service Status",
            "CriticalHighErrorRate:critical": "Error Rates:5xx Error Rate",
            "HighRequestLatency:warning": "Performance:Response Time",
            "RequestVolumeSpike:warning": "Service Overview:Request Rate",
            "HighCPUUsage:warning": "System Resources:CPU Usage",
            "HighMemoryUsage:warning": "System Resources:Memory Usage",
            
            # Generic mappings
            "request_rate": "Service Overview:Request Rate",
            "response_time": "Performance:Response Time",
            "error_rate": "Error Rates:5xx Error Rate",
            "cpu_usage": "System Resources:CPU Usage",
            "memory_usage": "System Resources:Memory Usage"
        }
        
        logger.info("Annotation Manager initialized")
    
    def handle_anomaly_detection(self, anomaly_data: Dict[str, Any]) -> bool:
        """
        Handle anomaly detection result and create annotation.
        
        Args:
            anomaly_data: Anomaly detection result
            
        Returns:
            True if annotation created successfully
        """
        try:
            success = self.grafana_service.create_anomaly_annotation(
                anomaly_data, self.dashboard_mapping
            )
            
            if success:
                logger.info(f"Anomaly annotation created for {anomaly_data.get('metric_name')}")
            else:
                logger.warning(f"Failed to create anomaly annotation for {anomaly_data.get('metric_name')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling anomaly detection: {e}")
            return False
    
    def handle_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Handle Prometheus alert and create annotation.
        
        Args:
            alert_data: Alert data from Alertmanager
            
        Returns:
            True if annotation created successfully
        """
        try:
            success = self.grafana_service.create_alert_annotation(
                alert_data, self.dashboard_mapping
            )
            
            if success:
                logger.info(f"Alert annotation created for {alert_data.get('labels', {}).get('alertname')}")
            else:
                logger.warning(f"Failed to create alert annotation for {alert_data.get('labels', {}).get('alertname')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
            return False
    
    def handle_deployment(self, deployment_info: Dict[str, Any]) -> bool:
        """
        Handle deployment event and create annotation.
        
        Args:
            deployment_info: Deployment information
            
        Returns:
            True if annotation created successfully
        """
        try:
            success = self.grafana_service.create_deployment_annotation(deployment_info)
            
            if success:
                logger.info(f"Deployment annotation created for version {deployment_info.get('version')}")
            else:
                logger.warning(f"Failed to create deployment annotation")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling deployment: {e}")
            return False
    
    def update_dashboard_mapping(self, new_mappings: Dict[str, str]):
        """
        Update dashboard mapping configuration.
        
        Args:
            new_mappings: New mapping dictionary
        """
        self.dashboard_mapping.update(new_mappings)
        logger.info(f"Updated dashboard mapping with {len(new_mappings)} new entries")
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """
        Get mapping statistics.
        
        Returns:
            Dictionary with mapping statistics
        """
        return {
            "total_mappings": len(self.dashboard_mapping),
            "mappings": self.dashboard_mapping
        }


# Global annotation manager instance
annotation_manager = None


def initialize_annotation_manager(grafana_url: str, api_key: str):
    """Initialize the global annotation manager"""
    global annotation_manager
    annotation_manager = AnnotationManager(grafana_url, api_key)
    logger.info("Global annotation manager initialized")


def annotate_anomaly(anomaly_data: Dict[str, Any]) -> bool:
    """Create annotation for anomaly detection result"""
    if annotation_manager is None:
        logger.error("Annotation manager not initialized")
        return False
    
    return annotation_manager.handle_anomaly_detection(anomaly_data)


def annotate_alert(alert_data: Dict[str, Any]) -> bool:
    """Create annotation for Prometheus alert"""
    if annotation_manager is None:
        logger.error("Annotation manager not initialized")
        return False
    
    return annotation_manager.handle_alert(alert_data)


def annotate_deployment(deployment_info: Dict[str, Any]) -> bool:
    """Create annotation for deployment event"""
    if annotation_manager is None:
        logger.error("Annotation manager not initialized")
        return False
    
    return annotation_manager.handle_deployment(deployment_info)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize with environment variables
    grafana_url = os.getenv('GRAFANA_URL', 'http://localhost:3000')
    api_key = os.getenv('GRAFANA_API_KEY', 'your-api-key')
    
    initialize_annotation_manager(grafana_url, api_key)
    
    # Example anomaly data
    example_anomaly = {
        'metric_name': 'request_rate',
        'severity': 'high',
        'current_value': 150.5,
        'baseline_value': 50.2,
        'deviation_factor': 3.0,
        'timestamp': datetime.now()
    }
    
    # Create annotation
    success = annotate_anomaly(example_anomaly)
    print(f"Annotation created: {success}")
