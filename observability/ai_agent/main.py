"""
Main AI Incident Insight Agent

Orchestrates the complete incident analysis workflow:
1. Collect incident context from all telemetry sources
2. Analyze incident to identify root causes
3. Generate insights and remediation recommendations
4. Send notifications to Slack and PagerDuty
5. Generate postmortem reports
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data_collector import IncidentContextCollector
from .incident_analyzer import IncidentAnalyzer
from .incident_reporter import IncidentReporter
from .insight_engine import InsightEngine
from .integrations.pagerduty_notifier import PagerDutyNotifier
from .integrations.slack_bot import SlackIncidentBot
from .postmortem_generator import PostmortemGenerator
from .remediation_advisor import RemediationAdvisor

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for the AI Incident Insight Agent"""

    # Data collection
    prometheus_url: str = "http://localhost:9090"
    jaeger_url: str = "http://localhost:16686"
    loki_url: str = "http://localhost:3100"
    github_token: str | None = None

    # Notification channels
    slack_bot_token: str | None = None
    slack_channels: dict[str, str] = None
    pagerduty_token: str | None = None
    pagerduty_integration_keys: dict[str, str] = None

    # Postmortem generation
    reports_dir: str = "/observability/reports"

    # Analysis parameters
    analysis_window_minutes: int = 30
    confidence_threshold: float = 0.3


class AIIncidentAgent:
    """Main AI Incident Insight Agent orchestrator"""

    def __init__(self, config: AgentConfig):
        """
        Initialize the AI Incident Agent

        Args:
            config: Agent configuration
        """
        self.config = config

        # Initialize components
        self.data_collector = IncidentContextCollector(self._get_collector_config())
        self.incident_analyzer = IncidentAnalyzer()
        self.insight_engine = InsightEngine()
        self.remediation_advisor = RemediationAdvisor()
        self.incident_reporter = IncidentReporter(self._get_reporter_config())
        self.postmortem_generator = PostmortemGenerator(config.reports_dir)

        # Initialize integrations
        self.slack_bot = None
        self.pagerduty_notifier = None

        if config.slack_bot_token:
            self.slack_bot = SlackIncidentBot(self._get_slack_config())

        if config.pagerduty_token:
            self.pagerduty_notifier = PagerDutyNotifier(self._get_pagerduty_config())

    async def analyze_incident(
        self,
        incident_id: str,
        alert_payload: dict[str, Any],
        resolution_notes: str | None = None,
        engineer_notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Complete incident analysis workflow

        Args:
            incident_id: Unique incident identifier
            alert_payload: Alertmanager webhook payload
            resolution_notes: Optional resolution notes
            engineer_notes: Optional engineer notes

        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Starting incident analysis for {incident_id}")

        try:
            # Step 1: Collect incident context
            logger.info("Step 1: Collecting incident context")
            context = await self.data_collector.collect_incident_context(
                incident_id, alert_payload, self.config.analysis_window_minutes
            )

            # Step 2: Analyze incident for root causes
            logger.info("Step 2: Analyzing incident for root causes")
            root_causes = self.incident_analyzer.analyze_incident(context)

            # Filter root causes by confidence threshold
            root_causes = [
                cause
                for cause in root_causes
                if cause.confidence >= self.config.confidence_threshold
            ]

            # Step 3: Generate insights
            logger.info("Step 3: Generating incident insights")
            insight = self.insight_engine.generate_insight(context, root_causes)

            # Step 4: Generate remediation plan
            logger.info("Step 4: Generating remediation recommendations")
            remediation_actions = self.remediation_advisor.generate_remediation_plan(
                insight
            )

            # Step 5: Generate reports for all channels
            logger.info("Step 5: Generating incident reports")
            reports = self.incident_reporter.generate_reports(
                insight, remediation_actions
            )

            # Step 6: Send notifications
            logger.info("Step 6: Sending notifications")
            notification_results = await self._send_notifications(
                insight, remediation_actions, reports
            )

            # Step 7: Generate postmortem
            logger.info("Step 7: Generating postmortem report")
            postmortem = self.postmortem_generator.generate_postmortem(
                insight, remediation_actions, resolution_notes, engineer_notes
            )

            # Compile results
            results = {
                "incident_id": incident_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "context": context.to_dict(),
                "root_causes": [
                    {
                        "type": cause.cause_type.value,
                        "confidence": cause.confidence,
                        "description": cause.description,
                        "evidence": cause.evidence,
                        "affected_services": cause.affected_services,
                    }
                    for cause in root_causes
                ],
                "insight": {
                    "summary": insight.summary,
                    "confidence_score": insight.confidence_score,
                    "business_impact": insight.impact_analysis.business_impact,
                    "users_affected": insight.impact_analysis.estimated_users_affected,
                    "timeline": [
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "event_type": event.event_type,
                            "description": event.description,
                            "severity": event.severity,
                        }
                        for event in insight.timeline
                    ],
                },
                "remediation_actions": [
                    {
                        "title": action.title,
                        "priority": action.priority.value,
                        "duration_minutes": action.expected_duration_minutes,
                        "risk_level": action.risk_level,
                        "automation_possible": action.automation_possible,
                    }
                    for action in remediation_actions
                ],
                "reports_generated": len(reports),
                "notification_results": notification_results,
                "postmortem": {
                    "file_path": postmortem.file_path,
                    "sections_count": len(postmortem.sections),
                },
            }

            logger.info(f"Completed incident analysis for {incident_id}")
            return results

        except Exception as e:
            logger.error(f"Error analyzing incident {incident_id}: {e}")
            raise

    async def _send_notifications(
        self, insight, remediation_actions, reports
    ) -> dict[str, Any]:
        """Send notifications to all configured channels"""
        results = {}

        # Send Slack notifications
        if self.slack_bot:
            try:
                async with self.slack_bot:
                    slack_reports = [r for r in reports if r.channel_type == "slack"]
                    slack_success = 0

                    for report in slack_reports:
                        if await self.slack_bot.send_incident_report(report):
                            slack_success += 1

                    results["slack"] = {
                        "success": slack_success,
                        "total": len(slack_reports),
                    }
            except Exception as e:
                logger.error(f"Error sending Slack notifications: {e}")
                results["slack"] = {"error": str(e)}

        # Send PagerDuty notifications
        if self.pagerduty_notifier:
            try:
                pagerduty_success = await self.pagerduty_notifier.send_incident_alert(
                    insight, remediation_actions
                )
                results["pagerduty"] = {"success": pagerduty_success}
            except Exception as e:
                logger.error(f"Error sending PagerDuty notifications: {e}")
                results["pagerduty"] = {"error": str(e)}

        return results

    def _get_collector_config(self) -> dict[str, Any]:
        """Get configuration for data collector"""
        return {
            "prometheus": {"base_url": self.config.prometheus_url},
            "jaeger": {"base_url": self.config.jaeger_url},
            "loki": {"base_url": self.config.loki_url},
            "github": {
                "api_url": "https://api.github.com",
                "token": self.config.github_token,
            },
        }

    def _get_reporter_config(self) -> dict[str, Any]:
        """Get configuration for incident reporter"""
        channels = []

        # Add Slack channel if configured
        if self.config.slack_bot_token and self.config.slack_channels:
            channels.append(
                {
                    "type": "slack",
                    "destination": self.config.slack_channels.get(
                        "incidents", "#incident-response"
                    ),
                    "template": "slack_incident",
                    "priority_filter": ["immediate", "high"],
                }
            )

        return {
            "channels": channels,
            "templates": {
                "slack_incident": "templates/slack_incident.md",
                "email_incident": "templates/email_incident.md",
            },
        }

    def _get_slack_config(self) -> dict[str, Any]:
        """Get configuration for Slack bot"""
        return {
            "bot_token": self.config.slack_bot_token,
            "default_channels": self.config.slack_channels or {},
            "commands": {
                "incident": "/incident",
                "summary": "/incident-summary",
                "postmortem": "/postmortem",
            },
        }

    def _get_pagerduty_config(self) -> dict[str, Any]:
        """Get configuration for PagerDuty notifier"""
        return {
            "api_token": self.config.pagerduty_token,
            "integration_keys": self.config.pagerduty_integration_keys or {},
            "default_routing": {
                "critical": "incidents",
                "high": "incidents",
                "medium": "alerts",
                "low": "alerts",
            },
        }


