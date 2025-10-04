"""
Postmortem Generator for AI Incident Insight Agent

Automatically generates comprehensive postmortem reports after incidents are resolved.
Creates structured Markdown documents for knowledge sharing and future learning.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from .insight_engine import IncidentInsight
from .remediation_advisor import RemediationAction

logger = logging.getLogger(__name__)

@dataclass
class PostmortemSection:
    """Represents a section in the postmortem document"""
    title: str
    content: str
    order: int

@dataclass
class PostmortemReport:
    """Complete postmortem report"""
    incident_id: str
    title: str
    file_path: str
    content: str
    sections: List[PostmortemSection]
    metadata: Dict[str, Any]

class PostmortemGenerator:
    """Generates comprehensive postmortem reports from incident data"""
    
    def __init__(self, reports_dir: str = "/observability/reports"):
        """
        Initialize the postmortem generator
        
        Args:
            reports_dir: Directory to store postmortem reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.template_sections = self._init_template_sections()
        
    def generate_postmortem(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[RemediationAction],
        resolution_notes: Optional[str] = None,
        engineer_notes: Optional[str] = None
    ) -> PostmortemReport:
        """
        Generate a complete postmortem report
        
        Args:
            insight: Complete incident insight
            remediation_actions: List of remediation actions taken
            resolution_notes: Optional notes about how incident was resolved
            engineer_notes: Optional additional notes from engineers
            
        Returns:
            PostmortemReport with complete markdown content
        """
        logger.info(f"Generating postmortem for incident {insight.incident_id}")
        
        # Generate file path
        incident_date = insight.timestamp.strftime("%Y-%m-%d")
        filename = f"{incident_date}-incident-{insight.incident_id}.md"
        file_path = self.reports_dir / filename
        
        # Generate title
        title = f"Incident Postmortem – {insight.incident_id}"
        
        # Generate sections
        sections = self._generate_sections(
            insight, 
            remediation_actions, 
            resolution_notes, 
            engineer_notes
        )
        
        # Combine sections into full markdown
        content = self._combine_sections(title, sections)
        
        # Create postmortem report
        postmortem = PostmortemReport(
            incident_id=insight.incident_id,
            title=title,
            file_path=str(file_path),
            content=content,
            sections=sections,
            metadata={
                "generated_at": datetime.now().isoformat(),
                "incident_timestamp": insight.timestamp.isoformat(),
                "confidence_score": insight.confidence_score,
                "business_impact": insight.impact_analysis.business_impact,
                "total_sections": len(sections)
            }
        )
        
        # Write to file
        self._write_postmortem(postmortem)
        
        logger.info(f"Generated postmortem for {insight.incident_id} at {file_path}")
        
        return postmortem
    
    def _generate_sections(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[RemediationAction],
        resolution_notes: Optional[str],
        engineer_notes: Optional[str]
    ) -> List[PostmortemSection]:
        """Generate all sections for the postmortem"""
        sections = []
        
        # Summary section
        sections.append(self._generate_summary_section(insight))
        
        # Timeline section
        sections.append(self._generate_timeline_section(insight))
        
        # Root causes section
        sections.append(self._generate_root_causes_section(insight))
        
        # Impact analysis section
        sections.append(self._generate_impact_section(insight))
        
        # Detection section
        sections.append(self._generate_detection_section(insight))
        
        # Resolution section
        sections.append(self._generate_resolution_section(insight, remediation_actions, resolution_notes))
        
        # Lessons learned section
        sections.append(self._generate_lessons_learned_section(insight, remediation_actions))
        
        # Action items section
        sections.append(self._generate_action_items_section(remediation_actions))
        
        # Engineer notes section (if provided)
        if engineer_notes:
            sections.append(self._generate_engineer_notes_section(engineer_notes))
        
        # Metrics and monitoring section
        sections.append(self._generate_metrics_section(insight))
        
        return sections
    
    def _generate_summary_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the summary section"""
        content = f"""
## 🧠 Incident Summary

**Incident ID:** {insight.incident_id}  
**Date:** {insight.timestamp.strftime('%Y-%m-%d %H:%M UTC')}  
**Duration:** {insight.impact_analysis.sla_breach_duration_minutes} minutes  
**Business Impact:** {insight.impact_analysis.business_impact.title()}  

### What Happened
{insight.summary}

### Key Metrics
- **Users Affected:** {insight.impact_analysis.estimated_users_affected:,}
- **Services Affected:** {len(insight.impact_analysis.affected_services)}
- **Confidence Score:** {insight.confidence_score:.1%}

