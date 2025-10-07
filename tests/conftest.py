"""
Ensures the project root is in sys.path so imports like `core.*` work.
Fixes `ModuleNotFoundError: No module named 'core'`.
"""

import os
import sqlite3
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure packages/core/src is importable for core module tests
CORE_SRC_PATH = os.path.join(PROJECT_ROOT, "packages", "core", "src")
if os.path.exists(CORE_SRC_PATH) and CORE_SRC_PATH not in sys.path:
    sys.path.insert(0, CORE_SRC_PATH)


@pytest.fixture
def test_data():
    """Comprehensive test data for financial metrics and operational values."""
    return {
        # Financial metrics
        "total_loans": 5,
        "total_principal": 245000.0,
        "total_paid": 81667.0,
        "total_outstanding": 163333.0,
        "total_collected_amount": 75000.0,
        "total_scheduled_amount": 225000.0,
        "total_interest_charged": 24500.0,
        "total_interest_collected": 8167.0,
        # Payment metrics
        "scheduled_payments": 60,
        "completed_payments": 20,
        "payment_completion_rate": 33.3,
        "collection_efficiency": 33.3,
        "collection_rate": 33.3,
        # Farmer metrics
        "total_farmers": 5,
        "active_farmers": 5,
        "farmers_with_loans": 5,
        "average_farm_size": 2.8,
        "total_farm_area": 14.0,
        "farmer_utilization_rate": 100.0,
        # Interest metrics
        "average_interest_rate": 10.0,
        "interest_collection_rate": 33.3,
        # Calculated metrics
        "average_loan_size": 49000.0,
        "average_payment_amount": 3750.0,
    }


@pytest.fixture
def export_context():
    """Expected export structure and validation data."""
    return {
        "farmer_export": {
            "expected_columns": [
                "id",
                "name",
                "phone",
                "email",
                "farm_size",
                "location",
                "crop_type",
            ],
            "expected_rows": 5,
            "format": "CSV",
            "data_validation": True,
        },
        "payment_export": {
            "expected_columns": [
                "id",
                "farmer_id",
                "amount",
                "payment_date",
                "status",
                "payment_method",
            ],
            "expected_rows": 60,
            "format": "JSON",
            "data_validation": True,
        },
        "financial_export": {
            "expected_columns": ["metric", "value", "target", "variance"],
            "expected_rows": 12,
            "format": "PDF",
            "data_validation": False,
        },
        "loan_export": {
            "expected_columns": [
                "farmer_name",
                "loan_amount",
                "interest_rate",
                "term",
                "status",
            ],
            "expected_rows": 5,
            "format": "XLSX",
            "data_validation": True,
        },
    }


@pytest.fixture
def scenario_context():
    """Mock scenario keys and report metadata."""
    return {
        "loan_portfolio_summary": {
            "report_type": "Loan Portfolio Summary",
            "calculations": {
                "average_loan_size": "total_principal / total_loans",
                "collection_rate": "(total_paid / total_principal) * 100",
                "outstanding_percentage": "(total_outstanding / total_principal) * 100",
            },
        },
        "monthly_payment_report": {
            "report_type": "Monthly Payment Report",
            "calculations": {
                "payment_completion_rate": "(completed_payments / scheduled_payments) * 100",
                "collection_efficiency": "(total_collected_amount / total_scheduled_amount) * 100",
                "average_payment_amount": "total_scheduled_amount / scheduled_payments",
            },
        },
        "farmer_performance_report": {
            "report_type": "Farmer Performance Report",
            "calculations": {
                "average_farm_size": "total_farm_area / total_farmers",
                "farmer_utilization_rate": "(farmers_with_loans / total_farmers) * 100",
                "active_farmer_percentage": "(active_farmers / total_farmers) * 100",
            },
        },
        "interest_income_report": {
            "report_type": "Interest Income Report",
            "calculations": {
                "average_interest_rate": "(total_interest_charged / total_principal) * 100",
                "interest_collection_rate": "(total_interest_collected / total_interest_charged) * 100",
                "interest_to_principal_ratio": "(total_interest_charged / total_principal) * 100",
            },
        },
    }


@pytest.fixture
def kpi_metrics():
    """KPI names, targets, and expected outcomes."""
    return {
        "loan_performance": {
            "approval_rate": {"value": 87.0, "target": 85.0, "unit": "%"},
            "default_rate": {"value": 2.1, "target": 5.0, "unit": "%"},
            "collection_rate": {"value": 95.5, "target": 90.0, "unit": "%"},
            "average_processing_time": {"value": 3.2, "target": 5.0, "unit": "days"},
        },
        "operational_efficiency": {
            "farmers_per_officer": {"value": 45.0, "target": 50.0, "unit": "farmers"},
            "applications_per_day": {
                "value": 8.5,
                "target": 10.0,
                "unit": "applications",
            },
            "site_visits_per_week": {"value": 12.0, "target": 15.0, "unit": "visits"},
            "documentation_completion_rate": {
                "value": 98.2,
                "target": 95.0,
                "unit": "%",
            },
        },
        "financial_performance": {
            "portfolio_growth_rate": {"value": 15.3, "target": 12.0, "unit": "%"},
            "interest_margin": {"value": 8.5, "target": 8.0, "unit": "%"},
            "cost_per_loan": {"value": 2500.0, "target": 3000.0, "unit": "PHP"},
            "revenue_per_farmer": {"value": 12500.0, "target": 10000.0, "unit": "PHP"},
        },
        "customer_satisfaction": {
            "farmer_satisfaction_score": {"value": 4.2, "target": 4.0, "unit": "/5"},
            "complaint_resolution_time": {"value": 2.1, "target": 3.0, "unit": "days"},
            "repeat_customer_rate": {"value": 78.5, "target": 75.0, "unit": "%"},
            "referral_rate": {"value": 35.2, "target": 30.0, "unit": "%"},
        },
    }


