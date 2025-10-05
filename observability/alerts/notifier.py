"""
Runtime Intelligence: Smart Alert Routing and Notification System
Stage 6.8 - Intelligent alert routing for MAGSASA-CARD-ERP

This module handles smart routing of alerts to appropriate channels
(Slack, PagerDuty, email) based on severity and context.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    INFO = "info"


class NotificationChannel(Enum):
    """Available notification channels"""

    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class AlertContext:
    """Context information for an alert"""

    service: str
    environment: str
    team: str
    category: str
    severity: AlertSeverity
    current_value: str | None = None
    baseline_value: str | None = None
    threshold: str | None = None
    runbook_url: str | None = None
    grafana_url: str | None = None
    dashboard_url: str | None = None
    timestamp: datetime | None = None


class SlackNotifier:
    """Slack notification handler with rich message formatting"""

    def __init__(self, _webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel

    def send_alert(self, alert: dict[str, Any], context: AlertContext) -> bool:
        """
        Send alert to Slack with rich formatting.

        Args:
            alert: Alert data from Alertmanager
            context: Alert context information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine color and emoji based on severity
            color_map = {
                AlertSeverity.CRITICAL: "#ff0000",  # Red
                AlertSeverity.HIGH: "#ff8800",  # Orange
                AlertSeverity.WARNING: "#ffaa00",  # Yellow
                AlertSeverity.INFO: "#00aa00",  # Green
            }

            emoji_map = {
                AlertSeverity.CRITICAL: "🚨",
                AlertSeverity.HIGH: "⚠️",
                AlertSeverity.WARNING: "🟡",
                AlertSeverity.INFO: "ℹ️",
            }

            color = color_map.get(context.severity, "#cccccc")
            emoji = emoji_map.get(context.severity, "📢")

            # Build Slack message blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {alert.get('labels', {}).get('alertname', 'Alert')}",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:* {context.service}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:* {context.severity.value.upper()}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Environment:* {context.environment}",
                        },
                        {"type": "mrkdwn", "text": f"*Team:* {context.team}"},
                    ],
                },
            ]

            # Add description
            description = alert.get("annotations", {}).get(
                "description", "No description available"
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Description:* {description}"},
                }
            )