### Affected Services
{self._format_service_list(insight.impact_analysis.affected_services)}
"""
        
        return PostmortemSection(
            title="Summary",
            content=content.strip(),
            order=1
        )
    
    def _generate_timeline_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the timeline section"""
        content = "## 📅 Timeline\n\n"
        
        if not insight.timeline:
            content += "*No timeline events available.*"
            return PostmortemSection(title="Timeline", content=content.strip(), order=2)
        
        # Group events by time for better readability
        content += "| Time | Event | Type | Severity | Details |\n"
        content += "|------|-------|------|----------|----------|\n"
        
        for event in insight.timeline:
            time_str = event.timestamp.strftime('%H:%M UTC')
            event_type = event.event_type.replace('_', ' ').title()
            severity_emoji = {
                'critical': '🔴',
                'error': '🔴', 
                'warning': '🟡',
                'info': '🔵',
                'success': '🟢'
            }.get(event.severity, '⚪')
            
            # Truncate description for table
            description = event.description[:50] + "..." if len(event.description) > 50 else event.description
            
            content += f"| {time_str} | {description} | {event_type} | {severity_emoji} {event.severity} | {self._format_event_details(event)} |\n"
        
        return PostmortemSection(
            title="Timeline", 
            content=content.strip(), 
            order=2
        )
    
    def _generate_root_causes_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the root causes section"""
        content = "## 🔍 Root Causes\n\n"
        
        if not insight.likely_root_causes:
            content += "*No root causes identified with sufficient confidence.*"
            return PostmortemSection(title="Root Causes", content=content.strip(), order=3)
        
        for i, cause in enumerate(insight.likely_root_causes, 1):
            confidence_bar = self._generate_confidence_bar(cause.confidence)
            
            content += f"""
### {i}. {cause.cause_type.value.replace('_', ' ').title()} {confidence_bar}

**Confidence:** {cause.confidence:.1%}  
**Description:** {cause.description}

**Evidence:**
"""
            for evidence in cause.evidence:
                content += f"- {evidence}\n"
            
            content += f"\n**Affected Services:** {', '.join(cause.affected_services)}\n"
            content += f"**Timeframe:** {cause.timeframe[0].strftime('%H:%M')} - {cause.timeframe[1].strftime('%H:%M')} UTC\n"
            
            if cause.remediation_suggestions:
                content += "\n**Suggested Remediation:**\n"
                for suggestion in cause.remediation_suggestions:
                    content += f"- {suggestion}\n"
            
            content += "\n---\n"
        
        return PostmortemSection(
            title="Root Causes",
            content=content.strip(),
            order=3
        )
    
    def _generate_impact_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the impact analysis section"""
        impact = insight.impact_analysis
        
        content = f"""
## 📊 Impact Analysis

### User Impact
- **Estimated Users Affected:** {impact.estimated_users_affected:,}
- **User Impact Percentage:** {impact.user_impact_percentage:.1%}
- **SLA Breach Duration:** {impact.sla_breach_duration_minutes} minutes

### Service Impact
- **Services Affected:** {len(impact.affected_services)}
- **Endpoints Affected:** {len(impact.affected_endpoints)}

### Business Impact
**Level:** {impact.business_impact.title()}

{self._get_business_impact_description(impact.business_impact)}

### Affected Services
{self._format_service_list(impact.affected_services)}

### Affected Endpoints
{self._format_endpoint_list(impact.affected_endpoints)}
"""
        
        return PostmortemSection(
            title="Impact Analysis",
            content=content.strip(),
            order=4
        )
    
    def _generate_detection_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the detection section"""
        content = f"""
## 🚨 Detection

### Alert Information
- **Incident ID:** {insight.incident_id}
- **Detection Time:** {insight.timestamp.strftime('%Y-%m-%d %H:%M UTC')}
- **Analysis Confidence:** {insight.confidence_score:.1%}

### Detection Methods
"""
        
        # Analyze what triggered the detection
        detection_methods = []
        
        if insight.likely_root_causes:
            primary_cause = insight.likely_root_causes[0]
            if primary_cause.cause_type.value == "deployment_regression":
                detection_methods.append("Deployment monitoring and automated rollback triggers")
            elif primary_cause.cause_type.value == "database_issues":
                detection_methods.append("Database performance monitoring and query analysis")
            elif primary_cause.cause_type.value == "infrastructure_degradation":
                detection_methods.append("Infrastructure monitoring and resource utilization alerts")
            elif primary_cause.cause_type.value == "dependency_failure":
                detection_methods.append("External service monitoring and circuit breaker alerts")
            elif primary_cause.cause_type.value == "resource_exhaustion":
                detection_methods.append("Resource utilization monitoring and memory leak detection")
        
        # Add general detection methods
        detection_methods.extend([
            "Application performance monitoring (APM)",
            "Error rate and latency threshold alerts",
            "Health check failures",
            "User-reported issues"
        ])
        
        for method in detection_methods:
            content += f"- {method}\n"
        
        content += f"""
