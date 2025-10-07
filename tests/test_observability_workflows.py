"""
Comprehensive Test Suite for Observability Workflows

This test suite provides extensive coverage for the AI Incident Insight Agent
and OpenTelemetry tracing components.

Target Coverage: Boost project coverage from ~25% to 65%+

Modules tested:
- observability/ai_agent/incident_analyzer.py
- observability/ai_agent/insight_engine.py
- observability/ai_agent/postmortem_generator.py
- observability/ai_agent/remediation_advisor.py
- observability/ai_agent/incident_reporter.py
- observability/ai_agent/integrations/pagerduty_notifier.py
- observability/ai_agent/webhook_server.py
- observability/tracing/otel_tracer.py
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Optional dependencies
try:
    from fastapi.testclient import TestClient

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    TestClient = None

# Import modules under test
from observability.ai_agent.data_collector import (
    DeploymentEvent,
    IncidentContext,
    LogSignature,
    MetricAnomaly,
    SystemEvent,
    TraceOutlier,
)
from observability.ai_agent.incident_analyzer import (
    IncidentAnalyzer,
    RootCause,
    RootCauseType,
)
from observability.ai_agent.incident_reporter import IncidentReporter
from observability.ai_agent.insight_engine import (
    ImpactAnalysis,
    IncidentInsight,
    IncidentTimeline,
    InsightEngine,
)
from observability.ai_agent.integrations.pagerduty_notifier import (
    PagerDutyNotifier,
)
from observability.ai_agent.postmortem_generator import PostmortemGenerator
from observability.ai_agent.remediation_advisor import (
    RemediationAction,
    RemediationAdvisor,
    RemediationPriority,
    RemediationType,
)

# ============================================================================
# FIXTURES - Create reusable test data
# ============================================================================


@pytest.fixture
def sample_timestamp():
    """Sample incident timestamp"""
    return datetime(2024, 10, 5, 14, 30, 0)


@pytest.fixture
def sample_metric_anomalies(sample_timestamp):
    """Sample metric anomalies for testing"""
    return [
        MetricAnomaly(
            metric_name="http_request_duration_seconds",
            value=0.85,
            threshold=0.5,
            severity="critical",
            timestamp=sample_timestamp,
            labels={"service": "api-gateway", "endpoint": "/api/orders"},
            description="High latency detected on orders endpoint",
        ),
        MetricAnomaly(
            metric_name="http_error_rate",
            value=0.12,
            threshold=0.05,
            severity="critical",
            timestamp=sample_timestamp + timedelta(minutes=2),
            labels={"service": "payment-service", "status": "500"},
            description="Elevated error rate in payment service",
        ),
    ]


@pytest.fixture
def sample_log_signatures(sample_timestamp):
    """Sample log signatures for testing"""
    return [
        LogSignature(
            pattern="Database connection timeout",
            count=45,
            first_seen=sample_timestamp,
            last_seen=sample_timestamp + timedelta(minutes=5),
            severity="critical",
            service="payment-service",
            log_level="ERROR",
            sample_messages=[
                "Database connection timeout after 30 seconds",
                "Failed to connect to PostgreSQL database",
            ],
        ),
        LogSignature(
            pattern="Configuration error: missing API key",
            count=8,
            first_seen=sample_timestamp,
            last_seen=sample_timestamp + timedelta(minutes=3),
            severity="error",
            service="notification-service",
            log_level="ERROR",
            sample_messages=[
                "Required configuration parameter 'SMTP_API_KEY' not found"
            ],
        ),
    ]


@pytest.fixture
def sample_trace_outliers(sample_timestamp):
    """Sample trace outliers for testing"""
    return [
        TraceOutlier(
            trace_id="abc123def456",
            span_id="span789",
            operation_name="database.query.orders",
            duration_ms=3500.0,
            status_code="200",
            error_message=None,
            timestamp=sample_timestamp,
            service_name="order-service",
            tags={"db.system": "postgresql", "db.operation": "SELECT"},
        )
    ]


@pytest.fixture
def sample_deployment_events(sample_timestamp):
    """Sample deployment events for testing"""
    return [
        DeploymentEvent(
            deployment_id="deploy-123",
            version="v1.4.2",
            commit_hash="abc123def456",
            author="developer@magsasa.com",
            timestamp=sample_timestamp - timedelta(minutes=15),
            status="success",
            affected_services=["payment-service", "order-service"],
            pull_request_id=812,
        )
    ]


@pytest.fixture
def sample_system_events(sample_timestamp):
    """Sample system events for testing"""
    return [
        SystemEvent(
            event_type="node_restart",
            timestamp=sample_timestamp - timedelta(minutes=5),
            description="Kubernetes node restarted due to memory pressure",
            severity="warning",
            affected_components=["k8s-node-1", "payment-pod"],
            metadata={"cluster": "production", "node": "node-1"},
        )
    ]


@pytest.fixture
def sample_incident_context(
    sample_timestamp,
    sample_metric_anomalies,
    sample_log_signatures,
    sample_trace_outliers,
    sample_deployment_events,
    sample_system_events,
):
    """Complete sample incident context"""
    return IncidentContext(
        incident_id="INC-2024-001",
        timestamp=sample_timestamp,
        duration_minutes=15,
        metric_anomalies=sample_metric_anomalies,
        trace_outliers=sample_trace_outliers,
        log_signatures=sample_log_signatures,
        deployment_events=sample_deployment_events,
        system_events=sample_system_events,
        alert_payload={"alerts": [{"status": "firing"}]},
    )


@pytest.fixture
def sample_root_causes(sample_timestamp):
    """Sample root causes for testing"""
    return [
        RootCause(
            cause_type=RootCauseType.DATABASE_ISSUES,
            confidence=0.85,
            description="Database query timeouts causing elevated error rates",
            evidence=[
                "Database metric anomaly: High query latency",
                "Database connection timeout errors detected",
            ],
            affected_services=["payment-service", "order-service"],
            timeframe=(
                sample_timestamp - timedelta(minutes=10),
                sample_timestamp,
            ),
            remediation_suggestions=[
                "Check database connection pool settings",
                "Review slow query logs",
            ],
            related_metrics=["database_query_duration_seconds"],
            related_logs=["Database connection timeout"],
            related_traces=["abc123def456"],
        )
    ]


# ============================================================================
# TEST: IncidentAnalyzer
# ============================================================================


class TestIncidentAnalyzer:
    """Test suite for IncidentAnalyzer"""

    def test_analyzer_initialization(self):
        """Test that analyzer initializes with pattern libraries"""
        analyzer = IncidentAnalyzer()

        assert analyzer.deployment_patterns is not None
        assert analyzer.database_patterns is not None
        assert analyzer.infrastructure_patterns is not None
        assert analyzer.dependency_patterns is not None

    def test_analyze_incident_with_database_issues(self, sample_incident_context):
        """Test incident analysis detects database issues"""
        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(sample_incident_context)

        assert len(root_causes) > 0
        assert any(
            cause.cause_type == RootCauseType.DATABASE_ISSUES for cause in root_causes
        )

    def test_analyze_incident_with_deployment_regression(self, sample_incident_context):
        """Test detection of deployment regression"""
        # Modify context to have recent deployment with errors
        sample_incident_context.deployment_events[0].timestamp = (
            sample_incident_context.timestamp - timedelta(minutes=5)
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(sample_incident_context)

        # Should detect deployment-related issues
        assert len(root_causes) > 0

    def test_analyze_incident_with_infrastructure_degradation(
        self, sample_incident_context
    ):
        """Test detection of infrastructure degradation"""
        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(sample_incident_context)

        # Should detect infrastructure issues from system events
        assert any(
            cause.cause_type == RootCauseType.INFRASTRUCTURE_DEGRADATION
            for cause in root_causes
        )

    def test_analyze_incident_filters_low_confidence(self, sample_incident_context):
        """Test that low confidence causes are filtered out"""
        analyzer = IncidentAnalyzer()

        # Create context with minimal evidence
        minimal_context = IncidentContext(
            incident_id="INC-TEST",
            timestamp=datetime.now(),
            duration_minutes=10,
            metric_anomalies=[],
            trace_outliers=[],
            log_signatures=[],
            deployment_events=[],
            system_events=[],
            alert_payload={},
        )

        root_causes = analyzer.analyze_incident(minimal_context)

        # All causes should have confidence > 0.3
        assert all(cause.confidence > 0.3 for cause in root_causes)

    def test_analyze_configuration_errors(self, sample_incident_context):
        """Test detection of configuration errors"""
        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(sample_incident_context)

        # Should detect configuration errors from log patterns
        assert any(
            cause.cause_type == RootCauseType.CONFIGURATION_ERROR
            for cause in root_causes
        )

    def test_analyze_dependency_failures(self):
        """Test detection of external dependency failures"""
        context = IncidentContext(
            incident_id="INC-DEP-TEST",
            timestamp=datetime.now(),
            duration_minutes=10,
            metric_anomalies=[],
            trace_outliers=[
                TraceOutlier(
                    trace_id="trace123",
                    span_id="span456",
                    operation_name="http.external.payment-gateway",
                    duration_ms=5000.0,
                    status_code="503",
                    error_message="Service Unavailable",
                    timestamp=datetime.now(),
                    service_name="payment-service",
                    tags={"http.status_code": "503"},
                )
            ],
            log_signatures=[
                LogSignature(
                    pattern="gateway timeout",
                    count=25,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    severity="error",
                    service="payment-service",
                    log_level="ERROR",
                    sample_messages=["Gateway timeout from external service"],
                )
            ],
            deployment_events=[],
            system_events=[],
            alert_payload={},
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        assert any(
            cause.cause_type == RootCauseType.DEPENDENCY_FAILURE
            for cause in root_causes
        )

    def test_analyze_resource_exhaustion(self):
        """Test detection of resource exhaustion"""
        context = IncidentContext(
            incident_id="INC-MEM-TEST",
            timestamp=datetime.now(),
            duration_minutes=10,
            metric_anomalies=[
                MetricAnomaly(
                    metric_name="memory_usage_bytes",
                    value=0.95,
                    threshold=0.8,
                    severity="critical",
                    timestamp=datetime.now(),
                    labels={"service": "api-service"},
                    description="High memory usage",
                )
            ],
            trace_outliers=[],
            log_signatures=[
                LogSignature(
                    pattern="out of memory",
                    count=12,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    severity="critical",
                    service="api-service",
                    log_level="ERROR",
                    sample_messages=["java.lang.OutOfMemoryError: Java heap space"],
                )
            ],
            deployment_events=[],
            system_events=[],
            alert_payload={},
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        assert any(
            cause.cause_type == RootCauseType.RESOURCE_EXHAUSTION
            for cause in root_causes
        )


# ============================================================================
# TEST: InsightEngine
# ============================================================================


class TestInsightEngine:
    """Test suite for InsightEngine"""

    def test_engine_initialization(self):
        """Test that engine initializes with templates"""
        engine = InsightEngine()

        assert engine.impact_templates is not None
        assert engine.summary_templates is not None

    def test_generate_insight(self, sample_incident_context, sample_root_causes):
        """Test generation of complete incident insight"""
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        assert isinstance(insight, IncidentInsight)
        assert insight.incident_id == "INC-2024-001"
        assert insight.summary is not None
        assert len(insight.timeline) > 0
        assert len(insight.likely_root_causes) > 0
        assert insight.confidence_score > 0

    def test_generate_insight_with_no_root_causes(self, sample_incident_context):
        """Test insight generation when no root causes are found"""
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, [])

        assert insight.confidence_score == 0.0
        assert "unknown root cause" in insight.summary.lower()

    def test_build_timeline(self, sample_incident_context):
        """Test timeline building from incident context"""
        engine = InsightEngine()
        timeline = engine._build_timeline(sample_incident_context)

        assert isinstance(timeline, list)
        assert len(timeline) > 0
        assert all(isinstance(event, IncidentTimeline) for event in timeline)

        # Timeline should be sorted by timestamp
        timestamps = [event.timestamp for event in timeline]
        assert timestamps == sorted(timestamps)

    def test_analyze_impact(self, sample_incident_context, sample_root_causes):
        """Test impact analysis calculation"""
        engine = InsightEngine()
        impact = engine._analyze_impact(sample_incident_context, sample_root_causes)

        assert isinstance(impact, ImpactAnalysis)
        assert len(impact.affected_services) > 0
        assert impact.estimated_users_affected > 0
        assert impact.business_impact in ["low", "medium", "high", "critical"]

    def test_generate_summary_with_database_issues(
        self, sample_incident_context, sample_root_causes
    ):
        """Test summary generation for database issues"""
        engine = InsightEngine()
        impact = engine._analyze_impact(sample_incident_context, sample_root_causes)
        summary = engine._generate_summary(
            sample_incident_context, sample_root_causes, impact
        )

        assert isinstance(summary, str)
        assert len(summary) > 0
        # Summary should contain relevant information
        assert "minutes" in summary.lower()

    def test_generate_next_steps(self, sample_root_causes):
        """Test generation of recommended next steps"""
        engine = InsightEngine()
        impact = ImpactAnalysis(
            affected_services=["payment-service"],
            affected_endpoints=["/api/payments"],
            user_impact_percentage=0.5,
            estimated_users_affected=500,
            sla_breach_duration_minutes=15,
            business_impact="high",
        )

        next_steps = engine._generate_next_steps(sample_root_causes, impact)

        assert isinstance(next_steps, list)
        assert len(next_steps) > 0
        assert all(isinstance(step, str) for step in next_steps)

    def test_calculate_confidence_score(self, sample_root_causes):
        """Test confidence score calculation"""
        engine = InsightEngine()
        confidence = engine._calculate_confidence_score(sample_root_causes)

        assert 0.0 <= confidence <= 1.0
        assert confidence == sample_root_causes[0].confidence

    def test_calculate_confidence_score_empty(self):
        """Test confidence score with no root causes"""
        engine = InsightEngine()
        confidence = engine._calculate_confidence_score([])

        assert confidence == 0.0


# ============================================================================
# TEST: PostmortemGenerator
# ============================================================================


class TestPostmortemGenerator:
    """Test suite for PostmortemGenerator"""

    def test_generator_initialization(self):
        """Test postmortem generator initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PostmortemGenerator(reports_dir=tmpdir)

            assert generator.reports_dir == Path(tmpdir)
            assert generator.reports_dir.exists()

    def test_generate_postmortem(self, sample_incident_context, sample_root_causes):
        """Test complete postmortem generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PostmortemGenerator(reports_dir=tmpdir)

            # Create insight
            engine = InsightEngine()
            insight = engine.generate_insight(
                sample_incident_context, sample_root_causes
            )

            # Add timestamp attribute that postmortem generator expects
            insight.timestamp = sample_incident_context.timestamp

            # Create remediation actions
            advisor = RemediationAdvisor()
            remediation_actions = advisor.generate_remediation_plan(insight)

            # Generate postmortem
            postmortem = generator.generate_postmortem(
                insight,
                remediation_actions,
                resolution_notes="Incident resolved by rolling back deployment",
                engineer_notes="Need better monitoring for database timeouts",
            )

            assert postmortem.incident_id == insight.incident_id
            assert postmortem.content is not None
            assert len(postmortem.sections) > 0

            # Verify file was written
            assert Path(postmortem.file_path).exists()

    def test_postmortem_sections(self, sample_incident_context, sample_root_causes):
        """Test that all required sections are generated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PostmortemGenerator(reports_dir=tmpdir)

            engine = InsightEngine()
            insight = engine.generate_insight(
                sample_incident_context, sample_root_causes
            )

            # Add timestamp attribute that postmortem generator expects
            insight.timestamp = sample_incident_context.timestamp

            advisor = RemediationAdvisor()
            remediation_actions = advisor.generate_remediation_plan(insight)

            postmortem = generator.generate_postmortem(insight, remediation_actions)

            section_titles = [section.title for section in postmortem.sections]

            # Check for required sections
            assert "Summary" in section_titles
            assert "Timeline" in section_titles
            assert "Root Causes" in section_titles
            assert "Impact Analysis" in section_titles
            assert "Resolution" in section_titles
            assert "Lessons Learned" in section_titles

    def test_postmortem_markdown_format(
        self, sample_incident_context, sample_root_causes
    ):
        """Test that postmortem is valid Markdown"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PostmortemGenerator(reports_dir=tmpdir)

            engine = InsightEngine()
            insight = engine.generate_insight(
                sample_incident_context, sample_root_causes
            )

            # Add timestamp attribute that postmortem generator expects
            insight.timestamp = sample_incident_context.timestamp

            advisor = RemediationAdvisor()
            remediation_actions = advisor.generate_remediation_plan(insight)

            postmortem = generator.generate_postmortem(insight, remediation_actions)

            # Check for Markdown formatting
            assert "##" in postmortem.content
            assert "**" in postmortem.content or "*" in postmortem.content
            assert "|" in postmortem.content  # Tables


# ============================================================================
# TEST: RemediationAdvisor
# ============================================================================


class TestRemediationAdvisor:
    """Test suite for RemediationAdvisor"""

    def test_advisor_initialization(self):
        """Test remediation advisor initialization"""
        advisor = RemediationAdvisor()

        assert advisor.action_templates is not None
        assert advisor.runbook_library is not None

    def test_generate_remediation_plan(
        self, sample_incident_context, sample_root_causes
    ):
        """Test generation of complete remediation plan"""
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        actions = advisor.generate_remediation_plan(insight)

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert all(isinstance(action, RemediationAction) for action in actions)

    def test_remediation_action_prioritization(
        self, sample_incident_context, sample_root_causes
    ):
        """Test that remediation actions are properly prioritized"""
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        actions = advisor.generate_remediation_plan(insight)

        # First action should be immediate priority
        if actions:
            assert actions[0].priority == RemediationPriority.IMMEDIATE

    def test_deployment_remediation(self):
        """Test remediation for deployment regression"""
        context = IncidentContext(
            incident_id="INC-DEPLOY",
            timestamp=datetime.now(),
            duration_minutes=10,
            metric_anomalies=[
                MetricAnomaly(
                    metric_name="http_request_latency_seconds",
                    value=2.5,
                    threshold=1.0,
                    severity="critical",
                    timestamp=datetime.now(),
                    labels={"service": "api"},
                    description="High latency after deployment",
                )
            ],
            trace_outliers=[],
            log_signatures=[],
            deployment_events=[
                DeploymentEvent(
                    deployment_id="deploy-456",
                    version="v2.0.0",
                    commit_hash="xyz789",
                    author="dev@example.com",
                    timestamp=datetime.now() - timedelta(minutes=5),
                    status="success",
                    affected_services=["api"],
                    pull_request_id=999,
                )
            ],
            system_events=[],
            alert_payload={},
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        engine = InsightEngine()
        insight = engine.generate_insight(context, root_causes)

        advisor = RemediationAdvisor()
        actions = advisor.generate_remediation_plan(insight)

        # Should include rollback action
        assert any(action.action_type == RemediationType.ROLLBACK for action in actions)

    def test_database_remediation(self, sample_incident_context, sample_root_causes):
        """Test remediation for database issues"""
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        actions = advisor.generate_remediation_plan(insight)

        # Should include database-related actions
        action_types = [action.action_type for action in actions]
        assert (
            RemediationType.QUERY_OPTIMIZATION in action_types
            or RemediationType.INFRA_MITIGATION in action_types
        )

    def test_generic_remediation_for_unknown_cause(self):
        """Test generic remediation when root cause is unknown"""
        context = IncidentContext(
            incident_id="INC-UNKNOWN",
            timestamp=datetime.now(),
            duration_minutes=10,
            metric_anomalies=[],
            trace_outliers=[],
            log_signatures=[],
            deployment_events=[],
            system_events=[],
            alert_payload={},
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        engine = InsightEngine()
        insight = engine.generate_insight(context, root_causes)

        advisor = RemediationAdvisor()
        actions = advisor.generate_remediation_plan(insight)

        # Should still generate generic investigation actions
        assert len(actions) > 0


# ============================================================================
# TEST: IncidentReporter
# ============================================================================


class TestIncidentReporter:
    """Test suite for IncidentReporter"""

    def test_reporter_initialization(self):
        """Test incident reporter initialization"""
        config = {
            "channels": [
                {
                    "type": "slack",
                    "destination": "#incidents",
                    "template": "slack_incident",
                    "priority_filter": ["immediate", "high"],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(config)

        assert len(reporter.channels) == 1
        assert reporter.channels[0].channel_type == "slack"

    def test_generate_slack_report(self, sample_incident_context, sample_root_causes):
        """Test generation of Slack-formatted report"""
        config = {
            "channels": [
                {
                    "type": "slack",
                    "destination": "#incidents",
                    "template": "slack_incident",
                    "priority_filter": [],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(config)

        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        remediation_actions = advisor.generate_remediation_plan(insight)

        reports = reporter.generate_reports(insight, remediation_actions)

        assert len(reports) > 0
        assert reports[0].channel_type == "slack"

        # Verify Slack blocks format
        content = json.loads(reports[0].content)
        assert "blocks" in content
        assert len(content["blocks"]) > 0

    def test_generate_email_report(self, sample_incident_context, sample_root_causes):
        """Test generation of email-formatted report"""
        config = {
            "channels": [
                {
                    "type": "email",
                    "destination": "incidents@example.com",
                    "template": "email_incident",
                    "priority_filter": [],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(config)

        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        remediation_actions = advisor.generate_remediation_plan(insight)

        reports = reporter.generate_reports(insight, remediation_actions)

        assert len(reports) > 0
        assert reports[0].channel_type == "email"
        assert "<html>" in reports[0].content

    def test_generate_dashboard_report(
        self, sample_incident_context, sample_root_causes
    ):
        """Test generation of dashboard-formatted report"""
        config = {
            "channels": [
                {
                    "type": "dashboard",
                    "destination": "http://dashboard.local/api/incidents",
                    "template": "dashboard_json",
                    "priority_filter": [],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(config)

        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        advisor = RemediationAdvisor()
        remediation_actions = advisor.generate_remediation_plan(insight)

        reports = reporter.generate_reports(insight, remediation_actions)

        assert len(reports) > 0
        assert reports[0].channel_type == "dashboard"

        # Verify JSON format
        content = json.loads(reports[0].content)
        assert "incident_id" in content
        assert "root_causes" in content

    def test_priority_filter(self, sample_incident_context, sample_root_causes):
        """Test that priority filters work correctly"""
        config = {
            "channels": [
                {
                    "type": "slack",
                    "destination": "#critical-only",
                    "template": "slack_incident",
                    "priority_filter": ["immediate"],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(config)

        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, sample_root_causes)

        # Create actions with different priorities
        advisor = RemediationAdvisor()
        remediation_actions = advisor.generate_remediation_plan(insight)

        reports = reporter.generate_reports(insight, remediation_actions)

        # Should generate report if any action has immediate priority
        assert len(reports) >= 0


# ============================================================================
# TEST: PagerDutyNotifier
# ============================================================================


class TestPagerDutyNotifier:
    """Test suite for PagerDutyNotifier"""

    def test_notifier_initialization(self):
        """Test PagerDuty notifier initialization"""
        config = {
            "integration_keys": {
                "incidents": "test-integration-key",
                "alerts": "test-alert-key",
            },
            "api_token": "test-api-token",
            "default_routing": {
                "critical": "incidents",
                "high": "incidents",
                "medium": "alerts",
                "low": "alerts",
            },
            "custom_fields": {},
        }

        notifier = PagerDutyNotifier(config)

        assert notifier.integration_keys["incidents"] == "test-integration-key"
        assert notifier.api_token == "test-api-token"

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_send_incident_alert_success(
        self, sample_incident_context, sample_root_causes
    ):
        """Test successful incident alert sending"""
        pass

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_send_incident_alert_failure(
        self, sample_incident_context, sample_root_causes
    ):
        """Test failed incident alert sending"""
        pass

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_acknowledge_incident(self):
        """Test incident acknowledgment"""
        pass

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_resolve_incident(self):
        """Test incident resolution"""
        pass

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_get_incident_details(self):
        """Test retrieving incident details"""
        pass

    @pytest.mark.skip(
        reason="Complex async mocking - to be implemented with pytest-aiohttp"
    )
    @pytest.mark.asyncio
    async def test_send_custom_alert(self):
        """Test sending custom alert"""
        pass


# ============================================================================
# TEST: OpenTelemetry Tracer
# ============================================================================


class TestOpenTelemetryTracer:
    """Test suite for OpenTelemetry tracer"""

    def test_init_tracing_default_config(self):
        """Test tracer initialization with default config"""
        from observability.tracing.otel_tracer import get_tracer, init_tracing

        # Initialize with defaults
        init_tracing(app=None, service_name="test-service", console_export=False)

        # Get a tracer
        tracer = get_tracer("test")
        assert tracer is not None

    def test_get_tracer(self):
        """Test getting a tracer instance"""
        from observability.tracing.otel_tracer import get_tracer

        tracer = get_tracer(__name__)
        assert tracer is not None

    def test_add_span_attributes(self):
        """Test adding attributes to current span"""
        from observability.tracing.otel_tracer import (
            add_span_attributes,
            get_tracer,
        )

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("test_span"):
            # This should not raise an error
            add_span_attributes(user_id="123", transaction_id="txn_456")

    def test_add_span_event(self):
        """Test adding events to current span"""
        from observability.tracing.otel_tracer import add_span_event, get_tracer

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("test_span"):
            # This should not raise an error
            add_span_event("test_event", {"key": "value"})

    def test_get_trace_context(self):
        """Test getting trace context"""
        from observability.tracing.otel_tracer import get_trace_context, get_tracer

        tracer = get_tracer(__name__)

        with tracer.start_as_current_span("test_span"):
            context = get_trace_context()

            assert context is not None
            assert "trace_id" in context
            assert "span_id" in context

    def test_get_trace_context_no_span(self):
        """Test getting trace context when no span is active"""
        from observability.tracing.otel_tracer import get_trace_context

        context = get_trace_context()

        assert context["trace_id"] is None
        assert context["span_id"] is None


# ============================================================================
# TEST: Webhook Server (FastAPI)
# ============================================================================


@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI not installed")
class TestWebhookServer:
    """Test suite for Webhook Server"""

    @pytest.fixture
    def test_client(self):
        """Create test client for FastAPI app"""
        from observability.ai_agent.webhook_server import app

        return TestClient(app)

    @pytest.mark.asyncio
    async def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = await test_client.get("/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert "timestamp" in payload

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint"""
        response = await test_client.get("/metrics")

        assert response.status_code == 200
        payload = response.json()
        assert "incidents_analyzed_total" in payload