# Example usage and CLI interface
async def main():
    """Example usage of the AI Incident Agent"""

    # Sample alert payload (simulating Alertmanager webhook)
    sample_alert = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighLatency",
                    "service": "magsasa-card-erp",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "High latency detected",
                    "description": "p95 latency is above threshold",
                },
                "startsAt": datetime.now().isoformat(),
                "endsAt": "0001-01-01T00:00:00Z",
            }
        ],
        "groupLabels": {"alertname": "HighLatency"},
        "commonLabels": {"service": "magsasa-card-erp"},
        "commonAnnotations": {"summary": "High latency detected"},
        "externalURL": "http://localhost:9093",
        "version": "4",
        "groupKey": "{}:{}",
    }

    # Create agent configuration
    config = AgentConfig(
        prometheus_url="http://localhost:9090",
        jaeger_url="http://localhost:16686",
        loki_url="http://localhost:3100",
        slack_bot_token="xoxb-your-slack-token",
        slack_channels={"incidents": "#incident-response", "notifications": "#alerts"},
        pagerduty_token="your-pagerduty-token",
        pagerduty_integration_keys={
            "incidents": "your-incidents-integration-key",
            "alerts": "your-alerts-integration-key",
        },
        reports_dir="/observability/reports",
    )

    # Initialize and run agent
    agent = AIIncidentAgent(config)

    try:
        results = await agent.analyze_incident(
            incident_id="INC-2025-01-03-001",
            alert_payload=sample_alert,
            resolution_notes="Rolled back deployment and optimized database queries",
            engineer_notes="Team responded quickly. Need to improve pre-deployment testing.",
        )

        print("Incident analysis completed successfully!")
        print(f"Results: {json.dumps(results, indent=2)}")

    except Exception as e:
        print(f"Error running incident analysis: {e}")


if __name__ == "__main__":
    asyncio.run(main())
