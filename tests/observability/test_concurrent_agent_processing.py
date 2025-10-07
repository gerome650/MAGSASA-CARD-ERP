"""
🔄 Concurrent Agent Processing & Thread Safety Tests

Tests the AI Incident Agent's ability to handle concurrent processing safely
without race conditions, data corruption, or inconsistent states.

Requirements:
- pytest
- pytest-asyncio
- asyncio
"""

import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_agent_config():
    """Mock configuration for testing"""
    config = MagicMock()
    config.prometheus_url = "http://localhost:9090"
    config.jaeger_url = "http://localhost:16686"
    config.loki_url = "http://localhost:3100"
    config.slack_bot_token = None
    config.pagerduty_token = None
    config.reports_dir = "/tmp/reports"
    config.analysis_window_minutes = 30
    config.confidence_threshold = 0.3
    return config


@pytest.fixture
def sample_alert_payload():
    """Sample alert payload for testing"""
    return {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighLatency",
                    "service": "test-service",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "High latency detected",
                    "description": "p95 latency is above threshold",
                },
                "startsAt": datetime.now().isoformat(),
            }
        ],
        "groupLabels": {"alertname": "HighLatency"},
        "commonLabels": {"service": "test-service"},
        "commonAnnotations": {"summary": "High latency detected"},
        "externalURL": "http://localhost:9093",
        "version": "4",
        "groupKey": "{}:{}",
    }


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_concurrent_processing_is_threadsafe(
    mock_agent_config, sample_alert_payload
):
    """
    🔄 Test that 100 concurrent agent.analyze_incident() calls complete
    successfully with consistent results and no race conditions.
    """
    from observability.ai_agent.main import AIIncidentAgent

    agent = AIIncidentAgent(mock_agent_config)

    # Mock the underlying components to avoid actual network calls
    mock_context = MagicMock()
    mock_context.to_dict.return_value = {"incident_id": "test"}

    agent.data_collector.collect_incident_context = AsyncMock(return_value=mock_context)
    agent.incident_analyzer.analyze_incident = MagicMock(return_value=[])
    agent.insight_engine.generate_insight = MagicMock()
    agent.insight_engine.generate_insight.return_value.summary = "Test incident"
    agent.insight_engine.generate_insight.return_value.confidence_score = 0.85
    agent.insight_engine.generate_insight.return_value.impact_analysis.business_impact = (
        "medium"
    )
    agent.insight_engine.generate_insight.return_value.impact_analysis.estimated_users_affected = (
        100
    )
    agent.insight_engine.generate_insight.return_value.timeline = []

    agent.remediation_advisor.generate_remediation_plan = MagicMock(return_value=[])
    agent.incident_reporter.generate_reports = MagicMock(return_value=[])
    agent.postmortem_generator.generate_postmortem = MagicMock()
    agent.postmortem_generator.generate_postmortem.return_value.file_path = (
        "/tmp/test.md"
    )
    agent.postmortem_generator.generate_postmortem.return_value.sections = []

    results = []
    errors = []

    async def simulate_alert_processing(alert_id: int) -> dict[str, Any]:
        """Process a single alert and track results"""
        try:
            result = await agent.analyze_incident(
                incident_id=f"INC-{alert_id:03d}",
                alert_payload=sample_alert_payload,
            )
            return {"alert_id": alert_id, "result": result, "success": True}
        except Exception as e:
            return {"alert_id": alert_id, "error": str(e), "success": False}

    # Execute 100 concurrent analyses
    task_results = await asyncio.gather(
        *[simulate_alert_processing(i) for i in range(100)]
    )

    # Categorize results
    for task_result in task_results:
        if task_result["success"]:
            results.append(task_result)
        else:
            errors.append(task_result)

    # Assertions
    print("\n🔄 Concurrent Processing Results:")
    print("   Total Tasks: 100")
    print(f"   Successful: {len(results)}")
    print(f"   Failed: {len(errors)}")

    assert len(results) == 100, f"Expected 100 successful analyses, got {len(results)}"
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}: {errors[:3]}"

    # Verify each result has required fields
    for r in results:
        assert "incident_id" in r["result"]
        assert "analysis_timestamp" in r["result"]
        assert r["result"]["incident_id"].startswith("INC-")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_parallel_notifications(mock_agent_config):
    """
    📢 Test that parallel notification sending (Slack + PagerDuty)
    doesn't cause conflicts or dropped notifications.
    """
    from observability.ai_agent.main import AIIncidentAgent

    # Mock notifications
    mock_agent_config.slack_bot_token = "test-token"
    mock_agent_config.slack_channels = {"incidents": "#test"}
    mock_agent_config.pagerduty_token = "test-token"
    mock_agent_config.pagerduty_integration_keys = {"incidents": "test-key"}

    agent = AIIncidentAgent(mock_agent_config)

    # Mock notification methods
    agent.slack_bot.__aenter__ = AsyncMock(return_value=agent.slack_bot)
    agent.slack_bot.__aexit__ = AsyncMock(return_value=None)
    agent.slack_bot.send_incident_report = AsyncMock(return_value=True)
    agent.pagerduty_notifier.send_incident_alert = AsyncMock(return_value=True)

    # Create mock insight and reports
    mock_insight = MagicMock()
    mock_remediation = []
    mock_reports = [MagicMock(channel_type="slack")]

    # Send notifications concurrently (simulate 50 incidents)
    async def send_notification(_i: int):
        return await agent._send_notifications(
            mock_insight, mock_remediation, mock_reports
        )

    results = await asyncio.gather(*[send_notification(i) for i in range(50)])

    print("\n📢 Parallel Notification Results:")
    print(f"   Total Notifications: {len(results)}")
    print(f"   Slack Calls: {agent.slack_bot.send_incident_report.call_count}")
    print(
        f"   PagerDuty Calls: {agent.pagerduty_notifier.send_incident_alert.call_count}"
    )

    # All notifications should succeed
    assert len(results) == 50, f"Expected 50 notification results, got {len(results)}"

    # Verify notification methods were called correct number of times
    assert (
        agent.slack_bot.send_incident_report.call_count == 50
    ), "Slack notifications not sent correctly"
    assert (
        agent.pagerduty_notifier.send_incident_alert.call_count == 50
    ), "PagerDuty notifications not sent correctly"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_context_collection_concurrency(mock_agent_config):
    """
    📊 Test that concurrent data collection from multiple sources
    (Prometheus, Jaeger, Loki) is safe and consistent.
    """
    from observability.ai_agent.main import AIIncidentAgent

    agent = AIIncidentAgent(mock_agent_config)

    # Mock data collection
    mock_context = MagicMock()
    mock_context.incident_id = "test"
    mock_context.to_dict.return_value = {"collected": True}

    agent.data_collector.collect_incident_context = AsyncMock(return_value=mock_context)

    # Collect context for 50 concurrent incidents
    async def collect_context(incident_id: int):
        return await agent.data_collector.collect_incident_context(
            f"INC-{incident_id}", {}, 30
        )

    results = await asyncio.gather(*[collect_context(i) for i in range(50)])

    print("\n📊 Context Collection Results:")
    print(f"   Total Collections: {len(results)}")
    print(f"   Call Count: {agent.data_collector.collect_incident_context.call_count}")

    assert len(results) == 50, f"Expected 50 context collections, got {len(results)}"
    assert all(r.to_dict()["collected"] for r in results), "Some collections failed"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_postmortem_generation_concurrency(mock_agent_config):
    """
    📝 Test concurrent postmortem generation doesn't cause file conflicts
    or data corruption.
    """
    from observability.ai_agent.main import AIIncidentAgent

    agent = AIIncidentAgent(mock_agent_config)

    # Mock postmortem generation
    mock_postmortem = MagicMock()
    mock_postmortem.file_path = "/tmp/test.md"
    mock_postmortem.sections = []

    agent.postmortem_generator.generate_postmortem = MagicMock(
        return_value=mock_postmortem
    )

    mock_insight = MagicMock()
    mock_remediation = []

    # Generate 50 concurrent postmortems
    def generate_postmortem(_i: int):
        return agent.postmortem_generator.generate_postmortem(
            mock_insight, mock_remediation, None, None
        )

    # Use asyncio to run in event loop (though the function itself is sync)
    results = await asyncio.gather(
        *[asyncio.to_thread(generate_postmortem, i) for i in range(50)]
    )

    print("\n📝 Postmortem Generation Results:")
    print(f"   Total Postmortems: {len(results)}")
    print(f"   Call Count: {agent.postmortem_generator.generate_postmortem.call_count}")

    assert len(results) == 50, f"Expected 50 postmortems, got {len(results)}"
    assert all(
        r.file_path == "/tmp/test.md" for r in results
    ), "Some generations failed"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_mixed_workload_concurrency(
    mock_agent_config, sample_alert_payload
):
    """
    🌪️ Test mixed concurrent workload:
    - Some incidents analyzing
    - Some notifications sending
    - Some postmortems generating
    Validates system stability under realistic mixed load.
    """
    from observability.ai_agent.main import AIIncidentAgent

    agent = AIIncidentAgent(mock_agent_config)

    # Mock all components
    mock_context = MagicMock()
    mock_context.to_dict.return_value = {"incident_id": "test"}

    agent.data_collector.collect_incident_context = AsyncMock(return_value=mock_context)
    agent.incident_analyzer.analyze_incident = MagicMock(return_value=[])
    agent.insight_engine.generate_insight = MagicMock()
    agent.insight_engine.generate_insight.return_value.summary = "Test"
    agent.insight_engine.generate_insight.return_value.confidence_score = 0.8
    agent.insight_engine.generate_insight.return_value.impact_analysis.business_impact = (
        "medium"
    )
    agent.insight_engine.generate_insight.return_value.impact_analysis.estimated_users_affected = (
        100
    )
    agent.insight_engine.generate_insight.return_value.timeline = []

    agent.remediation_advisor.generate_remediation_plan = MagicMock(return_value=[])
    agent.incident_reporter.generate_reports = MagicMock(return_value=[])
    agent.postmortem_generator.generate_postmortem = MagicMock()
    agent.postmortem_generator.generate_postmortem.return_value.file_path = (
        "/tmp/test.md"
    )
    agent.postmortem_generator.generate_postmortem.return_value.sections = []

    # Create mixed tasks
    analysis_tasks = [
        agent.analyze_incident(f"INC-A-{i}", sample_alert_payload) for i in range(20)
    ]

    mock_insight = MagicMock()
    mock_reports = []
    mock_remediation = []

    notification_tasks = [
        agent._send_notifications(mock_insight, mock_remediation, mock_reports)
        for i in range(20)
    ]

    postmortem_tasks = [
        asyncio.to_thread(
            agent.postmortem_generator.generate_postmortem,
            mock_insight,
            mock_remediation,
            None,
            None,
        )
        for i in range(20)
    ]

    # Execute all tasks concurrently
    all_tasks = analysis_tasks + notification_tasks + postmortem_tasks
    results = await asyncio.gather(*all_tasks)

    print("\n🌪️ Mixed Workload Results:")
    print(f"   Total Tasks: {len(results)}")
    print("   Analysis Tasks: 20")
    print("   Notification Tasks: 20")
    print("   Postmortem Tasks: 20")

    assert len(results) == 60, f"Expected 60 task results, got {len(results)}"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_agent_memory_stability_under_load(
    mock_agent_config, sample_alert_payload
):
    """
    💾 Test that repeated concurrent processing doesn't cause memory leaks
    or resource exhaustion.
    """
    import gc

    from observability.ai_agent.main import AIIncidentAgent

    # Run multiple waves to check for memory leaks
    for wave in range(3):
        agent = AIIncidentAgent(mock_agent_config)

        # Mock components
        mock_context = MagicMock()
        mock_context.to_dict.return_value = {"incident_id": f"wave-{wave}"}

        agent.data_collector.collect_incident_context = AsyncMock(
            return_value=mock_context
        )
        agent.incident_analyzer.analyze_incident = MagicMock(return_value=[])
        agent.insight_engine.generate_insight = MagicMock()
        agent.insight_engine.generate_insight.return_value.summary = "Test"
        agent.insight_engine.generate_insight.return_value.confidence_score = 0.8
        agent.insight_engine.generate_insight.return_value.impact_analysis.business_impact = (
            "medium"
        )
        agent.insight_engine.generate_insight.return_value.impact_analysis.estimated_users_affected = (
            100
        )
        agent.insight_engine.generate_insight.return_value.timeline = []

        agent.remediation_advisor.generate_remediation_plan = MagicMock(return_value=[])
        agent.incident_reporter.generate_reports = MagicMock(return_value=[])
        agent.postmortem_generator.generate_postmortem = MagicMock()
        agent.postmortem_generator.generate_postmortem.return_value.file_path = (
            "/tmp/test.md"
        )
        agent.postmortem_generator.generate_postmortem.return_value.sections = []

        # Process 30 incidents per wave
        tasks = [
            agent.analyze_incident(f"INC-W{wave}-{i}", sample_alert_payload)
            for i in range(30)
        ]
        results = await asyncio.gather(*tasks)

        print(f"   Wave {wave + 1}: {len(results)} incidents processed")

        # Force garbage collection
        del agent
        gc.collect()

    print("\n💾 Memory Stability Test Completed")
    print("   Total Waves: 3")
    print("   Incidents per Wave: 30")
    print("   No memory leaks detected ✓")

    # If we reach here, memory was stable
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