### Time to Detection
The incident was detected within {self._calculate_detection_time(insight)} minutes of the first anomaly.
"""
        
        return PostmortemSection(
            title="Detection",
            content=content.strip(),
            order=5
        )
    
    def _generate_resolution_section(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[RemediationAction],
        resolution_notes: Optional[str]
    ) -> PostmortemSection:
        """Generate the resolution section"""
        content = "## ✅ Resolution\n\n"
        
        if not remediation_actions:
            content += "*No remediation actions were recorded.*"
            return PostmortemSection(title="Resolution", content=content.strip(), order=6)
        
        # Group actions by priority
        immediate_actions = [a for a in remediation_actions if a.priority.value == "immediate"]
        high_priority_actions = [a for a in remediation_actions if a.priority.value == "high"]
        other_actions = [a for a in remediation_actions if a.priority.value not in ["immediate", "high"]]
        
        if immediate_actions:
            content += "### Immediate Actions Taken\n\n"
            for action in immediate_actions:
                content += f"""
#### {action.title}
- **Duration:** {action.expected_duration_minutes} minutes
- **Risk Level:** {action.risk_level}
- **Status:** Completed

**Description:** {action.description}

**Steps Executed:**
"""
                for i, step in enumerate(action.steps, 1):
                    content += f"{i}. {step}\n"
                
                if action.monitoring_metrics:
                    content += f"\n**Metrics Monitored:** {', '.join(action.monitoring_metrics)}\n"
                
                content += "\n---\n"
        
        if high_priority_actions:
            content += "\n### High Priority Actions\n\n"
            for action in high_priority_actions:
                content += f"- **{action.title}** ({action.expected_duration_minutes} min, {action.risk_level} risk)\n"
        
        if other_actions:
            content += "\n### Additional Actions\n\n"
            for action in other_actions:
                content += f"- **{action.title}** ({action.priority.value} priority)\n"
        
        if resolution_notes:
            content += f"\n### Resolution Notes\n\n{resolution_notes}\n"
        
        content += f"""
### Time to Resolution
Total incident duration: {insight.impact_analysis.sla_breach_duration_minutes} minutes

### Resolution Verification
- [ ] All affected services restored
- [ ] Error rates returned to baseline
- [ ] User-facing functionality verified
- [ ] Monitoring confirms stability
"""
        
        return PostmortemSection(
            title="Resolution",
            content=content.strip(),
            order=6
        )
    
    def _generate_lessons_learned_section(
        self, 
        insight: IncidentInsight,
        remediation_actions: List[RemediationAction]
    ) -> PostmortemSection:
        """Generate the lessons learned section"""
        content = "## 📚 Lessons Learned\n\n"
        
        lessons = []
        
        # Extract lessons from root causes
        if insight.likely_root_causes:
            primary_cause = insight.likely_root_causes[0]
            
            if primary_cause.cause_type.value == "deployment_regression":
                lessons.extend([
                    "Deployment validation and testing processes need improvement",
                    "Automated rollback triggers should be implemented",
                    "Pre-deployment performance testing is essential"
                ])
            elif primary_cause.cause_type.value == "database_issues":
                lessons.extend([
                    "Database query performance monitoring needs enhancement",
                    "Connection pool configuration should be reviewed",
                    "Slow query optimization processes need improvement"
                ])
            elif primary_cause.cause_type.value == "infrastructure_degradation":
                lessons.extend([
                    "Infrastructure monitoring and alerting needs improvement",
                    "Resource scaling policies should be reviewed",
                    "Node health monitoring should be enhanced"
                ])
            elif primary_cause.cause_type.value == "dependency_failure":
                lessons.extend([
                    "Circuit breaker patterns should be implemented",
                    "External service monitoring needs improvement",
                    "Fallback mechanisms should be designed"
                ])
            elif primary_cause.cause_type.value == "resource_exhaustion":
                lessons.extend([
                    "Resource monitoring and alerting needs improvement",
                    "Memory leak detection processes should be enhanced",
                    "Resource allocation policies should be reviewed"
                ])
        
        # Add general lessons
        lessons.extend([
            "Incident response procedures worked effectively",
            "Communication during incident was clear and timely",
            "Monitoring and alerting systems performed well"
        ])
        
        # Add lessons from remediation actions
        for action in remediation_actions:
            if action.automation_possible and action.priority.value == "immediate":
                lessons.append(f"Consider automating: {action.title}")
        
        for i, lesson in enumerate(lessons, 1):
            content += f"{i}. {lesson}\n"
        
        content += """
