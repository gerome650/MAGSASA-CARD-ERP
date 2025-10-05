#!/usr/bin/env python3
"""
Sample Workflow for AI Incident Insight Agent

Demonstrates the complete incident analysis workflow from alert to postmortem.
This script shows how to use the agent in a real-world scenario.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from main import AgentConfig, AIIncidentAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def simulate_incident_workflow():
    """Simulate a complete incident workflow"""

    print("🤖 AI Incident Insight Agent - Sample Workflow")
    print("=" * 60)

    # Step 1: Configuration
    print("\n📋 Step 1: Setting up configuration...")

    config = AgentConfig(
        prometheus_url="http://localhost:9090",
        jaeger_url="http://localhost:16686",
        loki_url="http://localhost:3100",
        reports_dir="/tmp/ai_agent_reports",
        analysis_window_minutes=30,
        confidence_threshold=0.3,
    )

    print("✅ Configuration loaded")

    # Step 2: Simulate Alert
    print("\n🚨 Step 2: Simulating incident alert...")

    incident_time = datetime.now()
    alert_payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighLatency",
                    "service": "magsasa-card-erp",
                    "severity": "critical",
                    "deployment": "v1.4.2",
                    "endpoint": "/api/orders",
                    "method": "POST",
                },
                "annotations": {
                    "summary": "High latency detected after deployment",
                    "description": "p95 latency increased by 240% following deployment v1.4.2. Error rates spiked to 7% due to database query timeouts.",
                },
                "startsAt": incident_time.isoformat(),
                "endsAt": "0001-01-01T00:00:00Z",
            }
        ],
        "groupLabels": {"alertname": "HighLatency"},
        "commonLabels": {"service": "magsasa-card-erp"},
        "commonAnnotations": {"summary": "High latency detected after deployment"},
        "externalURL": "http://localhost:9093",
        "version": "4",
        "groupKey": "{}:{}",
    }

    incident_id = f"INC-{incident_time.strftime('%Y-%m-%d-%H%M%S')}"
    print(f"✅ Alert simulated for incident: {incident_id}")

    # Step 3: Initialize Agent
    print("\n🔧 Step 3: Initializing AI Incident Agent...")

    agent = AIIncidentAgent(config)
    print("✅ Agent initialized successfully")

    # Step 4: Run Analysis
    print("\n🔍 Step 4: Running incident analysis...")

    try:
        results = await agent.analyze_incident(
            incident_id=incident_id,
            alert_payload=alert_payload,
            resolution_notes="Incident resolved by rolling back deployment v1.4.2 to v1.4.1. Database connection pool was also restarted to clear any connection issues.",
            engineer_notes="The team responded quickly to the incident. Need to implement automated query regression testing in CI/CD pipeline to prevent similar issues. Also consider adding canary deployments for future releases.",
        )

        print("✅ Incident analysis completed successfully")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return

    # Step 5: Display Results
    print("\n📊 Step 5: Analysis Results Summary")
    print("-" * 40)

    insight = results["insight"]
    print(f"🎯 Business Impact: {insight['business_impact'].title()}")
    print(f"👥 Users Affected: {insight['users_affected']:,}")
    print(f"⏱️  Duration: {insight['duration_minutes']} minutes")
    print(f"🎲 Confidence Score: {insight['confidence_score']:.1%}")

    print(f"\n🔍 Root Causes Identified: {len(results['root_causes'])}")
    for i, cause in enumerate(results["root_causes"], 1):
        print(
            f"   {i}. {cause['type'].replace('_', ' ').title()} ({cause['confidence']:.1%})"
        )
        print(f"      {cause['description']}")

    print(f"\n⚡ Remediation Actions: {len(results['remediation_actions'])}")
    immediate_actions = [
        a for a in results["remediation_actions"] if a["priority"] == "immediate"
    ]
    for action in immediate_actions[:3]:  # Show top 3 immediate actions
        print(f"   • {action['title']} ({action['duration_minutes']} min)")

    # Step 6: Show Generated Reports
    print("\n📄 Step 6: Generated Reports")
    print("-" * 40)

    print(f"📊 Reports Generated: {results['reports_generated']}")
    print(f"📝 Postmortem: {results['postmortem']['file_path']}")
    print(f"📋 Postmortem Sections: {results['postmortem']['sections_count']}")

    # Step 7: Show Timeline
    print("\n📅 Step 7: Incident Timeline")
    print("-" * 40)

    timeline = insight["timeline"]
    for event in timeline[:5]:  # Show first 5 events
        time_str = datetime.fromisoformat(event["timestamp"]).strftime("%H:%M UTC")
        print(f"   {time_str} - {event['description']}")

    if len(timeline) > 5:
        print(f"   ... and {len(timeline) - 5} more events")

    # Step 8: Show Notification Results
    print("\n📢 Step 8: Notification Results")
    print("-" * 40)

    notifications = results["notification_results"]
    for channel, result in notifications.items():
        if "success" in result:
            print(
                f"   {channel.title()}: {result['success']}/{result.get('total', 1)} notifications sent"
            )
        elif "error" in result:
            print(f"   {channel.title()}: ❌ Error - {result['error']}")

    # Step 9: Save Results
    print("\n💾 Step 9: Saving Results")
    print("-" * 40)

    results_file = f"/tmp/incident_analysis_{incident_id}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"✅ Results saved to: {results_file}")

    # Step 10: Show Postmortem Preview
    print("\n📝 Step 10: Postmortem Preview")
    print("-" * 40)

    postmortem_path = results["postmortem"]["file_path"]
    if Path(postmortem_path).exists():
        with open(postmortem_path) as f:
            postmortem_content = f.read()

        # Show first few lines of postmortem
        lines = postmortem_content.split("\n")[:10]
        for line in lines:
            if line.strip():
                print(f"   {line}")

        print(f"   ... (full postmortem available at {postmortem_path})")
    else:
        print("   Postmortem file not found")

    # Summary
    print("\n🎉 Workflow Summary")
    print("=" * 60)
    print(f"✅ Incident analyzed: {incident_id}")
    print(f"✅ Root causes identified: {len(results['root_causes'])}")
    print(f"✅ Remediation actions: {len(results['remediation_actions'])}")
    print(f"✅ Reports generated: {results['reports_generated']}")
    print(f"✅ Postmortem created: {results['postmortem']['sections_count']} sections")
    print(f"✅ Confidence score: {insight['confidence_score']:.1%}")

    print("\n📁 Generated Files:")
    print(f"   • Analysis Results: {results_file}")
    print(f"   • Postmortem Report: {postmortem_path}")

    print("\n🚀 Next Steps:")
    print("   1. Review the postmortem report")
    print("   2. Implement recommended action items")
    print("   3. Update monitoring and alerting")
    print("   4. Conduct post-incident review meeting")

    print("\n🤖 AI Incident Insight Agent workflow completed successfully!")


async def simulate_multiple_incidents():
    """Simulate analysis of multiple incident types"""

    print("\n🔄 Running Multiple Incident Scenarios")
    print("=" * 60)

    # Configuration
    config = AgentConfig(
        prometheus_url="http://localhost:9090",
        jaeger_url="http://localhost:16686",
        loki_url="http://localhost:3100",
        reports_dir="/tmp/ai_agent_reports",
    )

    # Different incident scenarios
    scenarios = [
        {
            "name": "Database Issues",
            "alert": {
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "DatabaseHighLatency",
                            "service": "magsasa-card-erp",
                            "severity": "critical",
                        },
                        "annotations": {
                            "summary": "Database connection timeout",
                            "description": "Database queries timing out, causing 7% error rate",
                        },
                        "startsAt": datetime.now().isoformat(),
                    }
                ]
            },
        },
        {
            "name": "Infrastructure Degradation",
            "alert": {
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "NodeMemoryPressure",
                            "service": "magsasa-card-erp",
                            "severity": "warning",
                        },
                        "annotations": {
                            "summary": "Node memory pressure",
                            "description": "Kubernetes node experiencing memory pressure",
                        },
                        "startsAt": datetime.now().isoformat(),
                    }
                ]
            },
        },
        {
            "name": "Dependency Failure",
            "alert": {
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "ExternalServiceDown",
                            "service": "magsasa-card-erp",
                            "severity": "critical",
                            "dependency": "payment-service",
                        },
                        "annotations": {
                            "summary": "External payment service unavailable",
                            "description": "Payment service returning 503 errors",
                        },
                        "startsAt": datetime.now().isoformat(),
                    }
                ]
            },
        },
    ]

    agent = AIIncidentAgent(config)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['name']}")
        print("-" * 40)

        incident_id = f"SCENARIO-{i}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            results = await agent.analyze_incident(
                incident_id=incident_id,
                alert_payload=scenario["alert"],
                resolution_notes=f"Scenario {i} resolution notes",
                engineer_notes=f"Scenario {i} engineer notes",
            )

            insight = results["insight"]
            print(f"   ✅ Analyzed: {incident_id}")
            print(f"   🎯 Impact: {insight['business_impact'].title()}")
            print(f"   🔍 Root Causes: {len(results['root_causes'])}")
            print(f"   ⚡ Actions: {len(results['remediation_actions'])}")
            print(f"   🎲 Confidence: {insight['confidence_score']:.1%}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n✅ Multiple incident scenarios completed!")


async def main():
    """Main function to run the sample workflow"""
    try:
        # Run main workflow
        await simulate_incident_workflow()

        # Run multiple scenarios
        await simulate_multiple_incidents()

    except KeyboardInterrupt:
        print("\n⏹️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error in sample workflow")


if __name__ == "__main__":
    asyncio.run(main())