@pytest.fixture
def database_connection():
    """Database connection fixture for testing."""
    db_path = "src/agsense.db"
    if not os.path.exists(db_path):
        db_path = "agsense.db"

    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture
def accuracy_scenarios():
    """Database accuracy test scenarios."""
    return {
        "farmer_data_integrity": {
            "table": "farmers",
            "test_data": {
                "name": "Test Farmer Accuracy",
                "phone": "09171234567",
                "email": "test@accuracy.com",
                "farm_size": 2.75,
                "location": "Test Location",
                "crop_type": "Rice",
            },
            "precision_fields": ["farm_size"],
            "expected_precision": 2,
        },
        "payment_calculation_accuracy": {
            "table": "payments",
            "test_data": {
                "farmer_id": 1,
                "amount": 3750.50,
                "payment_date": "2025-09-18",
                "status": "PAID",
                "payment_method": "Bank Transfer",
            },
            "precision_fields": ["amount"],
            "expected_precision": 2,
        },
    }


@pytest.fixture
def integrity_scenarios():
    """Referential integrity test scenarios."""
    return {
        "farmer_payment_relationship": {
            "description": "Payments must reference valid farmers",
            "parent_table": "farmers",
            "child_table": "payments",
            "foreign_key": "farmer_id",
            "test_valid_reference": True,
            "test_invalid_reference": True,
        },
        "user_farmer_relationship": {
            "description": "Users may reference farmer profiles",
            "parent_table": "farmers",
            "child_table": "users",
            "foreign_key": "farmer_id",
            "test_valid_reference": True,
            "test_invalid_reference": False,
        },
    }


@pytest.fixture
def realtime_scenarios():
    """Real-time update test scenarios."""
    return {
        "payment_status_updates": {
            "update_type": "Payment Status Updates",
            "trigger_event": "Payment Received",
            "affected_components": ["Dashboard", "Loan Status", "Payment History"],
            "update_latency_ms": 250,
            "expected_latency_ms": 500,
        },
        "farmer_profile_changes": {
            "update_type": "Farmer Profile Changes",
            "trigger_event": "Profile Updated",
            "affected_components": [
                "Farmer List",
                "Loan Applications",
                "Officer Dashboard",
            ],
            "update_latency_ms": 180,
            "expected_latency_ms": 300,
        },
        "loan_application_status": {
            "update_type": "Loan Application Status",
            "trigger_event": "Status Changed",
            "affected_components": [
                "Application List",
                "Farmer Dashboard",
                "Officer Tasks",
            ],
            "update_latency_ms": 320,
            "expected_latency_ms": 500,
        },
        "system_notifications": {
            "update_type": "System Notifications",
            "trigger_event": "New Notification",
            "affected_components": ["Notification Panel", "Mobile App", "Email Queue"],
            "update_latency_ms": 150,
            "expected_latency_ms": 200,
        },
    }


# ============================================================================
# OBSERVABILITY FIXTURES - Centralized Mock Agent and Configuration
# ============================================================================


@pytest.fixture
def mock_agent_config():
    """Mock AgentConfig for observability webhook server tests"""
    config = MagicMock()
    config.prometheus_url = "http://localhost:9090"
    config.jaeger_url = "http://localhost:16686"
    config.loki_url = "http://localhost:3100"
    config.slack_bot_token = "xoxb-test-token"
    config.slack_channels = {"incidents": "#incidents"}
    config.pagerduty_token = "test-pd-token"
    config.pagerduty_integration_keys = {"incidents": "test-key"}
    config.reports_dir = "/tmp/reports"
    config.analysis_window_minutes = 30
    config.confidence_threshold = 0.3
    return config


@pytest.fixture
def mock_agent(mock_agent_config):
    """Centralized mock AIIncidentAgent with AsyncMock for proper async handling"""
    agent = AsyncMock()
    agent.config = mock_agent_config
    agent.slack_bot = AsyncMock()

    # Mock async analyze_incident method with realistic return values
    async def mock_analyze_incident(*_args, **_kwargs):
        return {
            "insight": {
                "business_impact": "high",
                "confidence_score": 0.87,
            },
            "root_causes": [{"type": "database_issues", "confidence": 0.85}],
        }

    agent.analyze_incident = AsyncMock(side_effect=mock_analyze_incident)
    agent.slack_bot.handle_command = AsyncMock(return_value="Command processed")
    agent.slack_bot.handle_interactive_message = AsyncMock(
        return_value="Interaction processed"
    )

    # Add process method for health checks with realistic return values
    agent.process = AsyncMock(return_value={"status": "ok", "uptime": 123.45})

    return agent


@pytest.fixture
def sample_alert_payload():
    """Sample Alertmanager webhook payload for testing"""
    return {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighLatency",
                    "severity": "critical",
                    "service": "api-gateway",
                },
                "annotations": {
                    "description": "API latency exceeded threshold",
                    "summary": "High request latency detected",
                },
            }
        ],
        "groupLabels": {"alertname": "HighLatency"},
        "commonLabels": {"severity": "critical"},
        "commonAnnotations": {"summary": "High latency"},
        "externalURL": "http://alertmanager:9093",
        "version": "4",
        "groupKey": "test-group-key",
    }