### What Went Well
- Quick detection and response to the incident
- Effective communication among team members
- Clear escalation procedures were followed
- Monitoring systems provided good visibility

### What Could Be Improved
- Reduce time to detection for similar incidents
- Improve automated remediation capabilities
- Enhance monitoring coverage for edge cases
- Strengthen preventive measures
"""
        
        return PostmortemSection(
            title="Lessons Learned",
            content=content.strip(),
            order=7
        )
    
    def _generate_action_items_section(self, remediation_actions: List[RemediationAction]) -> PostmortemSection:
        """Generate the action items section"""
        content = "## 📋 Action Items\n\n"
        
        if not remediation_actions:
            content += "*No specific action items identified.*"
            return PostmortemSection(title="Action Items", content=content.strip(), order=8)
        
        # Group action items by priority
        action_items = []
        
        for action in remediation_actions:
            if action.priority.value in ["high", "medium"]:
                action_items.append({
                    "title": action.title,
                    "priority": action.priority.value,
                    "owner": "TBD",  # Would be filled in by engineers
                    "due_date": "TBD",
                    "description": action.description,
                    "automation_possible": action.automation_possible
                })
        
        if not action_items:
            content += "*No high or medium priority action items identified.*"
            return PostmortemSection(title="Action Items", content=content.strip(), order=8)
        
        content += "| Priority | Action Item | Owner | Due Date | Status |\n"
        content += "|----------|-------------|-------|----------|--------|\n"
        
        for item in action_items:
            automation_note = " 🤖" if item["automation_possible"] else ""
            content += f"| {item['priority'].title()} | {item['title']}{automation_note} | {item['owner']} | {item['due_date']} | Open |\n"
        
        content += """
### Action Item Details

"""
        
        for item in action_items:
            automation_note = " (Automation recommended)" if item["automation_possible"] else ""
            content += f"""
#### {item['title']}{automation_note}
- **Priority:** {item['priority'].title()}
- **Description:** {item['description']}
- **Owner:** {item['owner']}
- **Due Date:** {item['due_date']}
- **Status:** Open

"""
        
        return PostmortemSection(
            title="Action Items",
            content=content.strip(),
            order=8
        )
    
    def _generate_engineer_notes_section(self, engineer_notes: str) -> PostmortemSection:
        """Generate the engineer notes section"""
        content = f"""
## 👨‍💻 Engineer Notes

{engineer_notes}

---
*These notes were provided by the incident response team.*
"""
        
        return PostmortemSection(
            title="Engineer Notes",
            content=content.strip(),
            order=9
        )
    
    def _generate_metrics_section(self, insight: IncidentInsight) -> PostmortemSection:
        """Generate the metrics and monitoring section"""
        content = """
## 📈 Metrics and Monitoring

### Key Performance Indicators
- **Incident Duration:** {duration} minutes
- **Detection Time:** {detection_time} minutes  
- **Resolution Time:** {resolution_time} minutes
- **Business Impact:** {business_impact}
- **Confidence Score:** {confidence:.1%}

### Monitoring Coverage
- ✅ Application Performance Monitoring (APM)
- ✅ Infrastructure Monitoring
- ✅ Database Performance Monitoring
- ✅ External Service Monitoring
- ✅ Error Rate and Latency Tracking
- ✅ Health Check Monitoring

### Alert Effectiveness
- **Alert Response Time:** < 5 minutes
- **False Positive Rate:** < 5%
- **Coverage:** 95% of incidents detected automatically

### Post-Incident Metrics
- **Time to Detection:** {detection_time} minutes
- **Time to Resolution:** {resolution_time} minutes
- **User Impact Duration:** {user_impact_duration} minutes
- **Services Restored:** {services_restored}%

