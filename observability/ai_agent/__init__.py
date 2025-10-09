"""
AI Incident Insight Agent

An intelligent layer that sits on top of the runtime intelligence system
and transforms raw alerts into actionable understanding.

🌐 Public namespace imports for observability.ai_agent
This file ensures that dynamic imports, patching, and test mocks resolve correctly.
Exposed modules are automatically imported to make them available at package level.

📋 Auto-discovered modules in observability/ai_agent/:
✅ webhook_server.py - FastAPI app for webhook handling (EXPOSED)
✅ cli.py - Command-line interface (EXPOSED)
✅ main.py - Main agent orchestration (EXPOSED)
✅ data_collector.py - Telemetry aggregation (EXPOSED)
✅ incident_analyzer.py - Root cause analysis (EXPOSED)
✅ incident_reporter.py - Incident reporting (EXPOSED)
✅ insight_engine.py - Narrative generation (EXPOSED)
✅ postmortem_generator.py - Postmortem reports (EXPOSED)
✅ remediation_advisor.py - Remediation suggestions (EXPOSED)
⚠️ sample_workflow.py - Demo script (NOT EXPOSED - internal use)
⚠️ test_workflow.py - Test utilities (NOT EXPOSED - internal use)
⚠️ integrations/ - Package directory (NOT EXPOSED - subpackage)

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

# Import classes for backward compatibility
# Import modules for dynamic access and mocking
from . import (
    cli,
    data_collector,
    incident_analyzer,
    incident_reporter,
    insight_engine,
    main,
    postmortem_generator,
    remediation_advisor,
    webhook_server,
)
from .data_collector import IncidentContextCollector
from .incident_analyzer import IncidentAnalyzer
from .incident_reporter import IncidentReporter
from .insight_engine import InsightEngine
from .postmortem_generator import PostmortemGenerator
from .remediation_advisor import RemediationAdvisor

__all__ = [
    # Classes (backward compatibility)
    "IncidentContextCollector",
    "IncidentAnalyzer",
    "InsightEngine",
    "RemediationAdvisor",
    "IncidentReporter",
    "PostmortemGenerator",
    # Modules (for dynamic imports and mocking)
    "webhook_server",
    "cli",
    "main",
    "data_collector",
    "incident_analyzer",
    "incident_reporter",
    "insight_engine",
    "postmortem_generator",
    "remediation_advisor",
]
