"""
Incident Analyzer for AI Incident Insight Agent

Correlates anomalies with known root causes and scores them by confidence.
Analyzes patterns in metrics, logs, traces, deployments, and system events.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from .data_collector import IncidentContext, MetricAnomaly, TraceOutlier, LogSignature, DeploymentEvent, SystemEvent

logger = logging.getLogger(__name__)

class RootCauseType(Enum):
    """Types of root causes that can be detected"""
    DEPLOYMENT_REGRESSION = "deployment_regression"
    INFRASTRUCTURE_DEGRADATION = "infrastructure_degradation"
    DATABASE_ISSUES = "database_issues"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ISSUES = "network_issues"
    THIRD_PARTY_SERVICE = "third_party_service"
    UNKNOWN = "unknown"

@dataclass
class RootCause:
    """Represents a detected root cause with confidence score"""
    cause_type: RootCauseType
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: List[str]
    affected_services: List[str]
    timeframe: Tuple[datetime, datetime]
    remediation_suggestions: List[str]
    related_metrics: List[str]
    related_logs: List[str]
    related_traces: List[str]

class IncidentAnalyzer:
    """Analyzes incident context and infers likely root causes"""
    
    def __init__(self):
        """Initialize the incident analyzer with known patterns"""
        self.deployment_patterns = self._init_deployment_patterns()
        self.database_patterns = self._init_database_patterns()
        self.infrastructure_patterns = self._init_infrastructure_patterns()
        self.dependency_patterns = self._init_dependency_patterns()
        
    def analyze_incident(self, context: IncidentContext) -> List[RootCause]:
        """
        Analyze incident context and return ranked list of root causes
        
        Args:
            context: Complete incident context with telemetry data
            
        Returns:
            List of RootCause objects ranked by confidence
        """
        logger.info(f"Analyzing incident {context.incident_id}")
        
        root_causes = []
        
        # Analyze different types of root causes
        root_causes.extend(self._analyze_deployment_regression(context))
        root_causes.extend(self._analyze_database_issues(context))
        root_causes.extend(self._analyze_infrastructure_degradation(context))
        root_causes.extend(self._analyze_dependency_failures(context))
        root_causes.extend(self._analyze_resource_exhaustion(context))
        root_causes.extend(self._analyze_configuration_errors(context))
        
        # Sort by confidence (highest first)
        root_causes.sort(key=lambda x: x.confidence, reverse=True)
        
        # Filter out very low confidence causes
        root_causes = [rc for rc in root_causes if rc.confidence > 0.3]
        
        logger.info(f"Found {len(root_causes)} potential root causes for incident {context.incident_id}")
        
        return root_causes
    
    def _analyze_deployment_regression(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by a recent deployment"""
        causes = []
        
        # Check if there were deployments shortly before the incident
        incident_time = context.timestamp
        deployment_window = incident_time - timedelta(minutes=30)
        
        recent_deployments = [
            dep for dep in context.deployment_events
            if dep.timestamp >= deployment_window and dep.timestamp <= incident_time
        ]
        
        if not recent_deployments:
            return causes
        
        # Look for correlation between deployment and metrics
        deployment = recent_deployments[0]  # Most recent deployment
        
        # Check for latency spikes after deployment
        latency_anomalies = [
            ma for ma in context.metric_anomalies
            if "latency" in ma.metric_name.lower() or "duration" in ma.metric_name.lower()
        ]
        
        # Check for error rate increases after deployment
        error_anomalies = [
            ma for ma in context.metric_anomalies
            if "error" in ma.metric_name.lower() or "5" in ma.metric_name
        ]
        
        confidence = 0.5  # Base confidence
        
        evidence = []
        affected_services = deployment.affected_services
        
        if latency_anomalies:
            confidence += 0.3
            evidence.append(f"Latency spikes detected after deployment {deployment.version}")
            affected_services.extend([ma.labels.get("service", "unknown") for ma in latency_anomalies])
        
        if error_anomalies:
            confidence += 0.2
            evidence.append(f"Error rate increases detected after deployment {deployment.version}")
            affected_services.extend([ma.labels.get("service", "unknown") for ma in error_anomalies])
        
        # Check for specific error patterns in logs
        deployment_related_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "null pointer", "method not found", "class not found", 
                "configuration", "initialization", "startup"
            ])
        ]
        
        if deployment_related_errors:
            confidence += 0.2
            evidence.extend([f"Deployment-related errors: {ls.pattern}" for ls in deployment_related_errors])
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.DEPLOYMENT_REGRESSION,
                confidence=min(confidence, 0.95),
                description=f"Deployment regression in {deployment.version} (PR #{deployment.pull_request_id})",
                evidence=evidence,
                affected_services=list(set(affected_services)),
                timeframe=(deployment.timestamp, incident_time),
                remediation_suggestions=[
                    f"Rollback deployment to previous version",
                    f"Review changes in PR #{deployment.pull_request_id}",
                    "Check for breaking changes or configuration issues",
                    "Run canary deployment for future releases"
                ],
                related_metrics=[ma.metric_name for ma in latency_anomalies + error_anomalies],
                related_logs=[ls.pattern for ls in deployment_related_errors],
                related_traces=[]
            )
            causes.append(cause)
        
        return causes
    
    def _analyze_database_issues(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by database problems"""
        causes = []
        
        # Look for database-related error patterns
        db_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "database", "sql", "connection", "timeout", "deadlock", 
                "constraint", "foreign key", "unique", "duplicate"
            ])
        ]
        
        if not db_errors:
            return causes
        
        # Check for database-related metric anomalies
        db_metrics = [
            ma for ma in context.metric_anomalies
            if any(keyword in ma.metric_name.lower() for keyword in [
                "database", "db", "sql", "connection", "query"
            ])
        ]
        
        # Check for slow database traces
        slow_db_traces = [
            to for to in context.trace_outliers
            if any(keyword in to.operation_name.lower() for keyword in [
                "database", "sql", "query", "select", "insert", "update", "delete"
            ])
        ]
        
        confidence = 0.4  # Base confidence for database errors
        
        evidence = []
        affected_services = []
        
        if db_metrics:
            confidence += 0.3
            evidence.extend([f"Database metric anomaly: {ma.description}" for ma in db_metrics])
            affected_services.extend([ma.labels.get("service", "unknown") for ma in db_metrics])
        
        if slow_db_traces:
            confidence += 0.2
            evidence.extend([f"Slow database operation: {to.operation_name} ({to.duration_ms:.0f}ms)" for to in slow_db_traces])
            affected_services.extend([to.service_name for to in slow_db_traces])
        
        # Analyze specific error types
        timeout_errors = [ls for ls in db_errors if "timeout" in ls.pattern.lower()]
        if timeout_errors:
            confidence += 0.2
            evidence.append("Database connection timeout errors detected")
        
        deadlock_errors = [ls for ls in db_errors if "deadlock" in ls.pattern.lower()]
        if deadlock_errors:
            confidence += 0.3
            evidence.append("Database deadlock errors detected")
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.DATABASE_ISSUES,
                confidence=min(confidence, 0.95),
                description="Database performance or connectivity issues",
                evidence=evidence,
                affected_services=list(set(affected_services)) or ["database-service"],
                timeframe=(context.timestamp - timedelta(minutes=10), context.timestamp),
                remediation_suggestions=[
                    "Check database connection pool settings",
                    "Review slow query logs",
                    "Verify database server health and resources",
                    "Check for database locks or long-running transactions",
                    "Consider scaling database resources"
                ],
                related_metrics=[ma.metric_name for ma in db_metrics],
                related_logs=[ls.pattern for ls in db_errors],
                related_traces=[to.trace_id for to in slow_db_traces]
            )
            causes.append(cause)
        
        return causes
    
    def _analyze_infrastructure_degradation(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by infrastructure problems"""
        causes = []
        
        # Check for system events indicating infrastructure issues
        infra_events = [
            se for se in context.system_events
            if se.event_type in ["node_restart", "pod_eviction", "memory_pressure", "disk_full"]
        ]
        
        if not infra_events:
            return causes
        
        # Check for resource-related metric anomalies
        resource_metrics = [
            ma for ma in context.metric_anomalies
            if any(keyword in ma.metric_name.lower() for keyword in [
                "cpu", "memory", "disk", "network", "load", "usage"
            ])
        ]
        
        # Check for infrastructure-related error patterns
        infra_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "out of memory", "disk full", "network", "connection refused", 
                "timeout", "unreachable", "no space"
            ])
        ]
        
        confidence = 0.5  # Base confidence for infrastructure events
        
        evidence = []
        affected_components = []
        
        for event in infra_events:
            evidence.append(f"Infrastructure event: {event.description}")
            affected_components.extend(event.affected_components)
            confidence += 0.2
        
        if resource_metrics:
            confidence += 0.2
            evidence.extend([f"Resource metric anomaly: {ma.description}" for ma in resource_metrics])
        
        if infra_errors:
            confidence += 0.1
            evidence.extend([f"Infrastructure error: {ls.pattern}" for ls in infra_errors])
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.INFRASTRUCTURE_DEGRADATION,
                confidence=min(confidence, 0.95),
                description="Infrastructure degradation affecting system performance",
                evidence=evidence,
                affected_services=list(set(affected_components)),
                timeframe=(context.timestamp - timedelta(minutes=15), context.timestamp),
                remediation_suggestions=[
                    "Check node health and resource utilization",
                    "Restart affected pods or nodes",
                    "Scale resources if needed",
                    "Check for resource leaks in applications",
                    "Verify network connectivity between components"
                ],
                related_metrics=[ma.metric_name for ma in resource_metrics],
                related_logs=[ls.pattern for ls in infra_errors],
                related_traces=[]
            )
            causes.append(cause)
        
        return causes
    
    def _analyze_dependency_failures(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by external dependency failures"""
        causes = []
        
        # Look for dependency-related error patterns
        dependency_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "connection refused", "timeout", "unreachable", "service unavailable",
                "gateway timeout", "bad gateway", "502", "503", "504"
            ])
        ]
        
        # Check for dependency-related traces
        dependency_traces = [
            to for to in context.trace_outliers
            if any(keyword in to.operation_name.lower() for keyword in [
                "http", "api", "external", "third-party", "payment", "notification"
            ])
        ]
        
        if not dependency_errors and not dependency_traces:
            return causes
        
        confidence = 0.4  # Base confidence
        
        evidence = []
        affected_services = []
        
        if dependency_errors:
            confidence += 0.3
            evidence.extend([f"Dependency error: {ls.pattern}" for ls in dependency_errors])
            affected_services.extend([ls.service for ls in dependency_errors])
        
        if dependency_traces:
            confidence += 0.2
            evidence.extend([f"Slow external call: {to.operation_name}" for to in dependency_traces])
            affected_services.extend([to.service_name for to in dependency_traces])
        
        # Check for specific HTTP status codes
        http_5xx_errors = [ls for ls in dependency_errors if any(code in ls.pattern for code in ["502", "503", "504"])]
        if http_5xx_errors:
            confidence += 0.2
            evidence.append("HTTP 5xx errors from external services detected")
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.DEPENDENCY_FAILURE,
                confidence=min(confidence, 0.95),
                description="External dependency service failure or degradation",
                evidence=evidence,
                affected_services=list(set(affected_services)),
                timeframe=(context.timestamp - timedelta(minutes=10), context.timestamp),
                remediation_suggestions=[
                    "Check external service status pages",
                    "Implement circuit breaker patterns",
                    "Add retry logic with exponential backoff",
                    "Consider fallback mechanisms",
                    "Contact external service provider if needed"
                ],
                related_metrics=[],
                related_logs=[ls.pattern for ls in dependency_errors],
                related_traces=[to.trace_id for to in dependency_traces]
            )
            causes.append(cause)
        
        return causes
    
    def _analyze_resource_exhaustion(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by resource exhaustion"""
        causes = []
        
        # Look for resource exhaustion patterns
        resource_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "out of memory", "memory allocation failed", "heap space",
                "too many open files", "disk space", "quota exceeded"
            ])
        ]
        
        # Check for resource-related metrics
        resource_metrics = [
            ma for ma in context.metric_anomalies
            if any(keyword in ma.metric_name.lower() for keyword in [
                "memory", "heap", "gc", "cpu", "thread", "connection"
            ])
        ]
        
        if not resource_errors and not resource_metrics:
            return causes
        
        confidence = 0.4  # Base confidence
        
        evidence = []
        affected_services = []
        
        if resource_errors:
            confidence += 0.4
            evidence.extend([f"Resource exhaustion error: {ls.pattern}" for ls in resource_errors])
            affected_services.extend([ls.service for ls in resource_errors])
        
        if resource_metrics:
            confidence += 0.2
            evidence.extend([f"Resource metric anomaly: {ma.description}" for ma in resource_metrics])
            affected_services.extend([ma.labels.get("service", "unknown") for ma in resource_metrics])
        
        # Check for memory-specific issues
        memory_errors = [ls for ls in resource_errors if "memory" in ls.pattern.lower()]
        if memory_errors:
            confidence += 0.2
            evidence.append("Memory exhaustion errors detected")
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.RESOURCE_EXHAUSTION,
                confidence=min(confidence, 0.95),
                description="Application or system resource exhaustion",
                evidence=evidence,
                affected_services=list(set(affected_services)),
                timeframe=(context.timestamp - timedelta(minutes=15), context.timestamp),
                remediation_suggestions=[
                    "Increase memory limits for affected services",
                    "Check for memory leaks in application code",
                    "Scale horizontally to distribute load",
                    "Optimize memory usage in application",
                    "Monitor garbage collection patterns"
                ],
                related_metrics=[ma.metric_name for ma in resource_metrics],
                related_logs=[ls.pattern for ls in resource_errors],
                related_traces=[]
            )
            causes.append(cause)
        
        return causes
    
    def _analyze_configuration_errors(self, context: IncidentContext) -> List[RootCause]:
        """Analyze if incident is caused by configuration errors"""
        causes = []
        
        # Look for configuration-related error patterns
        config_errors = [
            ls for ls in context.log_signatures
            if any(pattern in ls.pattern.lower() for pattern in [
                "configuration", "config", "property", "setting", "parameter",
                "missing", "invalid", "not found", "unrecognized"
            ])
        ]
        
        if not config_errors:
            return causes
        
        confidence = 0.5  # Base confidence for configuration errors
        
        evidence = []
        affected_services = []
        
        evidence.extend([f"Configuration error: {ls.pattern}" for ls in config_errors])
        affected_services.extend([ls.service for ls in config_errors])
        
        # Check if there were recent deployments (config changes often come with deployments)
        recent_deployments = [
            dep for dep in context.deployment_events
            if dep.timestamp >= context.timestamp - timedelta(minutes=30)
        ]
        
        if recent_deployments:
            confidence += 0.2
            evidence.append(f"Configuration errors following deployment {recent_deployments[0].version}")
        
        if confidence > 0.6:
            cause = RootCause(
                cause_type=RootCauseType.CONFIGURATION_ERROR,
                confidence=min(confidence, 0.95),
                description="Application configuration error or missing settings",
                evidence=evidence,
                affected_services=list(set(affected_services)),
                timeframe=(context.timestamp - timedelta(minutes=10), context.timestamp),
                remediation_suggestions=[
                    "Verify application configuration files",
                    "Check environment variables and secrets",
                    "Validate configuration schema",
                    "Review recent configuration changes",
                    "Test configuration in staging environment"
                ],
                related_metrics=[],
                related_logs=[ls.pattern for ls in config_errors],
                related_traces=[]
            )
            causes.append(cause)
        
        return causes
    
    def _init_deployment_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for detecting deployment-related issues"""
        return {
            "error_patterns": [
                "null pointer", "method not found", "class not found",
                "configuration", "initialization", "startup"
            ],
            "metric_patterns": [
                "latency", "duration", "error_rate", "exception"
            ]
        }
    
    def _init_database_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for detecting database issues"""
        return {
            "error_patterns": [
                "database", "sql", "connection", "timeout", "deadlock",
                "constraint", "foreign key", "unique", "duplicate"
            ],
            "metric_patterns": [
                "database", "db", "sql", "connection", "query"
            ]
        }
    
    def _init_infrastructure_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for detecting infrastructure issues"""
        return {
            "error_patterns": [
                "out of memory", "disk full", "network", "connection refused",
                "timeout", "unreachable", "no space"
            ],
            "metric_patterns": [
                "cpu", "memory", "disk", "network", "load", "usage"
            ]
        }
    
    def _init_dependency_patterns(self) -> Dict[str, Any]:
        """Initialize patterns for detecting dependency failures"""
        return {
            "error_patterns": [
                "connection refused", "timeout", "unreachable", "service unavailable",
                "gateway timeout", "bad gateway", "502", "503", "504"
            ],
            "trace_patterns": [
                "http", "api", "external", "third-party", "payment", "notification"
            ]
        }
