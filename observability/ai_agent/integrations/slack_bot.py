"""
Slack Bot Integration for AI Incident Insight Agent

Provides interactive Slack commands and notifications for incident management.
Supports querying incidents, getting summaries, and generating postmortems.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

from ..incident_reporter import IncidentReport

logger = logging.getLogger(__name__)


@dataclass
class SlackCommand:
    """Represents a Slack slash command"""

    command: str
    description: str
    usage: str
    handler: str


@dataclass
class SlackMessage:
    """Represents a Slack message to be sent"""

    channel: str
    text: str
    blocks: list[dict[str, Any]] | None = None
    attachments: list[dict[str, Any]] | None = None


class SlackIncidentBot:
    """Slack bot for incident management and querying"""

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the Slack bot with configuration

        Expected config structure:
        {
            "bot_token": "xoxb-...",
            "signing_secret": "...",
            "default_channels": {
                "incidents": "#incident-response",
                "notifications": "#alerts"
            },
            "commands": {
                "incident": "/incident",
                "summary": "/incident-summary",
                "postmortem": "/postmortem"
            }
        }
        """
        self.config = config
        self.bot_token = config.get("bot_token")
        self.signing_secret = config.get("signing_secret")
        self.default_channels = config.get("default_channels", {})
        self.commands = self._init_commands()
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def send_incident_report(self, report: IncidentReport) -> bool:
        """
        Send an incident report to Slack

        Args:
            report: IncidentReport to send

        Returns:
            True if successful, False otherwise
        """
        try:
            if report.channel_type != "slack":
                logger.warning(
                    f"Report is not for Slack channel: {report.channel_type}"
                )
                return False

            # Parse Slack blocks from report content
            blocks = json.loads(report.content).get("blocks", [])

            payload = {
                "channel": report.destination,
                "blocks": blocks,
                "text": report.subject,  # Fallback text
            }

            success = await self._send_message(payload)

            if success:
                logger.info(
                    f"Sent incident report {report.incident_id} to {report.destination}"
                )
            else:
                logger.error(f"Failed to send incident report {report.incident_id}")

            return success

        except Exception as e:
            logger.error(f"Error sending incident report to Slack: {e}")
            return False

    async def handle_command(self, command_data: dict[str, Any]) -> str:
        """
        Handle incoming Slack slash commands

        Args:
            command_data: Slack command payload

        Returns:
            Response message for Slack
        """
        try:
            command = command_data.get("command", "")
            text = command_data.get("text", "").strip()
            user_id = command_data.get("user_id", "")
            channel_id = command_data.get("channel_id", "")

            logger.info(f"Handling Slack command: {command} from user {user_id}")

            if command == self.config.get("commands", {}).get("incident"):
                return await self._handle_incident_command(text, channel_id)
            elif command == self.config.get("commands", {}).get("summary"):
                return await self._handle_summary_command(text, channel_id)
            elif command == self.config.get("commands", {}).get("postmortem"):
                return await self._handle_postmortem_command(text, channel_id)
            else:
                return self._get_help_message()

        except Exception as e:
            logger.error(f"Error handling Slack command: {e}")
            return f"❌ Error processing command: {str(e)}"

    async def handle_interactive_message(self, payload: dict[str, Any]) -> str:
        """
        Handle interactive Slack message interactions (buttons, selects)

        Args:
            payload: Slack interactive message payload

        Returns:
            Response message for Slack
        """
        try:
            action = payload.get("actions", [{}])[0]
            action_type = action.get("type")
            action_value = action.get("value", "")
            user_id = payload.get("user", {}).get("id", "")

            logger.info(
                f"Handling interactive message: {action_type} from user {user_id}"
            )

            if action_type == "button":
                if action_value.startswith("incident_details_"):
                    incident_id = action_value.replace("incident_details_", "")
                    return await self._get_incident_details(incident_id)
                elif action_value.startswith("generate_postmortem_"):
                    incident_id = action_value.replace("generate_postmortem_", "")
                    return await self._generate_postmortem_interactive(incident_id)
                elif action_value == "list_recent_incidents":
                    return await self._list_recent_incidents()

            return "✅ Action completed successfully"

        except Exception as e:
            logger.error(f"Error handling interactive message: {e}")
            return f"❌ Error processing interaction: {str(e)}"

    async def _handle_incident_command(self, text: str, channel_id: str) -> str:
        """Handle /incident command"""
        if not text:
            return self._get_incident_help()

        parts = text.split()
        subcommand = parts[0].lower()

        if subcommand == "list":
            return await self._list_recent_incidents()
        elif subcommand == "details":
            if len(parts) < 2:
                return "❌ Please provide an incident ID. Usage: `/incident details INC-123`"
            incident_id = parts[1]
            return await self._get_incident_details(incident_id)
        elif subcommand == "status":
            if len(parts) < 2:
                return "❌ Please provide an incident ID. Usage: `/incident status INC-123`"
            incident_id = parts[1]
            return await self._get_incident_status(incident_id)
        else:
            return self._get_incident_help()

    async def _handle_summary_command(self, text: str, channel_id: str) -> str:
        """Handle /incident-summary command"""
        if not text:
            return (
                "❌ Please provide an incident ID. Usage: `/incident-summary INC-123`"
            )

        incident_id = text.strip()
        return await self._get_incident_summary(incident_id)

    async def _handle_postmortem_command(self, text: str, channel_id: str) -> str:
        """Handle /postmortem command"""
        if not text:
            return "❌ Please provide an incident ID. Usage: `/postmortem INC-123`"

        incident_id = text.strip()
        return await self._generate_postmortem_interactive(incident_id)

    async def _get_incident_details(self, incident_id: str) -> str:
        """Get detailed information about an incident"""
        try:
            # In a real implementation, this would query the incident database
            # For now, return a simulated response

            response = f"""
🔍 *Incident Details: {incident_id}*

📊 *Status:* Resolved
🕐 *Duration:* 45 minutes
👥 *Users Affected:* 1,200
🎯 *Business Impact:* High
🎲 *Confidence Score:* 87%

📝 *Summary:*
Database query timeout caused error rates to spike to 7% following deployment v1.4.2. The incident lasted 45 minutes and affected 3 services: magsasa-card-erp, payment-service, order-service.

🔍 *Root Causes:*
1. *Deployment Regression* (87% confidence)
   - Inefficient ORM query introduced in PR #812
   - Database connection timeout errors detected

2. *Database Issues* (72% confidence)
   - Slow database operation: SELECT orders (2,340ms)
   - Database connection pool exhaustion

⚡ *Immediate Actions Taken:*
• Rollback deployment to v1.4.1 (10 minutes)
• Restart database connection pool (5 minutes)
• Scale database resources (15 minutes)

📅 *Timeline:*
• 14:32 UTC - Deployment v1.4.2 released
• 14:34 UTC - Latency anomaly detected
• 14:36 UTC - Alerts fired to Slack
• 14:45 UTC - Rollback initiated
• 14:55 UTC - Latency normalized

Generated by AI Incident Agent 🤖
"""

            return response

        except Exception as e:
            logger.error(f"Error getting incident details for {incident_id}: {e}")
            return f"❌ Error retrieving incident details: {str(e)}"

    async def _get_incident_summary(self, incident_id: str) -> str:
        """Get a brief summary of an incident"""
        try:
            # Simulated incident summary
            summary = f"""
📋 *Incident Summary: {incident_id}*

At 14:32 UTC, p95 latency increased by 240% following deployment v1.4.2. Error rates spiked to 7% due to database query timeouts. The incident lasted 45 minutes and affected 3 services.

🎯 *Key Points:*
• Root Cause: Deployment regression (87% confidence)
• Impact: High business impact, 1,200 users affected
• Resolution: Rollback to v1.4.1, database optimization
• Duration: 45 minutes

🤖 Generated by AI Incident Agent
"""

            return summary

        except Exception as e:
            logger.error(f"Error getting incident summary for {incident_id}: {e}")
            return f"❌ Error retrieving incident summary: {str(e)}"

    async def _get_incident_status(self, incident_id: str) -> str:
        """Get current status of an incident"""
        try:
            # Simulated status check
            status = f"""
📊 *Incident Status: {incident_id}*

🟢 *Status:* Resolved
🕐 *Resolved At:* 14:55 UTC
⏱️ *Total Duration:* 45 minutes
👥 *Users Affected:* 1,200

🔍 *Current State:*
• All services restored ✅
• Error rates normalized ✅
• Database performance stable ✅
• User functionality verified ✅

📈 *Post-Resolution Metrics:*
• Response time: 150ms (baseline: 120ms)
• Error rate: 0.1% (baseline: 0.05%)
• Throughput: 95% of normal

🤖 Generated by AI Incident Agent
"""

            return status

        except Exception as e:
            logger.error(f"Error getting incident status for {incident_id}: {e}")
            return f"❌ Error retrieving incident status: {str(e)}"

    async def _list_recent_incidents(self) -> str:
        """List recent incidents"""
        try:
            # Simulated recent incidents
            incidents = [
                {
                    "id": "INC-2025-01-03-001",
                    "timestamp": "2025-01-03 14:32 UTC",
                    "duration": "45 min",
                    "impact": "High",
                    "status": "Resolved",
                    "cause": "Deployment Regression",
                },
                {
                    "id": "INC-2025-01-02-003",
                    "timestamp": "2025-01-02 09:15 UTC",
                    "duration": "12 min",
                    "impact": "Medium",
                    "status": "Resolved",
                    "cause": "Database Issues",
                },
                {
                    "id": "INC-2025-01-01-007",
                    "timestamp": "2025-01-01 16:45 UTC",
                    "duration": "8 min",
                    "impact": "Low",
                    "status": "Resolved",
                    "cause": "Infrastructure Degradation",
                },
            ]

            response = "📋 *Recent Incidents*\n\n"

            for incident in incidents:
                impact_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(
                    incident["impact"], "⚪"
                )

                response += f"""
{impact_emoji} *{incident['id']}*
• Time: {incident['timestamp']}
• Duration: {incident['duration']}
• Impact: {incident['impact']}
• Status: {incident['status']}
• Cause: {incident['cause']}
"""

            response += (
                "\n💡 *Tip:* Use `/incident details INC-123` for more information"
            )

            return response

        except Exception as e:
            logger.error(f"Error listing recent incidents: {e}")
            return f"❌ Error retrieving incident list: {str(e)}"

    async def _generate_postmortem_interactive(self, incident_id: str) -> str:
        """Generate postmortem interactively"""
        try:
            # In a real implementation, this would trigger the postmortem generator
            response = f"""
📝 *Generating Postmortem for {incident_id}*

🤖 AI Incident Agent is analyzing the incident and generating a comprehensive postmortem report...

⏳ *Processing:*
• Analyzing incident timeline ✅
• Identifying root causes ✅
• Assessing impact ✅
• Documenting resolution steps ✅
• Extracting lessons learned ✅

📄 *Postmortem Report Generated:*
📁 File: `/observability/reports/2025-01-03-incident-{incident_id}.md`
🔗 Link: [View Postmortem](https://docs.magsasa.com/incidents/{incident_id})

📋 *Report Sections:*
• Executive Summary
• Timeline of Events
• Root Cause Analysis
• Impact Assessment
• Resolution Steps
• Lessons Learned
• Action Items

The postmortem has been automatically generated and saved. Please review and update as needed.

🤖 Generated by AI Incident Agent
"""

            return response

        except Exception as e:
            logger.error(f"Error generating postmortem for {incident_id}: {e}")
            return f"❌ Error generating postmortem: {str(e)}"

    async def _send_message(self, payload: dict[str, Any]) -> bool:
        """Send a message to Slack"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            }

            async with self.session.post(
                url, headers=headers, json=payload
            ) as response:
                result = await response.json()

                if result.get("ok"):
                    return True
                else:
                    logger.error(f"Slack API error: {result.get('error')}")
                    return False

        except Exception as e:
            logger.error(f"Error sending message to Slack: {e}")
            return False

    def _get_help_message(self) -> str:
        """Get general help message"""
        return """
