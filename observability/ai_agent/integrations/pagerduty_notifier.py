"""
PagerDuty Integration for AI Incident Insight Agent

Sends structured incident insights to PagerDuty for on-call systems.
Provides escalation and notification capabilities.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
from ..incident_reporter import IncidentReport
from ..insight_engine import IncidentInsight

logger = logging.getLogger(__name__)

@dataclass
class PagerDutyEvent:
    """Represents a PagerDuty event"""
    routing_key: str
    event_action: str  # "trigger", "acknowledge", "resolve"
    dedup_key: str
    payload: Dict[str, Any]

@dataclass
class PagerDutyIncident:
    """Represents a PagerDuty incident"""
    incident_id: str
    incident_key: str
    title: str
    severity: str
    status: str
    description: str
    details: Dict[str, Any]

class PagerDutyNotifier:
    """PagerDuty integration for incident notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the PagerDuty notifier with configuration
        
        Expected config structure:
        {
            "integration_keys": {
                "incidents": "integration_key_for_incidents",
                "alerts": "integration_key_for_alerts"
            },
            "api_token": "pagerduty_api_token",
            "default_routing": {
                "critical": "incidents",
                "high": "incidents", 
                "medium": "alerts",
                "low": "alerts"
            },
            "custom_fields": {
                "business_impact": "business_impact",
                "confidence_score": "confidence_score",
                "root_causes": "root_causes"
            }
        }
        """
        self.config = config
        self.integration_keys = config.get("integration_keys", {})
        self.api_token = config.get("api_token")
        self.default_routing = config.get("default_routing", {})
        self.custom_fields = config.get("custom_fields", {})
        self.base_url = "https://events.pagerduty.com/v2"
        
    async def send_incident_alert(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[Any] = None
    ) -> bool:
        """
        Send incident alert to PagerDuty
        
        Args:
            insight: Incident insight to send
            remediation_actions: Optional remediation actions
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine routing based on business impact
            routing_key = self._get_routing_key(insight.impact_analysis.business_impact)
            
            if not routing_key:
                logger.warning(f"No routing key found for business impact: {insight.impact_analysis.business_impact}")
                return False
            
            # Create PagerDuty event
            event = self._create_incident_event(insight, remediation_actions, routing_key)
            
            # Send to PagerDuty
            success = await self._send_event(event)
            
            if success:
                logger.info(f"Sent incident alert {insight.incident_id} to PagerDuty")
            else:
                logger.error(f"Failed to send incident alert {insight.incident_id} to PagerDuty")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending incident alert to PagerDuty: {e}")
            return False
    
    async def acknowledge_incident(self, incident_id: str, incident_key: str) -> bool:
        """
        Acknowledge a PagerDuty incident
        
        Args:
            incident_id: Internal incident ID
            incident_key: PagerDuty incident key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = PagerDutyEvent(
                routing_key="",  # Will be determined by incident_key
                event_action="acknowledge",
                dedup_key=incident_key,
                payload={}
            )
            
            success = await self._send_event(event)
            
            if success:
                logger.info(f"Acknowledged PagerDuty incident {incident_key}")
            else:
                logger.error(f"Failed to acknowledge PagerDuty incident {incident_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error acknowledging PagerDuty incident: {e}")
            return False
    
    async def resolve_incident(self, incident_id: str, incident_key: str) -> bool:
        """
        Resolve a PagerDuty incident
        
        Args:
            incident_id: Internal incident ID
            incident_key: PagerDuty incident key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            event = PagerDutyEvent(
                routing_key="",  # Will be determined by incident_key
                event_action="resolve",
                dedup_key=incident_key,
                payload={
                    "summary": f"Incident {incident_id} has been resolved",
                    "source": "AI Incident Agent",
                    "severity": "info"
                }
            )
            
            success = await self._send_event(event)
            
            if success:
                logger.info(f"Resolved PagerDuty incident {incident_key}")
            else:
                logger.error(f"Failed to resolve PagerDuty incident {incident_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error resolving PagerDuty incident: {e}")
            return False
    
    async def get_incident_details(self, incident_key: str) -> Optional[PagerDutyIncident]:
        """
        Get details of a PagerDuty incident using REST API
        
        Args:
            incident_key: PagerDuty incident key
            
        Returns:
            PagerDutyIncident details or None if not found
        """
        try:
            if not self.api_token:
                logger.warning("PagerDuty API token not configured")
                return None
            
            url = f"https://api.pagerduty.com/incidents/{incident_key}"
            headers = {
                "Authorization": f"Token token={self.api_token}",
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        incident_data = data.get("incident", {})
                        
                        incident = PagerDutyIncident(
                            incident_id=incident_data.get("id", ""),
                            incident_key=incident_key,
                            title=incident_data.get("title", ""),
                            severity=incident_data.get("severity", "unknown"),
                            status=incident_data.get("status", "unknown"),
                            description=incident_data.get("description", ""),
                            details=incident_data
                        )
                        
                        logger.info(f"Retrieved PagerDuty incident details for {incident_key}")
                        return incident
                    else:
                        logger.error(f"Failed to get PagerDuty incident {incident_key}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting PagerDuty incident details: {e}")
            return None
    
    def _get_routing_key(self, business_impact: str) -> Optional[str]:
        """Get routing key based on business impact"""
        routing_type = self.default_routing.get(business_impact.lower())
        if routing_type:
            return self.integration_keys.get(routing_type)
        return None
    
    def _create_incident_event(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[Any],
        routing_key: str
    ) -> PagerDutyEvent:
        """Create a PagerDuty event for incident alert"""
        
        # Determine severity based on business impact
        severity_map = {
            "critical": "critical",
            "high": "error", 
            "medium": "warning",
            "low": "info"
        }
        severity = severity_map.get(insight.impact_analysis.business_impact.lower(), "warning")
        
        # Create summary
        summary = f"Incident {insight.incident_id}: {insight.summary[:100]}"
        
        # Create detailed payload
        payload = {
            "summary": summary,
            "source": "AI Incident Agent",
            "severity": severity,
            "timestamp": insight.timestamp.isoformat(),
            "component": "MAGSASA-CARD-ERP",
            "group": "incident-response",
            "class": "incident",
            "custom_details": {
                "incident_id": insight.incident_id,
                "business_impact": insight.impact_analysis.business_impact,
                "confidence_score": insight.confidence_score,
                "users_affected": insight.impact_analysis.estimated_users_affected,
                "duration_minutes": insight.impact_analysis.sla_breach_duration_minutes,
                "affected_services": insight.impact_analysis.affected_services,
                "root_causes": [
                    {
                        "type": cause.cause_type.value,
                        "confidence": cause.confidence,
                        "description": cause.description
                    }
                    for cause in insight.likely_root_causes[:3]  # Top 3 causes
                ]
            }
        }
        
        # Add remediation actions if available
        if remediation_actions:
            immediate_actions = [action for action in remediation_actions if hasattr(action, 'priority') and action.priority.value == "immediate"]
            if immediate_actions:
                payload["custom_details"]["immediate_actions"] = [
                    {
                        "title": action.title,
                        "duration_minutes": getattr(action, 'expected_duration_minutes', 0),
                        "risk_level": getattr(action, 'risk_level', 'unknown')
                    }
                    for action in immediate_actions[:3]  # Top 3 immediate actions
                ]
        
        # Add timeline events
        if insight.timeline:
            payload["custom_details"]["timeline"] = [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "description": event.description,
                    "severity": event.severity
                }
                for event in insight.timeline[:5]  # First 5 events
            ]
        
        # Create deduplication key
        dedup_key = f"incident-{insight.incident_id}"
        
        return PagerDutyEvent(
            routing_key=routing_key,
            event_action="trigger",
            dedup_key=dedup_key,
            payload=payload
        )
    
    async def _send_event(self, event: PagerDutyEvent) -> bool:
        """Send event to PagerDuty Events API v2"""
        try:
            url = f"{self.base_url}/enqueue"
            
            payload = {
                "routing_key": event.routing_key,
                "event_action": event.event_action,
                "dedup_key": event.dedup_key,
                "payload": event.payload
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status in [200, 202]:
                        result = await response.json()
                        if result.get("status") == "success":
                            return True
                        else:
                            logger.error(f"PagerDuty API returned error: {result}")
                            return False
                    else:
                        logger.error(f"PagerDuty API returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending event to PagerDuty: {e}")
            return False
    
    def _format_incident_summary(self, insight: IncidentInsight) -> str:
        """Format incident summary for PagerDuty"""
        return f"""
Incident {insight.incident_id} - {insight.impact_analysis.business_impact.title()} Impact

Summary: {insight.summary}

Impact:
- Users Affected: {insight.impact_analysis.estimated_users_affected:,}
- Duration: {insight.impact_analysis.sla_breach_duration_minutes} minutes
- Services: {', '.join(insight.impact_analysis.affected_services[:3])}

Root Causes:
{chr(10).join(f"- {cause.cause_type.value.replace('_', ' ').title()} ({cause.confidence:.1%})" for cause in insight.likely_root_causes[:3])}

Generated by AI Incident Agent
"""
    
    def _get_severity_from_impact(self, business_impact: str) -> str:
        """Map business impact to PagerDuty severity"""
        severity_mapping = {
            "critical": "critical",
            "high": "error",
            "medium": "warning", 
            "low": "info"
        }
        return severity_mapping.get(business_impact.lower(), "warning")
    
    async def send_custom_alert(
        self, 
        title: str, 
        description: str, 
        severity: str,
        routing_key: str,
        custom_details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a custom alert to PagerDuty
        
        Args:
            title: Alert title
            description: Alert description
            severity: Alert severity (critical, error, warning, info)
            routing_key: PagerDuty routing key
            custom_details: Optional custom details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "summary": title,
                "source": "AI Incident Agent",
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "component": "MAGSASA-CARD-ERP",
                "group": "custom-alerts",
                "class": "custom"
            }
            
            if custom_details:
                payload["custom_details"] = custom_details
            
            event = PagerDutyEvent(
                routing_key=routing_key,
                event_action="trigger",
                dedup_key=f"custom-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                payload=payload
            )
            
            success = await self._send_event(event)
            
            if success:
                logger.info(f"Sent custom alert '{title}' to PagerDuty")
            else:
                logger.error(f"Failed to send custom alert '{title}' to PagerDuty")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending custom alert to PagerDuty: {e}")
            return False
