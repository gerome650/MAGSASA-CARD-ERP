"""
Data Collector for AI Incident Insight Agent

Aggregates telemetry from:
- Metrics: Prometheus API (before/after anomaly windows)
- Logs: Loki / ELK queries
- Traces: Jaeger / Tempo spans
- Alerts: Alertmanager webhook payloads
- Deployments: GitHub / CI webhook data
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class MetricAnomaly:
    """Represents a metric anomaly detected during incident window"""

    metric_name: str
    value: float
    threshold: float
    severity: str  # "critical", "warning", "info"
    timestamp: datetime
    labels: dict[str, str]
    description: str


@dataclass
class TraceOutlier:
    """Represents a slow or failed trace span"""

    trace_id: str
    span_id: str
    operation_name: str
    duration_ms: float
    status_code: str
    error_message: str | None
    timestamp: datetime
    service_name: str
    tags: dict[str, str]


@dataclass
class LogSignature:
    """Represents error patterns in logs"""

    pattern: str
    count: int
    first_seen: datetime
    last_seen: datetime
    severity: str
    service: str
    log_level: str
    sample_messages: list[str]


@dataclass
class DeploymentEvent:
    """Represents a deployment that occurred around incident time"""

    deployment_id: str
    version: str
    commit_hash: str
    author: str
    timestamp: datetime
    status: str  # "success", "failure", "rolling_back"
    affected_services: list[str]
    pull_request_id: int | None


@dataclass
class SystemEvent:
    """Represents infrastructure or system-level events"""

    event_type: str
    timestamp: datetime
    description: str
    severity: str
    affected_components: list[str]
    metadata: dict[str, Any]


@dataclass
class IncidentContext:
    """Complete incident context with all telemetry data"""

    incident_id: str
    timestamp: datetime
    duration_minutes: int
    metric_anomalies: list[MetricAnomaly]
    trace_outliers: list[TraceOutlier]
    log_signatures: list[LogSignature]
    deployment_events: list[DeploymentEvent]
    system_events: list[SystemEvent]
    alert_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat(),
            "duration_minutes": self.duration_minutes,
            "metric_anomalies": [asdict(ma) for ma in self.metric_anomalies],
            "trace_outliers": [asdict(to) for to in self.trace_outliers],
            "log_signatures": [asdict(ls) for ls in self.log_signatures],
            "deployment_events": [asdict(de) for de in self.deployment_events],
            "system_events": [asdict(se) for se in self.system_events],
            "alert_payload": self.alert_payload,
        }


class IncidentContextCollector:
    """Collects and aggregates telemetry data for incident analysis"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the collector with configuration

        Expected config structure:
        {
            "prometheus": {"base_url": "http://localhost:9090"},
            "jaeger": {"base_url": "http://localhost:16686"},
            "loki": {"base_url": "http://localhost:3100"},
            "github": {"api_url": "https://api.github.com", "token": "..."},
            "alertmanager": {"webhook_url": "..."}
        }
        """
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    async def collect_incident_context(
        self, incident_id: str, alert_payload: dict[str, Any], window_minutes: int = 30
    ) -> IncidentContext:
        """
        Collect complete incident context from all telemetry sources

        Args:
            incident_id: Unique identifier for the incident
            alert_payload: Alertmanager webhook payload
            window_minutes: Time window to analyze (before and after alert)

        Returns:
            IncidentContext with all aggregated telemetry data
        """
        logger.info(f"Collecting incident context for {incident_id}")

        # Parse alert timestamp
        alert_time = datetime.fromisoformat(
            alert_payload.get("alerts", [{}])[0].get(
                "startsAt", datetime.now().isoformat()
            )
        )

        # Define time windows
        start_time = alert_time - timedelta(minutes=window_minutes)
        end_time = alert_time + timedelta(minutes=window_minutes)

        # Collect data from all sources in parallel (simulated with sequential calls)
        metric_anomalies = await self._collect_metric_anomalies(start_time, end_time)
        trace_outliers = await self._collect_trace_outliers(start_time, end_time)
        log_signatures = await self._collect_log_signatures(start_time, end_time)
        deployment_events = await self._collect_deployment_events(start_time, end_time)
        system_events = await self._collect_system_events(start_time, end_time)

        context = IncidentContext(
            incident_id=incident_id,
            timestamp=alert_time,
            duration_minutes=window_minutes,
            metric_anomalies=metric_anomalies,
            trace_outliers=trace_outliers,
            log_signatures=log_signatures,
            deployment_events=deployment_events,
            system_events=system_events,
            alert_payload=alert_payload,
        )

        logger.info(
            f"Collected context for {incident_id}: {len(metric_anomalies)} metrics, "
            f"{len(trace_outliers)} traces, {len(log_signatures)} log patterns"
        )

        return context

    async def _collect_metric_anomalies(
        self, start_time: datetime, end_time: datetime
    ) -> list[MetricAnomaly]:
        """Collect metric anomalies from Prometheus"""
        anomalies = []

        try:
            prometheus_config = self.config.get("prometheus", {})
            base_url = prometheus_config.get("base_url", "http://localhost:9090")

            # Query for high latency metrics
            latency_query = """
            rate(http_request_duration_seconds_bucket{le="+Inf"}[5m]) > 0.1
            """
            latency_response = self.session.get(
                f"{base_url}/api/v1/query",
                params={"query": latency_query, "time": end_time.timestamp()},
                timeout=30,
            )

            if latency_response.status_code == 200:
                data = latency_response.json()
                if data.get("status") == "success":
                    for result in data.get("data", {}).get("result", []):
                        metric = result.get("metric", {})
                        value = float(result.get("value", [0, 0])[1])

                        anomaly = MetricAnomaly(
                            metric_name="http_request_duration_seconds",
                            value=value,
                            threshold=0.1,
                            severity="critical" if value > 0.5 else "warning",
                            timestamp=datetime.fromtimestamp(
                                result.get("value", [0, 0])[0]
                            ),
                            labels=metric,
                            description=f"High request latency detected: {value:.2f}s",
                        )
                        anomalies.append(anomaly)

            # Query for error rate spikes
            error_query = """
            rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
            """
            error_response = self.session.get(
                f"{base_url}/api/v1/query",
                params={"query": error_query, "time": end_time.timestamp()},
                timeout=30,
            )

            if error_response.status_code == 200:
                data = error_response.json()
                if data.get("status") == "success":
                    for result in data.get("data", {}).get("result", []):
                        metric = result.get("metric", {})
                        value = float(result.get("value", [0, 0])[1])

                        anomaly = MetricAnomaly(
                            metric_name="http_error_rate",
                            value=value,
                            threshold=0.05,
                            severity="critical" if value > 0.1 else "warning",
                            timestamp=datetime.fromtimestamp(
                                result.get("value", [0, 0])[0]
                            ),
                            labels=metric,
                            description=f"High error rate detected: {value:.1%}",
                        )
                        anomalies.append(anomaly)

        except Exception as e:
            logger.error(f"Failed to collect metric anomalies: {e}")

        return anomalies

    async def _collect_trace_outliers(
        self, start_time: datetime, end_time: datetime
    ) -> list[TraceOutlier]:
        """Collect slow/failed traces from Jaeger"""
        outliers = []

        try:
            jaeger_config = self.config.get("jaeger", {})
            base_url = jaeger_config.get("base_url", "http://localhost:16686")

            # Query for slow traces (> 2 seconds)
            search_params = {
                "service": "",  # All services
                "start": int(start_time.timestamp() * 1000000),  # Microseconds
                "end": int(end_time.timestamp() * 1000000),
                "minDuration": "2s",
                "limit": 100,
            }

            response = self.session.get(
                f"{base_url}/api/traces", params=search_params, timeout=30
            )

            if response.status_code == 200:
                traces = response.json().get("data", [])

                for trace in traces:
                    for span in trace.get("spans", []):
                        duration_ms = span.get("duration", 0) / 1000  # Convert to ms

                        if duration_ms > 2000:  # > 2 seconds
                            outlier = TraceOutlier(
                                trace_id=trace.get("traceID", ""),
                                span_id=span.get("spanID", ""),
                                operation_name=span.get("operationName", ""),
                                duration_ms=duration_ms,
                                status_code=str(span.get("statusCode", 0)),
                                error_message=span.get("error", ""),
                                timestamp=datetime.fromtimestamp(
                                    span.get("startTime", 0) / 1000000
                                ),
                                service_name=span.get("process", {}).get(
                                    "serviceName", ""
                                ),
                                tags=span.get("tags", {}),
                            )
                            outliers.append(outlier)

        except Exception as e:
            logger.error(f"Failed to collect trace outliers: {e}")

        return outliers

    async def _collect_log_signatures(
        self, start_time: datetime, end_time: datetime
    ) -> list[LogSignature]:
        """Collect error patterns from logs (Loki/ELK)"""
        signatures = []

        try:
            # For now, simulate log signature collection
            # In production, this would query Loki or ELK

            # Simulate common error patterns
            error_patterns = [
                {
                    "pattern": "Database connection timeout",
                    "count": 45,
                    "severity": "critical",
                    "service": "magsasa-card-erp",
                    "log_level": "ERROR",
                    "sample_messages": [
                        "Database connection timeout after 30 seconds",
                        "Failed to connect to PostgreSQL database",
                    ],
                },
                {
                    "pattern": "Out of memory",
                    "count": 12,
                    "severity": "critical",
                    "service": "magsasa-card-erp",
                    "log_level": "ERROR",
                    "sample_messages": [
                        "java.lang.OutOfMemoryError: Java heap space",
                        "Memory allocation failed",
                    ],
                },
                {
                    "pattern": "Rate limit exceeded",
                    "count": 8,
                    "severity": "warning",
                    "service": "magsasa-card-erp",
                    "log_level": "WARN",
                    "sample_messages": [
                        "Rate limit exceeded for user 12345",
                        "API rate limit reached",
                    ],
                },
            ]

            for pattern_data in error_patterns:
                signature = LogSignature(
                    pattern=pattern_data["pattern"],
                    count=pattern_data["count"],
                    first_seen=start_time,
                    last_seen=end_time,
                    severity=pattern_data["severity"],
                    service=pattern_data["service"],
                    log_level=pattern_data["log_level"],
                    sample_messages=pattern_data["sample_messages"],
                )
                signatures.append(signature)

        except Exception as e:
            logger.error(f"Failed to collect log signatures: {e}")

        return signatures

    async def _collect_deployment_events(
        self, start_time: datetime, end_time: datetime
    ) -> list[DeploymentEvent]:
        """Collect deployment events from GitHub/CI systems"""
        events = []

        try:
            github_config = self.config.get("github", {})
            github_config.get("api_url", "https://api.github.com")
            token = github_config.get("token", "")

            if token:

                # Query recent deployments (simplified)
                # In production, this would query GitHub API or CI webhooks

                # Simulate deployment event
                deployment = DeploymentEvent(
                    deployment_id="deploy-123",
                    version="v1.4.2",
                    commit_hash="abc123def456",
                    author="developer@magsasa.com",
                    timestamp=start_time - timedelta(minutes=5),
                    status="success",
                    affected_services=["magsasa-card-erp", "payment-service"],
                    pull_request_id=812,
                )
                events.append(deployment)

        except Exception as e:
            logger.error(f"Failed to collect deployment events: {e}")

        return events

    async def _collect_system_events(
        self, start_time: datetime, end_time: datetime
    ) -> list[SystemEvent]:
        """Collect system-level events (infrastructure, scaling, etc.)"""
        events = []

        try:
            # Simulate system events
            # In production, this would query infrastructure monitoring

            system_events_data = [
                {
                    "event_type": "node_restart",
                    "description": "Kubernetes node restarted due to memory pressure",
                    "severity": "warning",
                    "affected_components": ["k8s-node-1", "payment-pod"],
                },
                {
                    "event_type": "scaling_event",
                    "description": "Auto-scaling triggered due to high CPU usage",
                    "severity": "info",
                    "affected_components": ["payment-service", "order-service"],
                },
            ]

            for event_data in system_events_data:
                event = SystemEvent(
                    event_type=event_data["event_type"],
                    timestamp=start_time + timedelta(minutes=2),
                    description=event_data["description"],
                    severity=event_data["severity"],
                    affected_components=event_data["affected_components"],
                    metadata={"source": "kubernetes", "cluster": "production"},
                )
                events.append(event)

        except Exception as e:
            logger.error(f"Failed to collect system events: {e}")

        return events