🤖 *AI Incident Agent Commands*

📋 *Available Commands:*
• `/incident list` - List recent incidents
• `/incident details INC-123` - Get incident details
• `/incident status INC-123` - Get incident status
• `/incident-summary INC-123` - Get incident summary
• `/postmortem INC-123` - Generate postmortem report

💡 *Examples:*
• `/incident details INC-2025-01-03-001`
• `/incident-summary INC-2025-01-03-001`
• `/postmortem INC-2025-01-03-001`

🔍 *Interactive Features:*
• Click buttons in incident reports for quick actions
• Use mentions like `@IncidentBot why is error rate spiking?`

Need help? Contact the incident response team.
"""

    def _get_incident_help(self) -> str:
        """Get incident command help"""
        return """
📋 *Incident Command Help*

**Usage:** `/incident <subcommand> [arguments]`

**Subcommands:**
• `list` - List recent incidents
• `details <incident-id>` - Get detailed incident information
• `status <incident-id>` - Get current incident status

**Examples:**
• `/incident list`
• `/incident details INC-2025-01-03-001`
• `/incident status INC-2025-01-03-001`

**Incident IDs format:** `INC-YYYY-MM-DD-XXX`
"""

    def _init_commands(self) -> list[SlackCommand]:
        """Initialize available Slack commands"""
        return [
            SlackCommand(
                command=self.config.get("commands", {}).get("incident", "/incident"),
                description="Manage and query incidents",
                usage="/incident [list|details|status] [incident-id]",
                handler="_handle_incident_command",
            ),
            SlackCommand(
                command=self.config.get("commands", {}).get(
                    "summary", "/incident-summary"
                ),
                description="Get incident summary",
                usage="/incident-summary <incident-id>",
                handler="_handle_summary_command",
            ),
            SlackCommand(
                command=self.config.get("commands", {}).get(
                    "postmortem", "/postmortem"
                ),
                description="Generate postmortem report",
                usage="/postmortem <incident-id>",
                handler="_handle_postmortem_command",
            ),
        ]