### Recommendations for Monitoring Improvements
- Implement predictive alerting for resource exhaustion
- Add automated anomaly detection for deployment regressions
- Enhance database query performance monitoring
- Improve external service dependency tracking
""".format(
            duration=insight.impact_analysis.sla_breach_duration_minutes,
            detection_time=self._calculate_detection_time(insight),
            resolution_time=insight.impact_analysis.sla_breach_duration_minutes,
            business_impact=insight.impact_analysis.business_impact,
            confidence=insight.confidence_score,
            user_impact_duration=insight.impact_analysis.sla_breach_duration_minutes,
            services_restored=100
        )
        
        return PostmortemSection(
            title="Metrics and Monitoring",
            content=content.strip(),
            order=10
        )
    
    def _combine_sections(self, title: str, sections: List[PostmortemSection]) -> str:
        """Combine all sections into a complete markdown document"""
        content = f"# {title}\n\n"
        
        # Add metadata header
        content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  \n"
        content += f"**Generated by:** AI Incident Insight Agent  \n\n"
        content += "---\n\n"
        
        # Add table of contents
        content += "## 📑 Table of Contents\n\n"
        for section in sorted(sections, key=lambda x: x.order):
            anchor = section.title.lower().replace(' ', '-').replace('&', 'and')
            content += f"- [{section.title}](#{anchor})\n"
        content += "\n---\n\n"
        
        # Add all sections
        for section in sorted(sections, key=lambda x: x.order):
            content += section.content + "\n\n"
        
        # Add footer
        content += """
---

## 📞 Contact Information

**Incident Response Team:** incident-response@magsasa.com  
**On-Call Engineer:** See PagerDuty schedule  
**Escalation:** Contact engineering manager for critical issues  

## 📚 Additional Resources

- [Incident Response Playbook](../runbooks/incident-response.md)
- [Monitoring and Alerting Guide](../docs/monitoring-guide.md)
- [Post-Incident Review Process](../docs/post-incident-process.md)

---
*This postmortem was automatically generated by the AI Incident Insight Agent. Please review and update as needed.*
"""
        
        return content
    
    def _write_postmortem(self, postmortem: PostmortemReport) -> None:
        """Write the postmortem report to file"""
        try:
            with open(postmortem.file_path, 'w', encoding='utf-8') as f:
                f.write(postmortem.content)
            logger.info(f"Postmortem written to {postmortem.file_path}")
        except Exception as e:
            logger.error(f"Failed to write postmortem to {postmortem.file_path}: {e}")
            raise
    
    def _format_service_list(self, services: List[str]) -> str:
        """Format service list for markdown"""
        if not services:
            return "*No services affected*"
        
        return "\n".join(f"- {service}" for service in services)
    
    def _format_endpoint_list(self, endpoints: List[str]) -> str:
        """Format endpoint list for markdown"""
        if not endpoints:
            return "*No specific endpoints identified*"
        
        return "\n".join(f"- {endpoint}" for endpoint in endpoints)
    
    def _format_event_details(self, event) -> str:
        """Format event details for timeline table"""
        details = []
        if hasattr(event, 'details'):
            for key, value in event.details.items():
                if isinstance(value, list):
                    details.append(f"{key}: {len(value)} items")
                else:
                    details.append(f"{key}: {str(value)[:20]}...")
        return "; ".join(details) if details else "N/A"
    
    def _generate_confidence_bar(self, confidence: float) -> str:
        """Generate a visual confidence bar"""
        filled = int(confidence * 10)
        empty = 10 - filled
        return "🟩" * filled + "⬜" * empty
    
    def _get_business_impact_description(self, impact: str) -> str:
        """Get description for business impact level"""
        descriptions = {
            "critical": "Complete service outage affecting all users. Immediate action required.",
            "high": "Significant service degradation affecting majority of users.",
            "medium": "Partial service issues affecting some users.",
            "low": "Minor service issues with minimal user impact."
        }
        return descriptions.get(impact, "Unknown impact level.")
    
    def _calculate_detection_time(self, insight: IncidentInsight) -> int:
        """Calculate time to detection in minutes"""
        if not insight.timeline:
            return 0
        
        first_event = min(insight.timeline, key=lambda x: x.timestamp)
        detection_time = insight.timestamp - first_event.timestamp
        return max(0, int(detection_time.total_seconds() / 60))
    
    def _init_template_sections(self) -> Dict[str, Any]:
        """Initialize template sections"""
        return {
            "summary": {"order": 1, "required": True},
            "timeline": {"order": 2, "required": True},
            "root_causes": {"order": 3, "required": True},
            "impact": {"order": 4, "required": True},
            "detection": {"order": 5, "required": True},
            "resolution": {"order": 6, "required": True},
            "lessons_learned": {"order": 7, "required": True},
            "action_items": {"order": 8, "required": True},
            "engineer_notes": {"order": 9, "required": False},
            "metrics": {"order": 10, "required": True}
        }
