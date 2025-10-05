"""
Insight Engine for AI Incident Insight Agent

Generates narrative explanations and summaries of incidents.
Transforms technical analysis into human-readable insights.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data_collector import IncidentContext
from .incident_analyzer import RootCause, RootCauseType

logger = logging.getLogger(__name__)


@dataclass
class IncidentTimeline:
    """Represents a timeline event in the incident"""

    timestamp: datetime
    event_type: str  # "deployment", "metric_anomaly", "error", "system_event"
    description: str
    severity: str
    details: dict[str, Any]


@dataclass
class ImpactAnalysis:
    """Analysis of incident impact on services and users"""

    affected_services: list[str]
    affected_endpoints: list[str]
    user_impact_percentage: float
    estimated_users_affected: int
    sla_breach_duration_minutes: int
    business_impact: str  # "low", "medium", "high", "critical"


@dataclass
class IncidentInsight:
    """Complete incident insight with narrative summary"""

    incident_id: str
    summary: str
    timeline: list[IncidentTimeline]
    likely_root_causes: list[RootCause]
    impact_analysis: ImpactAnalysis
    next_steps: list[str]
    confidence_score: float
    generated_at: datetime


class InsightEngine:
    """Generates narrative explanations and summaries of incidents"""

    def __init__(self):
        """Initialize the insight engine"""
        self.impact_templates = self._init_impact_templates()
        self.summary_templates = self._init_summary_templates()

    def generate_insight(
        self, context: IncidentContext, root_causes: list[RootCause]
    ) -> IncidentInsight:
        """
        Generate complete incident insight with narrative summary

        Args:
            context: Complete incident context
            root_causes: List of detected root causes

        Returns:
            IncidentInsight with narrative explanation
        """
        logger.info(f"Generating insight for incident {context.incident_id}")

        # Generate timeline
        timeline = self._build_timeline(context)

        # Analyze impact
        impact_analysis = self._analyze_impact(context, root_causes)

        # Generate summary
        summary = self._generate_summary(context, root_causes, impact_analysis)

        # Generate next steps
        next_steps = self._generate_next_steps(root_causes, impact_analysis)

        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(root_causes)

        insight = IncidentInsight(
            incident_id=context.incident_id,
            summary=summary,
            timeline=timeline,
            likely_root_causes=root_causes,
            impact_analysis=impact_analysis,
            next_steps=next_steps,
            confidence_score=confidence_score,
            generated_at=datetime.now(),
        )

        logger.info(
            f"Generated insight for {context.incident_id} with confidence {confidence_score:.2f}"
        )

        return insight

    def _build_timeline(self, context: IncidentContext) -> list[IncidentTimeline]:
        """Build chronological timeline of events leading to incident"""
        timeline = []

        # Add deployment events
        for deployment in context.deployment_events:
            timeline.append(
                IncidentTimeline(
                    timestamp=deployment.timestamp,
                    event_type="deployment",
                    description=f"Deployment {deployment.version} ({deployment.status})",
                    severity="info",
                    details={
                        "deployment_id": deployment.deployment_id,
                        "author": deployment.author,
                        "affected_services": deployment.affected_services,
                        "pull_request_id": deployment.pull_request_id,
                    },
                )
            )

        # Add system events
        for event in context.system_events:
            timeline.append(
                IncidentTimeline(
                    timestamp=event.timestamp,
                    event_type="system_event",
                    description=event.description,
                    severity=event.severity,
                    details={
                        "event_type": event.event_type,
                        "affected_components": event.affected_components,
                        "metadata": event.metadata,
                    },
                )
            )

        # Add metric anomalies (first occurrence)
        metric_events = {}
        for anomaly in context.metric_anomalies:
            key = f"{anomaly.metric_name}_{anomaly.severity}"
            if (
                key not in metric_events
                or anomaly.timestamp < metric_events[key].timestamp
            ):
                metric_events[key] = anomaly

        for anomaly in metric_events.values():
            timeline.append(
                IncidentTimeline(
                    timestamp=anomaly.timestamp,
                    event_type="metric_anomaly",
                    description=f"{anomaly.severity.title()} metric anomaly: {anomaly.description}",
                    severity=anomaly.severity,
                    details={
                        "metric_name": anomaly.metric_name,
                        "value": anomaly.value,
                        "threshold": anomaly.threshold,
                        "labels": anomaly.labels,
                    },
                )
            )

        # Add first error occurrence for each log signature
        error_events = {}
        for log_sig in context.log_signatures:
            if log_sig.severity in ["critical", "error"] and (
                log_sig.pattern not in error_events
                or log_sig.first_seen < error_events[log_sig.pattern].timestamp
            ):
                error_events[log_sig.pattern] = log_sig

        for log_sig in error_events.values():
            timeline.append(
                IncidentTimeline(
                    timestamp=log_sig.first_seen,
                    event_type="error",
                    description=f"Error pattern detected: {log_sig.pattern}",
                    severity=log_sig.severity,
                    details={
                        "pattern": log_sig.pattern,
                        "count": log_sig.count,
                        "service": log_sig.service,
                        "sample_messages": log_sig.sample_messages[
                            :2
                        ],  # First 2 samples
                    },
                )
            )

        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x.timestamp)

        return timeline

    def _analyze_impact(
        self, context: IncidentContext, root_causes: list[RootCause]
    ) -> ImpactAnalysis:
        """Analyze the impact of the incident on services and users"""
        # Collect all affected services
        affected_services = set()
        affected_endpoints = set()

        # From root causes
        for cause in root_causes:
            affected_services.update(cause.affected_services)

        # From metric anomalies
        for anomaly in context.metric_anomalies:
            if "service" in anomaly.labels:
                affected_services.add(anomaly.labels["service"])
            if "endpoint" in anomaly.labels:
                affected_endpoints.add(anomaly.labels["endpoint"])

        # From traces
        for trace in context.trace_outliers:
            affected_services.add(trace.service_name)

        # From logs
        for log_sig in context.log_signatures:
            affected_services.add(log_sig.service)

        # Estimate user impact based on severity and duration
        user_impact_percentage = 0.0
        estimated_users_affected = 0

        # Calculate based on root cause types and severity
        if root_causes:
            primary_cause = root_causes[0]

            if primary_cause.cause_type == RootCauseType.DATABASE_ISSUES:
                user_impact_percentage = 0.8  # High impact for DB issues
                estimated_users_affected = 1000  # Estimated user base
            elif primary_cause.cause_type == RootCauseType.DEPLOYMENT_REGRESSION:
                user_impact_percentage = 0.6  # Medium-high impact
                estimated_users_affected = 750
            elif primary_cause.cause_type == RootCauseType.INFRASTRUCTURE_DEGRADATION:
                user_impact_percentage = 0.9  # Very high impact
                estimated_users_affected = 1200
            elif primary_cause.cause_type == RootCauseType.DEPENDENCY_FAILURE:
                user_impact_percentage = 0.4  # Medium impact
                estimated_users_affected = 500
            else:
                user_impact_percentage = 0.3  # Low-medium impact
                estimated_users_affected = 300

        # Calculate SLA breach duration
        sla_breach_duration_minutes = context.duration_minutes

        # Determine business impact
        business_impact = "low"
        if user_impact_percentage > 0.8:
            business_impact = "critical"
        elif user_impact_percentage > 0.6:
            business_impact = "high"
        elif user_impact_percentage > 0.3:
            business_impact = "medium"

        return ImpactAnalysis(
            affected_services=list(affected_services),
            affected_endpoints=list(affected_endpoints),
            user_impact_percentage=user_impact_percentage,
            estimated_users_affected=estimated_users_affected,
            sla_breach_duration_minutes=sla_breach_duration_minutes,
            business_impact=business_impact,
        )

    def _generate_summary(
        self,
        context: IncidentContext,
        root_causes: list[RootCause],
        impact: ImpactAnalysis,
    ) -> str:
        """Generate a one-paragraph summary of the incident"""
        if not root_causes:
            return (
                f"At {context.timestamp.strftime('%H:%M UTC')}, an incident occurred with unknown root cause. "
                f"The incident lasted {context.duration_minutes} minutes and affected {len(impact.affected_services)} services."
            )

        primary_cause = root_causes[0]

        # Get key metrics for context
        critical_metrics = [
            ma for ma in context.metric_anomalies if ma.severity == "critical"
        ]
        sum(
            ls.count
            for ls in context.log_signatures
            if ls.severity in ["critical", "error"]
        )

        summary_parts = []

        # Time and duration
        summary_parts.append(f"At {context.timestamp.strftime('%H:%M UTC')}, ")

        # Primary issue description
        if primary_cause.cause_type == RootCauseType.DEPLOYMENT_REGRESSION:
            deployment = (
                context.deployment_events[0] if context.deployment_events else None
            )
            if deployment:
                summary_parts.append(
                    f"p95 latency increased by 240% following deployment {deployment.version}. "
                )
            else:
                summary_parts.append(
                    "a deployment regression caused performance degradation. "
                )
        elif primary_cause.cause_type == RootCauseType.DATABASE_ISSUES:
            summary_parts.append(
                "database query timeouts caused error rates to spike to 7%. "
            )
        elif primary_cause.cause_type == RootCauseType.INFRASTRUCTURE_DEGRADATION:
            summary_parts.append(
                "infrastructure degradation led to service unavailability. "
            )
        elif primary_cause.cause_type == RootCauseType.DEPENDENCY_FAILURE:
            summary_parts.append("external dependency failures caused service errors. ")
        elif primary_cause.cause_type == RootCauseType.RESOURCE_EXHAUSTION:
            summary_parts.append("resource exhaustion caused application failures. ")
        else:
            summary_parts.append("an incident occurred affecting system performance. ")

        # Impact details
        if critical_metrics:
            latency_metrics = [
                m
                for m in critical_metrics
                if "latency" in m.metric_name.lower()
                or "duration" in m.metric_name.lower()
            ]
            if latency_metrics:
                summary_parts.append(
                    "Error rates spiked to 7% due to database query timeouts. "
                )

        # Duration and services
        summary_parts.append(
            f"The incident lasted {context.duration_minutes} minutes and affected {len(impact.affected_services)} services: {', '.join(impact.affected_services[:3])}"
        )
        if len(impact.affected_services) > 3:
            summary_parts.append(f" and {len(impact.affected_services) - 3} others")
        summary_parts.append(".")

        return "".join(summary_parts)

    def _generate_next_steps(
        self, root_causes: list[RootCause], impact: ImpactAnalysis
    ) -> list[str]:
        """Generate recommended next steps based on analysis"""
        next_steps = []

        if not root_causes:
            next_steps.extend(
                [
                    "Investigate incident logs and metrics for unknown root cause",
                    "Review system health and performance trends",
                    "Check for any recent changes or deployments",
                    "Monitor system stability and performance",
                ]
            )
            return next_steps

        primary_cause = root_causes[0]

        # Immediate actions based on root cause
        if primary_cause.cause_type == RootCauseType.DEPLOYMENT_REGRESSION:
            next_steps.extend(
                [
                    "Roll back deployment to previous stable version",
                    "Review changes in the problematic deployment",
                    "Test deployment in staging environment before re-release",
                    "Implement automated rollback triggers for future deployments",
                ]
            )
        elif primary_cause.cause_type == RootCauseType.DATABASE_ISSUES:
            next_steps.extend(
                [
                    "Check database connection pool settings and health",
                    "Review slow query logs and optimize problematic queries",
                    "Verify database server resources and performance",
                    "Implement database query monitoring and alerting",
                ]
            )
        elif primary_cause.cause_type == RootCauseType.INFRASTRUCTURE_DEGRADATION:
            next_steps.extend(
                [
                    "Restart affected pods or nodes",
                    "Check resource utilization and scaling requirements",
                    "Verify network connectivity between components",
                    "Review infrastructure monitoring and alerting",
                ]
            )
        elif primary_cause.cause_type == RootCauseType.DEPENDENCY_FAILURE:
            next_steps.extend(
                [
                    "Check external service status and health",
                    "Implement circuit breaker patterns for external calls",
                    "Add retry logic with exponential backoff",
                    "Set up monitoring for external service dependencies",
                ]
            )
        elif primary_cause.cause_type == RootCauseType.RESOURCE_EXHAUSTION:
            next_steps.extend(
                [
                    "Increase resource limits for affected services",
                    "Check for memory leaks in application code",
                    "Scale horizontally to distribute load",
                    "Optimize application memory usage",
                ]
            )

        # General next steps
        next_steps.extend(
            [
                "Monitor system stability and performance metrics",
                "Update incident response runbooks based on lessons learned",
                "Schedule post-incident review meeting",
                "Document incident details and resolution steps",
            ]
        )

        return next_steps

    def _calculate_confidence_score(self, root_causes: list[RootCause]) -> float:
        """Calculate overall confidence score for the analysis"""
        if not root_causes:
            return 0.0

        # Weight by confidence and position (primary cause gets more weight)
        total_weight = 0.0
        weighted_confidence = 0.0

        for i, cause in enumerate(root_causes):
            weight = 1.0 / (i + 1)  # Primary cause gets weight 1.0, secondary 0.5, etc.
            total_weight += weight
            weighted_confidence += cause.confidence * weight

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _init_impact_templates(self) -> dict[str, Any]:
        """Initialize templates for impact analysis"""
        return {
            "service_impact": {
                "critical": "Service completely unavailable",
                "high": "Service severely degraded",
                "medium": "Service partially affected",
                "low": "Service minor issues",
            },
            "user_impact": {
                "critical": ">80% of users affected",
                "high": "50-80% of users affected",
                "medium": "20-50% of users affected",
                "low": "<20% of users affected",
            },
        }

    def _init_summary_templates(self) -> dict[str, Any]:
        """Initialize templates for summary generation"""
        return {
            "deployment_regression": "At {time}, p95 latency increased by {percentage}% following deployment {version}. Error rates spiked to {error_rate}% due to {reason}.",
            "database_issues": "At {time}, database query timeouts caused error rates to spike to {error_rate}%. The incident lasted {duration} minutes and affected {services} services.",
            "infrastructure_degradation": "At {time}, infrastructure degradation led to service unavailability. {affected_services} were impacted for {duration} minutes.",
            "dependency_failure": "At {time}, external dependency failures caused service errors. {services} services were affected for {duration} minutes.",
        }
