"""
AI Incident Insight Agent

An intelligent layer that sits on top of the runtime intelligence system
and transforms raw alerts into actionable understanding.

Components:
- data_collector: Aggregates telemetry from metrics, logs, traces, alerts
- incident_analyzer: Correlates anomalies and infers root causes
- insight_engine: Generates narrative explanations and summaries
- remediation_advisor: Suggests specific remediation actions
- incident_reporter: Formats and delivers incident summaries
- postmortem_generator: Auto-writes incident postmortem reports
- integrations: Slack and PagerDuty integrations
"""

__version__ = "1.0.0"
__author__ = "AI Studio Dev Pipeline"

from .data_collector import IncidentContextCollector
from .incident_analyzer import IncidentAnalyzer
from .incident_reporter import IncidentReporter
from .insight_engine import InsightEngine
from .postmortem_generator import PostmortemGenerator
from .remediation_advisor import RemediationAdvisor

__all__ = [
    "IncidentContextCollector",
    "IncidentAnalyzer",
    "InsightEngine",
    "RemediationAdvisor",
    "IncidentReporter",
    "PostmortemGenerator",
]