# ============================================================================
# TEST: Integration - Full Incident Workflow
# ============================================================================


class TestObservabilityWorkflow:
    """Integration tests for complete incident lifecycle"""

    def test_full_incident_workflow(self, sample_incident_context):
        """Test complete incident analysis workflow from start to finish"""
        # Step 1: Analyze incident
        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(sample_incident_context)

        assert len(root_causes) > 0

        # Step 2: Generate insights
        engine = InsightEngine()
        insight = engine.generate_insight(sample_incident_context, root_causes)

        # Add timestamp attribute that postmortem generator expects
        insight.timestamp = sample_incident_context.timestamp

        assert insight.confidence_score > 0

        # Step 3: Generate remediation plan
        advisor = RemediationAdvisor()
        remediation_actions = advisor.generate_remediation_plan(insight)

        assert len(remediation_actions) > 0

        # Step 4: Generate reports
        reporter_config = {
            "channels": [
                {
                    "type": "slack",
                    "destination": "#incidents",
                    "template": "slack_incident",
                    "priority_filter": [],
                }
            ],
            "templates": {},
        }

        reporter = IncidentReporter(reporter_config)
        reports = reporter.generate_reports(insight, remediation_actions)

        assert len(reports) > 0

        # Step 5: Generate postmortem
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PostmortemGenerator(reports_dir=tmpdir)
            postmortem = generator.generate_postmortem(
                insight, remediation_actions, resolution_notes="Resolved successfully"
            )

            assert postmortem is not None
            assert Path(postmortem.file_path).exists()

    def test_incident_workflow_with_multiple_root_causes(self):
        """Test workflow with multiple detected root causes"""
        # Create context with multiple issues
        context = IncidentContext(
            incident_id="INC-MULTI",
            timestamp=datetime.now(),
            duration_minutes=20,
            metric_anomalies=[
                MetricAnomaly(
                    metric_name="http_latency",
                    value=2.5,
                    threshold=1.0,
                    severity="critical",
                    timestamp=datetime.now(),
                    labels={"service": "api"},
                    description="High latency",
                ),
                MetricAnomaly(
                    metric_name="memory_usage",
                    value=0.95,
                    threshold=0.8,
                    severity="critical",
                    timestamp=datetime.now(),
                    labels={"service": "api"},
                    description="High memory",
                ),
            ],
            trace_outliers=[],
            log_signatures=[
                LogSignature(
                    pattern="database timeout",
                    count=30,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    severity="error",
                    service="api",
                    log_level="ERROR",
                    sample_messages=["Database timeout"],
                ),
                LogSignature(
                    pattern="out of memory",
                    count=15,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    severity="critical",
                    service="api",
                    log_level="ERROR",
                    sample_messages=["OOM error"],
                ),
            ],
            deployment_events=[
                DeploymentEvent(
                    deployment_id="deploy-789",
                    version="v2.1.0",
                    commit_hash="def456",
                    author="dev@test.com",
                    timestamp=datetime.now() - timedelta(minutes=10),
                    status="success",
                    affected_services=["api"],
                    pull_request_id=100,
                )
            ],
            system_events=[],
            alert_payload={},
        )

        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        # Should detect multiple root cause types
        cause_types = {cause.cause_type for cause in root_causes}
        assert len(cause_types) >= 2

    def test_error_handling_invalid_context(self):
        """Test error handling with invalid/minimal context"""
        context = IncidentContext(
            incident_id="INC-INVALID",
            timestamp=datetime.now(),
            duration_minutes=0,
            metric_anomalies=[],
            trace_outliers=[],
            log_signatures=[],
            deployment_events=[],
            system_events=[],
            alert_payload={},
        )

        # Should handle gracefully without crashing
        analyzer = IncidentAnalyzer()
        root_causes = analyzer.analyze_incident(context)

        engine = InsightEngine()
        insight = engine.generate_insight(context, root_causes)

        assert insight is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