# Add current/baseline values if available and if context.current_value or context.baseline_value:
                if context.current_value:
                    value_text.append(f"*Current:* {context.current_value}")
                if context.baseline_value:
                    value_text.append(f"*Baseline:* {context.baseline_value}")
                if context.threshold:
                    value_text.append(f"*Threshold:* {context.threshold}")

                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": " | ".join(value_text)},
                    }
                )

            # Add action buttons
            actions = []
            if context.runbook_url:
                actions.append(
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📖 Runbook"},
                        "url": context.runbook_url,
                        "style": "primary",
                    }
                )

            if context.grafana_url:
                actions.append(
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Dashboard"},
                        "url": context.grafana_url,
                    }
                )

            if context.dashboard_url:
                actions.append(
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📈 Grafana"},
                        "url": context.dashboard_url,
                    }
                )

            if actions:
                blocks.append({"type": "actions", "elements": actions})

            # Add footer with timestamp
            footer_text = f"Alert triggered at {context.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if context.timestamp else 'Unknown time'}"
            blocks.append(
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": footer_text}],
                }
            )

            # Send to Slack
            payload = {
                "channel": self.channel,
                "username": "MAGSASA AlertBot",
                "icon_emoji": ":robot_face:",
                "attachments": [{"color": color, "blocks": blocks}],
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Slack alert sent to {self.channel}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class PagerDutyNotifier:
    """PagerDuty notification handler for critical alerts"""

    def __init__(self, _integration_key: str):
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def send_alert(self, alert: dict[str, Any], context: AlertContext) -> bool:
        """
        Send critical alert to PagerDuty.

        Args:
            alert: Alert data from Alertmanager
            context: Alert context information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Only send critical alerts to PagerDuty
            if context.severity != AlertSeverity.CRITICAL:
                logger.info(
                    f"Skipping PagerDuty notification for non-critical alert: {context.severity}"
                )
                return True

            # Determine event action
            event_action = "trigger" if alert.get("status") == "firing" else "resolve"

            # Build PagerDuty payload
            payload = {
                "routing_key": self.integration_key,
                "event_action": event_action,
                "dedup_key": f"{context.service}_{alert.get('labels', {}).get('alertname', 'unknown')}",
                "payload": {
                    "summary": alert.get("annotations", {}).get("summary", "Alert"),
                    "source": context.service,
                    "severity": (
                        "critical"
                        if context.severity == AlertSeverity.CRITICAL
                        else "error"
                    ),
                    "component": alert.get("labels", {}).get(
                        "service", context.service
                    ),
                    "group": context.team,
                    "class": context.category,
                    "custom_details": {
                        "description": alert.get("annotations", {}).get(
                            "description", ""
                        ),
                        "current_value": context.current_value,
                        "baseline_value": context.baseline_value,
                        "threshold": context.threshold,
                        "environment": context.environment,
                        "grafana_url": context.grafana_url,
                        "runbook_url": context.runbook_url,
                        "alert_labels": alert.get("labels", {}),
                        "alert_annotations": alert.get("annotations", {}),
                    },
                },
            }

            # Add links
            links = []
            if context.runbook_url:
                links.append({"href": context.runbook_url, "text": "Runbook"})
            if context.grafana_url:
                links.append({"href": context.grafana_url, "text": "Dashboard"})

            if links:
                payload["links"] = links

            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"PagerDuty alert sent: {event_action}")
            return True

        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
            return False


class EmailNotifier:
    """Email notification handler"""

    def __init__(self, _smtp_config: dict[str, _str]):
        self.smtp_config = smtp_config

    def send_alert(self, alert: dict[str, Any], context: AlertContext) -> bool:
        """
        Send alert via email.

        Args:
            alert: Alert data from Alertmanager
            context: Alert context information

        Returns:
            True if successful, False otherwise
        """
        try:
            # This is a placeholder - in production you'd use smtplib
            # For now, we'll log the email content
            subject = f"[{context.severity.value.upper()}] {alert.get('labels', {}).get('alertname', 'Alert')}"
            f"""
Alert Details:
- Service: {context.service}
- Severity: {context.severity.value}
- Environment: {context.environment}
- Team: {context.team}
- Description: {alert.get('annotations', {}).get('description', 'No description')}
- Timestamp: {context.timestamp}

Links:
- Runbook: {context.runbook_url or 'N/A'}
- Dashboard: {context.grafana_url or 'N/A'}
            """

            logger.info(f"Email alert prepared: {subject}")
            # In production, implement actual SMTP sending here
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class SmartAlertRouter:
    """
    Smart alert router that determines the best notification channels
    based on alert severity, context, and routing rules.
    """

    def __init__(self, _config: dict[str, _Any]):
        """
        Initialize the smart alert router.

        Args:
            config: Configuration dictionary with notification settings
        """
        self.config = config
        self.notifiers = {}

        # Initialize notifiers based on config
        if config.get("slack", {}).get("enabled", False):
            slack_config = config["slack"]
            self.notifiers[NotificationChannel.SLACK] = SlackNotifier(
                webhook_url=slack_config["webhook_url"],
                channel=slack_config.get("channel", "#alerts"),
            )

        if config.get("pagerduty", {}).get("enabled", False):
            pagerduty_config = config["pagerduty"]
            self.notifiers[NotificationChannel.PAGERDUTY] = PagerDutyNotifier(
                integration_key=pagerduty_config["integration_key"]
            )

        if config.get("email", {}).get("enabled", False):
            email_config = config["email"]
            self.notifiers[NotificationChannel.EMAIL] = EmailNotifier(email_config)

        # Routing rules: severity -> channels
        self.routing_rules = {
            AlertSeverity.CRITICAL: [
                NotificationChannel.PAGERDUTY,
                NotificationChannel.SLACK,
                NotificationChannel.EMAIL,
            ],
            AlertSeverity.HIGH: [NotificationChannel.SLACK, NotificationChannel.EMAIL],
            AlertSeverity.WARNING: [NotificationChannel.SLACK],
            AlertSeverity.INFO: [NotificationChannel.SLACK],
        }

        logger.info("Smart Alert Router initialized")

    def extract_context(self, alert: dict[str, Any]) -> AlertContext:
        """
        Extract context information from alert.

        Args:
            alert: Alert data from Alertmanager

        Returns:
            AlertContext object
        """
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})

        # Determine severity
        severity_str = labels.get("severity", "info").lower()
        severity = (
            AlertSeverity(severity_str)
            if severity_str in [s.value for _s in AlertSeverity]
            else AlertSeverity.INFO
        )

        # Extract values
        current_value = annotations.get("current_value") or labels.get("current_value")
        baseline_value = annotations.get("baseline_value") or labels.get(
            "baseline_value"
        )
        threshold = annotations.get("threshold") or labels.get("threshold")

        # Extract URLs
        runbook_url = annotations.get("runbook_url") or labels.get("runbook_url")
        grafana_url = annotations.get("grafana_url") or labels.get("dashboard_url")
        dashboard_url = annotations.get("dashboard_url") or grafana_url

        # Parse timestamp
        timestamp = None
        if alert.get("startsAt"):
            try:
                timestamp = datetime.fromisoformat(
                    alert["startsAt"].replace("Z", "+00:00")
                )
            except Exception:
        timestamp = datetime.now()

        return AlertContext(
            service=labels.get("service", "unknown"),
            environment=labels.get("environment", "development"),
            team=labels.get("team", "backend"),
            category=labels.get("category", "general"),
            severity=severity,
            current_value=current_value,
            baseline_value=baseline_value,
            threshold=threshold,
            runbook_url=runbook_url,
            grafana_url=grafana_url,
            dashboard_url=dashboard_url,
            timestamp=timestamp,
        )

    def should_suppress_alert(
        self, context: AlertContext, alert: dict[str, Any]
    ) -> bool:
        """
        Check if alert should be suppressed based on various rules.

        Args:
            context: Alert context
            alert: Alert data

        Returns:
            True if alert should be suppressed
        """
        # Suppress info alerts during maintenance windows (example)
        if context.severity == AlertSeverity.INFO:
            # Check if it's a maintenance window (simplified logic)
            current_hour = datetime.now().hour
            if 2 <= current_hour <= 6:  # 2 AM to 6 AM maintenance window
                return True

        # Suppress non-critical alerts on weekends (example)
if context.severity in [AlertSeverity.WARNING, AlertSeverity.INFO] and if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6:

        # Check for duplicate alerts (simple deduplication)
        # In production, you'd implement proper deduplication logic here

        return False

    def route_alert(self, alert: dict[str, Any]) -> dict[str, bool]:
        """
        Route alert to appropriate notification channels.

        Args:
            alert: Alert data from Alertmanager

        Returns:
            Dictionary mapping channel names to success status
        """
        context = self.extract_context(alert)

# Check if alert should be suppressed and if self.should_suppress_alert(context, alert):
            return {"suppressed": True}

        # Get routing channels for this severity
        channels = self.routing_rules.get(context.severity, [NotificationChannel.SLACK])

        results = {}
        for _channel in channels:
            notifier = self.notifiers.get(channel)
            if notifier:
                try:
                    success = notifier.send_alert(alert, context)
                    results[channel.value] = success
                    logger.info(f"Alert routed to {channel.value}: {success}")
                except Exception as e:
                    logger.error(f"Error routing alert to {channel.value}: {e}")
                    results[channel.value] = False
            else:
                logger.warning(f"No notifier configured for channel: {channel.value}")
                results[channel.value] = False

        return results

    def get_routing_stats(self) -> dict[str, Any]:
        """
        Get routing statistics.

        Returns:
            Dictionary with routing statistics
        """
        return {
            "configured_channels": list(self.notifiers.keys()),
            "routing_rules": {
                severity.value: [ch.value for _ch in channels]
                for _severity, channels in self.routing_rules.items()
            },
            "config": self.config,
        }


# Default configuration (can be overridden by environment variables)
DEFAULT_CONFIG = {
    "slack": {
        "enabled": os.getenv("SLACK_ENABLED", "false").lower() == "true",
        "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "channel": os.getenv("SLACK_CHANNEL", "#alerts"),
    },
    "pagerduty": {
        "enabled": os.getenv("PAGERDUTY_ENABLED", "false").lower() == "true",
        "integration_key": os.getenv("PAGERDUTY_INTEGRATION_KEY", ""),
    },
    "email": {
        "enabled": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "smtp_host": os.getenv("EMAIL_SMTP_HOST", ""),
        "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
        "smtp_user": os.getenv("EMAIL_SMTP_USER", ""),
        "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD", ""),
        "from_email": os.getenv("EMAIL_FROM", ""),
        "to_emails": (
            os.getenv("EMAIL_TO", "").split(",") if os.getenv("EMAIL_TO") else []
        ),
    },
}

# Global router instance
alert_router = SmartAlertRouter(DEFAULT_CONFIG)


def route_alert(alert_data: dict[str, Any]) -> dict[str, bool]:
    """
    Route a single alert to appropriate channels.

    Args:
        alert_data: Alert data from Alertmanager

    Returns:
        Dictionary mapping channel names to success status
    """
    return alert_router.route_alert(alert_data)


def get_routing_config() -> dict[str, Any]:
    """Get current routing configuration"""
    return alert_router.get_routing_stats()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Example alert
    example_alert = {
        "labels": {
            "alertname": "HighErrorRate",
            "service": "magsasa-card-erp",
            "severity": "critical",
            "team": "backend",
            "category": "errors",
        },
        "annotations": {
            "summary": "High error rate detected",
            "description": "5xx error rate is 15% (threshold: 5%)",
            "current_value": "15%",
            "baseline_value": "2%",
            "threshold": "5%",
            "runbook_url": "https://docs.example.com/runbooks/high-error-rate",
            "grafana_url": "http://grafana:3000/d/error-rates",
        },
        "status": "firing",
        "startsAt": datetime.now().isoformat() + "Z",
    }

    # Route the alert
    results = route_alert(example_alert)
    print(f"Routing results: {results}")
