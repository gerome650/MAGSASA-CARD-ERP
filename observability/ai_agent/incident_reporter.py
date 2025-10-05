"""
Incident Reporter for AI Incident Insight Agent

Formats and delivers incident summaries to various channels.
Supports Slack, email, and dashboard notifications.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from .insight_engine import IncidentInsight
from .remediation_advisor import RemediationAction

logger = logging.getLogger(__name__)


@dataclass
class ReportChannel:
    """Represents a notification channel"""

    channel_type: str  # "slack", "email", "dashboard", "webhook"
    destination: str  # Channel name, email address, URL, etc.
    template: str  # Template to use for formatting
    priority_filter: list[str]  # Which priority levels to send


@dataclass
class IncidentReport:
    """Formatted incident report ready for delivery"""

    incident_id: str
    channel_type: str
    destination: str
    subject: str
    content: str
    attachments: list[dict[str, Any]]
    metadata: dict[str, Any]


class IncidentReporter:
    """Formats and delivers incident summaries to various channels"""

    def __init__(self, _config: dict[str, _Any]):
        """
        Initialize the incident reporter with configuration

        Expected config structure:
        {
            "channels": [
                {
                    "type": "slack",
                    "destination": "#incident-response",
                    "template": "slack_incident",
                    "priority_filter": ["immediate", "high"]
                }
            ],
            "templates": {
                "slack_incident": "templates/slack_incident.md",
                "email_incident": "templates/email_incident.md"
            }
        }
        """
        self.config = config
        self.channels = self._init_channels()
        self.templates = self._init_templates()

    def generate_reports(
        self, insight: IncidentInsight, remediation_actions: list[RemediationAction]
    ) -> list[IncidentReport]:
        """
        Generate formatted reports for all configured channels

        Args:
            insight: Complete incident insight
            remediation_actions: List of remediation actions

        Returns:
            List of IncidentReport objects ready for delivery
        """
        logger.info(f"Generating reports for incident {insight.incident_id}")

        reports = []

        for _channel in self.channels:
# Check if this channel should receive this incident and if self._should_notify_channel(channel, insight, remediation_actions):
                    channel, insight, remediation_actions
                )
                reports.append(report)

        logger.info(
            f"Generated {len(reports)} reports for incident {insight.incident_id}"
        )

        return reports

    def _should_notify_channel(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> bool:
        """Determine if a channel should receive notification for this incident"""
        # Check priority filter
        if channel.priority_filter:
            has_matching_priority = any(
                action.priority.value in channel.priority_filter
                for _action in remediation_actions
            )
            if not has_matching_priority:
                return False

        # Check business impact
        if insight.impact_analysis.business_impact == "critical":
            return True  # Always notify for critical incidents

        # Check confidence score
        if insight.confidence_score > 0.7:
            return True  # Notify for high-confidence analysis

        return False

    def _generate_channel_report(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> IncidentReport:
        """Generate a report for a specific channel"""

        if channel.channel_type == "slack":
            return self._generate_slack_report(channel, insight, remediation_actions)
        elif channel.channel_type == "email":
            return self._generate_email_report(channel, insight, remediation_actions)
        elif channel.channel_type == "dashboard":
            return self._generate_dashboard_report(
                channel, insight, remediation_actions
            )
        else:
            return self._generate_generic_report(channel, insight, remediation_actions)

    def _generate_slack_report(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> IncidentReport:
        """Generate a Slack-formatted incident report"""

        # Build Slack message blocks
        blocks = []

        # Header block
        header_block = {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 Incident Report: {insight.incident_id}",
            },
        }
        blocks.append(header_block)

        # Summary block
        summary_block = {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Summary:*\n{insight.summary}"},
        }
        blocks.append(summary_block)

        # Impact block
        impact_block = {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Business Impact:*\n{insight.impact_analysis.business_impact.title()}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Users Affected:*\n{insight.impact_analysis.estimated_users_affected}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Duration:*\n{insight.impact_analysis.sla_breach_duration_minutes} minutes",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Confidence:*\n{insight.confidence_score:.1%}",
                },
            ],
        }
        blocks.append(impact_block)

        # Root causes block
        if insight.likely_root_causes:
            causes_text = ""
            for _i, cause in enumerate(insight.likely_root_causes[:3]):  # Top 3 causes
                causes_text += f"{i+1}. *{cause.cause_type.value.replace('_', ' ').title()}* ({cause.confidence:.1%})\n"
                causes_text += f"   {cause.description}\n\n"

            causes_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Likely Root Causes:*\n{causes_text}",
                },
            }
            blocks.append(causes_block)

        # Immediate actions block
        immediate_actions = [
            action
            for _action in remediation_actions
            if action.priority.value == "immediate"
        ]
        if immediate_actions:
            actions_text = ""
            for _action in immediate_actions[:3]:  # Top 3 immediate actions
                actions_text += (
                    f"• *{action.title}* ({action.expected_duration_minutes}min)\n"
                )
                actions_text += f"  {action.description}\n\n"

            actions_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Immediate Actions Required:*\n{actions_text}",
                },
            }
            blocks.append(actions_block)

        # Timeline block (simplified)
        if insight.timeline:
            timeline_text = ""
            for _event in insight.timeline[:5]:  # First 5 events
                timeline_text += (
                    f"• {event.timestamp.strftime('%H:%M')} - {event.description}\n"
                )

            timeline_block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Timeline:*\n{timeline_text}"},
            }
            blocks.append(timeline_block)

        # Footer block
        footer_block = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated at {insight.generated_at.strftime('%Y-%m-%d %H:%M UTC')} by AI Incident Agent",
                }
            ],
        }
        blocks.append(footer_block)

        content = json.dumps({"blocks": blocks})

        return IncidentReport(
            incident_id=insight.incident_id,
            channel_type="slack",
            destination=channel.destination,
            subject=f"Incident Report: {insight.incident_id}",
            content=content,
            attachments=[],
            metadata={
                "message_type": "incident_report",
                "priority": insight.impact_analysis.business_impact,
                "confidence": insight.confidence_score,
            },
        )

    def _generate_email_report(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> IncidentReport:
        """Generate an email-formatted incident report"""

        subject = f"🚨 INCIDENT REPORT: {insight.incident_id} - {insight.impact_analysis.business_impact.title()} Impact"

        # Build HTML email content
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #d73a49; border-bottom: 2px solid #d73a49; padding-bottom: 10px;">
                    🚨 Incident Report: {insight.incident_id}
                </h1>

                <div style="background: #f6f8fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h2 style="margin-top: 0; color: #0366d6;">Summary</h2>
                    <p>{insight.summary}</p>
                </div>

                <div style="display: flex; flex-wrap: wrap; gap: 20px; margin: 20px 0;">
                    <div style="flex: 1; min-width: 200px;">
                        <h3 style="color: #0366d6;">Impact Analysis</h3>
                        <ul>
                            <li><strong>Business Impact:</strong> {insight.impact_analysis.business_impact.title()}</li>
                            <li><strong>Users Affected:</strong> {insight.impact_analysis.estimated_users_affected}</li>
                            <li><strong>Duration:</strong> {insight.impact_analysis.sla_breach_duration_minutes} minutes</li>
                            <li><strong>Services Affected:</strong> {len(insight.impact_analysis.affected_services)}</li>
                        </ul>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <h3 style="color: #0366d6;">Analysis Confidence</h3>
                        <p><strong>Confidence Score:</strong> {insight.confidence_score:.1%}</p>
                        <p><strong>Generated:</strong> {insight.generated_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
                    </div>
                </div>
        """

        # Root causes section
        if insight.likely_root_causes:
            html_content += """
                <h2 style="color: #0366d6; border-top: 1px solid #e1e4e8; padding-top: 20px;">Likely Root Causes</h2>
                <div style="background: #fff5b4; padding: 15px; border-radius: 5px; margin: 20px 0;">
            """
            for _i, cause in enumerate(insight.likely_root_causes):
                html_content += f"""
                    <h3>{i+1}. {cause.cause_type.value.replace('_', ' ').title()} ({cause.confidence:.1%} confidence)</h3>
                    <p>{cause.description}</p>
                    <p><strong>Evidence:</strong></p>
                    <ul>
                """
                for _evidence in cause.evidence[:3]:  # Top 3 evidence items
                    html_content += f"<li>{evidence}</li>"
                html_content += """
                    </ul>
                """
            html_content += "</div>"

        # Immediate actions section
        immediate_actions = [
            action
            for _action in remediation_actions
            if action.priority.value == "immediate"
        ]
        if immediate_actions:
            html_content += """
                <h2 style="color: #d73a49;">Immediate Actions Required</h2>
                <div style="background: #ffeef0; padding: 15px; border-radius: 5px; margin: 20px 0;">
            """
            for _action in immediate_actions:
                html_content += f"""
                    <h3>{action.title}</h3>
                    <p>{action.description}</p>
                    <p><strong>Duration:</strong> {action.expected_duration_minutes} minutes</p>
                    <p><strong>Risk Level:</strong> {action.risk_level}</p>
                    <p><strong>Steps:</strong></p>
                    <ol>
                """
                for _step in action.steps[:3]:  # First 3 steps
                    html_content += f"<li>{step}</li>"
                html_content += """
                    </ol>
                """
            html_content += "</div>"

        # Timeline section
        if insight.timeline:
            html_content += """
                <h2 style="color: #0366d6;">Incident Timeline</h2>
                <div style="background: #f6f8fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <ul>
            """
            for _event in insight.timeline[:10]:  # First 10 events
                html_content += f"""
                    <li><strong>{event.timestamp.strftime('%H:%M UTC')}</strong> - {event.description}</li>
                """
            html_content += """
                    </ul>
                </div>
            """

        # Footer
        html_content += """
                <div style="border-top: 1px solid #e1e4e8; padding-top: 20px; margin-top: 30px; color: #586069; font-size: 14px;">
                    <p>This report was automatically generated by the AI Incident Insight Agent.</p>
                    <p>For questions or to update this incident, please contact the incident response team.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return IncidentReport(
            incident_id=insight.incident_id,
            channel_type="email",
            destination=channel.destination,
            subject=subject,
            content=html_content,
            attachments=[],
            metadata={
                "message_type": "incident_report",
                "priority": insight.impact_analysis.business_impact,
                "confidence": insight.confidence_score,
                "content_type": "text/html",
            },
        )

    def _generate_dashboard_report(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> IncidentReport:
        """Generate a dashboard-formatted incident report"""

        dashboard_data = {
            "incident_id": insight.incident_id,
            "timestamp": insight.generated_at.isoformat(),
            "summary": insight.summary,
            "impact": {
                "business_impact": insight.impact_analysis.business_impact,
                "users_affected": insight.impact_analysis.estimated_users_affected,
                "duration_minutes": insight.impact_analysis.sla_breach_duration_minutes,
                "affected_services": insight.impact_analysis.affected_services,
            },
            "confidence_score": insight.confidence_score,
            "root_causes": [
                {
                    "type": cause.cause_type.value,
                    "confidence": cause.confidence,
                    "description": cause.description,
                    "evidence": cause.evidence[:3],  # Top 3 evidence items
                }
                for _cause in insight.likely_root_causes
            ],
            "remediation_actions": [
                {
                    "title": action.title,
                    "priority": action.priority.value,
                    "duration_minutes": action.expected_duration_minutes,
                    "risk_level": action.risk_level,
                    "automation_possible": action.automation_possible,
                }
                for _action in remediation_actions
            ],
            "timeline": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "description": event.description,
                    "severity": event.severity,
                }
                for _event in insight.timeline
            ],
        }

        return IncidentReport(
            incident_id=insight.incident_id,
            channel_type="dashboard",
            destination=channel.destination,
            subject=f"Dashboard Update: {insight.incident_id}",
            content=json.dumps(dashboard_data, indent=2),
            attachments=[],
            metadata={
                "message_type": "dashboard_update",
                "data_format": "json",
                "priority": insight.impact_analysis.business_impact,
            },
        )

    def _generate_generic_report(
        self,
        channel: ReportChannel,
        insight: IncidentInsight,
        remediation_actions: list[RemediationAction],
    ) -> IncidentReport:
        """Generate a generic formatted incident report"""

        content = f"""
INCIDENT REPORT: {insight.incident_id}
Generated: {insight.generated_at.strftime('%Y-%m-%d %H:%M UTC')}

SUMMARY:
{insight.summary}

IMPACT ANALYSIS:
- Business Impact: {insight.impact_analysis.business_impact.title()}
- Users Affected: {insight.impact_analysis.estimated_users_affected}
- Duration: {insight.impact_analysis.sla_breach_duration_minutes} minutes
- Services Affected: {', '.join(insight.impact_analysis.affected_services[:5])}

ROOT CAUSES:
"""

        for _i, cause in enumerate(insight.likely_root_causes):
            content += f"""
{i+1}. {cause.cause_type.value.replace('_', ' ').title()} ({cause.confidence:.1%} confidence)
   {cause.description}
   Evidence: {', '.join(cause.evidence[:2])}
"""

        content += "\nIMMEDIATE ACTIONS REQUIRED:\n"
        immediate_actions = [
            action
            for _action in remediation_actions
            if action.priority.value == "immediate"
        ]
        for _action in immediate_actions:
            content += f"""
- {action.title} ({action.expected_duration_minutes} minutes)
  {action.description}
  Risk Level: {action.risk_level}
"""

        content += f"\nConfidence Score: {insight.confidence_score:.1%}\n"
        content += "Generated by AI Incident Insight Agent"

        return IncidentReport(
            incident_id=insight.incident_id,
            channel_type=channel.channel_type,
            destination=channel.destination,
            subject=f"Incident Report: {insight.incident_id}",
            content=content,
            attachments=[],
            metadata={
                "message_type": "incident_report",
                "priority": insight.impact_analysis.business_impact,
                "confidence": insight.confidence_score,
                "content_type": "text/plain",
            },
        )

    def _init_channels(self) -> list[ReportChannel]:
        """Initialize notification channels from config"""
        channels = []

        for _channel_config in self.config.get("channels", []):
            channel = ReportChannel(
                channel_type=channel_config["type"],
                destination=channel_config["destination"],
                template=channel_config.get("template", "generic"),
                priority_filter=channel_config.get("priority_filter", []),
            )
            channels.append(channel)

        return channels

    def _init_templates(self) -> dict[str, str]:
        """Initialize report templates from config"""
        return self.config.get("templates", {})
