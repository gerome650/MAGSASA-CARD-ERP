"""
Test Workflow for AI Incident Insight Agent

Provides test scenarios and validation scripts to verify the agent functionality.
Includes synthetic incident generation and end-to-end testing.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .data_collector import IncidentContext
from .main import AgentConfig, AIIncidentAgent

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Represents a test scenario for incident analysis"""

    name: str
    description: str
    alert_payload: dict[str, Any]
    expected_root_causes: list[str]
    expected_impact: str
    expected_actions: list[str]


class IncidentAgentTester:
    """Test suite for the AI Incident Insight Agent"""

    def __init__(self, config: AgentConfig):
        """Initialize the tester with agent configuration"""
        self.config = config
        self.agent = AIIncidentAgent(config)
        self.test_scenarios = self._init_test_scenarios()

    def _init_test_scenarios(self) -> list[TestScenario]:
        """Initialize test scenarios"""
        return [
            self._create_deployment_regression_scenario(),
            self._create_database_issues_scenario(),
            self._create_infrastructure_degradation_scenario(),
            self._create_dependency_failure_scenario(),
            self._create_resource_exhaustion_scenario(),
        ]

    def _create_deployment_regression_scenario(self) -> TestScenario:
        """Create test scenario for deployment regression"""
        return TestScenario(
            name="deployment_regression",
            description="Test deployment regression detection and remediation",
            alert_payload={
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "HighLatency",
                            "service": "magsasa-card-erp",
                            "severity": "critical",
                            "deployment": "v1.4.2",
                        },
                        "annotations": {
                            "summary": "High latency detected after deployment",
                            "description": "p95 latency increased by 240% following deployment v1.4.2",
                        },
                        "startsAt": datetime.now().isoformat(),
                        "endsAt": "0001-01-01T00:00:00Z",
                    }
                ],
                "groupLabels": {"alertname": "HighLatency"},
                "commonLabels": {"service": "magsasa-card-erp"},
                "commonAnnotations": {"summary": "High latency detected"},
                "externalURL": "http://localhost:9093",
                "version": "4",
                "groupKey": "{}:{}",
            },
            expected_root_causes=["deployment_regression"],
            expected_impact="high",
            expected_actions=["rollback", "investigation"],
        )

    def _create_database_issues_scenario(self) -> TestScenario:
        """Create test scenario for database issues"""
        return TestScenario(
            name="database_issues",
            description="Test database performance issue detection",
            alert_payload={
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "DatabaseHighLatency",
                            "service": "magsasa-card-erp",
                            "severity": "critical",
                        },
                        "annotations": {
                            "summary": "Database query timeout",
                            "description": "Database connection timeouts causing 7% error rate",
                        },
                        "startsAt": datetime.now().isoformat(),
                        "endsAt": "0001-01-01T00:00:00Z",
                    }
                ],
                "groupLabels": {"alertname": "DatabaseHighLatency"},
                "commonLabels": {"service": "magsasa-card-erp"},
                "commonAnnotations": {"summary": "Database query timeout"},
                "externalURL": "http://localhost:9093",
                "version": "4",
                "groupKey": "{}:{}",
            },
            expected_root_causes=["database_issues"],
            expected_impact="critical",
            expected_actions=["health_check", "query_optimization"],
        )

    def _create_infrastructure_degradation_scenario(self) -> TestScenario:
        """Create test scenario for infrastructure issues"""
        return TestScenario(
            name="infrastructure_degradation",
            description="Test infrastructure degradation detection",
            alert_payload={
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "NodeMemoryPressure",
                            "service": "magsasa-card-erp",
                            "severity": "warning",
                        },
                        "annotations": {
                            "summary": "Node memory pressure detected",
                            "description": "Kubernetes node experiencing memory pressure",
                        },
                        "startsAt": datetime.now().isoformat(),
                        "endsAt": "0001-01-01T00:00:00Z",
                    }
                ],
                "groupLabels": {"alertname": "NodeMemoryPressure"},
                "commonLabels": {"service": "magsasa-card-erp"},
                "commonAnnotations": {"summary": "Node memory pressure detected"},
                "externalURL": "http://localhost:9093",
                "version": "4",
                "groupKey": "{}:{}",
            },
            expected_root_causes=["infrastructure_degradation"],
            expected_impact="medium",
            expected_actions=["restart", "scale"],
        )

    def _create_dependency_failure_scenario(self) -> TestScenario:
        """Create test scenario for dependency failures"""
        return TestScenario(
            name="dependency_failure",
            description="Test external dependency failure detection",
            alert_payload={
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
                        "endsAt": "0001-01-01T00:00:00Z",
                    }
                ],
                "groupLabels": {"alertname": "ExternalServiceDown"},
                "commonLabels": {"service": "magsasa-card-erp"},
                "commonAnnotations": {
                    "summary": "External payment service unavailable"
                },
                "externalURL": "http://localhost:9093",
                "version": "4",
                "groupKey": "{}:{}",
            },
            expected_root_causes=["dependency_failure"],
            expected_impact="high",
            expected_actions=["circuit_breaker", "retry_logic"],
        )

    def _create_resource_exhaustion_scenario(self) -> TestScenario:
        """Create test scenario for resource exhaustion"""
        return TestScenario(
            name="resource_exhaustion",
            description="Test resource exhaustion detection",
            alert_payload={
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "OutOfMemory",
                            "service": "magsasa-card-erp",
                            "severity": "critical",
                        },
                        "annotations": {
                            "summary": "Application out of memory",
                            "description": "Java heap space exhaustion detected",
                        },
                        "startsAt": datetime.now().isoformat(),
                        "endsAt": "0001-01-01T00:00:00Z",
                    }
                ],
                "groupLabels": {"alertname": "OutOfMemory"},
                "commonLabels": {"service": "magsasa-card-erp"},
                "commonAnnotations": {"summary": "Application out of memory"},
                "externalURL": "http://localhost:9093",
                "version": "4",
                "groupKey": "{}:{}",
            },
            expected_root_causes=["resource_exhaustion"],
            expected_impact="critical",
            expected_actions=["resource_increase", "leak_investigation"],
        )

    async def run_test_suite(self) -> dict[str, Any]:
        """Run the complete test suite"""
        logger.info("Starting AI Incident Agent test suite")

        results = {
            "test_suite_timestamp": datetime.now().isoformat(),
            "total_scenarios": len(self.test_scenarios),
            "passed_scenarios": 0,
            "failed_scenarios": 0,
            "scenario_results": [],
        }

        for scenario in self.test_scenarios:
            logger.info(f"Running test scenario: {scenario.name}")

            try:
                scenario_result = await self._run_scenario(scenario)
                results["scenario_results"].append(scenario_result)

                if scenario_result["passed"]:
                    results["passed_scenarios"] += 1
                else:
                    results["failed_scenarios"] += 1

            except Exception as e:
                logger.error(f"Error running scenario {scenario.name}: {e}")
                results["scenario_results"].append(
                    {"scenario_name": scenario.name, "passed": False, "error": str(e)}
                )
                results["failed_scenarios"] += 1

        # Calculate success rate
        results["success_rate"] = (
            results["passed_scenarios"] / results["total_scenarios"]
            if results["total_scenarios"] > 0
            else 0
        )

        logger.info(
            f"Test suite completed. Success rate: {results['success_rate']:.1%}"
        )
        return results

    async def _run_scenario(self, scenario: TestScenario) -> dict[str, Any]:
        """Run a single test scenario"""
        incident_id = f"TEST-{scenario.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            # Run incident analysis
            results = await self.agent.analyze_incident(
                incident_id=incident_id,
                alert_payload=scenario.alert_payload,
                resolution_notes="Test scenario resolution",
                engineer_notes="Test scenario engineer notes",
            )

            # Validate results
            validation = self._validate_scenario_results(scenario, results)

            return {
                "scenario_name": scenario.name,
                "incident_id": incident_id,
                "passed": validation["passed"],
                "validation_results": validation,
                "analysis_results": {
                    "confidence_score": results["insight"]["confidence_score"],
                    "business_impact": results["insight"]["business_impact"],
                    "root_causes_found": len(results["root_causes"]),
                    "remediation_actions": len(results["remediation_actions"]),
                },
            }

        except Exception as e:
            logger.error(f"Error in scenario {scenario.name}: {e}")
            return {
                "scenario_name": scenario.name,
                "incident_id": incident_id,
                "passed": False,
                "error": str(e),
            }

    def _validate_scenario_results(
        self, scenario: TestScenario, results: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate that scenario results match expectations"""
        validation = {"passed": True, "checks": {}}

        # Check root causes
        found_root_causes = [cause["type"] for cause in results["root_causes"]]
        expected_causes_found = any(
            expected in found_root_causes for expected in scenario.expected_root_causes
        )

        validation["checks"]["root_causes"] = {
            "passed": expected_causes_found,
            "expected": scenario.expected_root_causes,
            "found": found_root_causes,
        }

        if not expected_causes_found:
            validation["passed"] = False

        # Check business impact
        actual_impact = results["insight"]["business_impact"].lower()
        expected_impact = scenario.expected_impact.lower()
        impact_match = actual_impact == expected_impact

        validation["checks"]["business_impact"] = {
            "passed": impact_match,
            "expected": expected_impact,
            "actual": actual_impact,
        }

        if not impact_match:
            validation["passed"] = False

        # Check remediation actions
        action_types = [
            action.get("action_type", "") for action in results["remediation_actions"]
        ]
        expected_actions_found = any(
            expected in action_types for expected in scenario.expected_actions
        )

        validation["checks"]["remediation_actions"] = {
            "passed": expected_actions_found,
            "expected": scenario.expected_actions,
            "found": action_types,
        }

        if not expected_actions_found:
            validation["passed"] = False

        # Check confidence score
        confidence = results["insight"]["confidence_score"]
        confidence_acceptable = confidence > 0.3

        validation["checks"]["confidence_score"] = {
            "passed": confidence_acceptable,
            "actual": confidence,
            "threshold": 0.3,
        }

        if not confidence_acceptable:
            validation["passed"] = False

        return validation

    async def run_integration_test(self) -> dict[str, Any]:
        """Run integration test with real components"""
        logger.info("Running integration test")

        # Test data collector
        collector_test = await self._test_data_collector()

        # Test incident analyzer
        analyzer_test = await self._test_incident_analyzer()

        # Test insight engine
        insight_test = await self._test_insight_engine()

        # Test remediation advisor
        remediation_test = await self._test_remediation_advisor()

        # Test postmortem generator
        postmortem_test = await self._test_postmortem_generator()

        return {
            "integration_test_timestamp": datetime.now().isoformat(),
            "data_collector": collector_test,
            "incident_analyzer": analyzer_test,
            "insight_engine": insight_test,
            "remediation_advisor": remediation_test,
            "postmortem_generator": postmortem_test,
        }

    async def _test_data_collector(self) -> dict[str, Any]:
        """Test data collector functionality"""
        try:
            # Create test alert payload
            test_alert = {
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {"alertname": "TestAlert"},
                        "startsAt": datetime.now().isoformat(),
                    }
                ]
            }

            # Test context collection
            context = await self.agent.data_collector.collect_incident_context(
                "TEST-001", test_alert, 30
            )

            return {
                "passed": True,
                "context_collected": True,
                "metric_anomalies": len(context.metric_anomalies),
                "trace_outliers": len(context.trace_outliers),
                "log_signatures": len(context.log_signatures),
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _test_incident_analyzer(self) -> dict[str, Any]:
        """Test incident analyzer functionality"""
        try:
            # Create test context
            test_context = IncidentContext(
                incident_id="TEST-001",
                timestamp=datetime.now(),
                duration_minutes=30,
                metric_anomalies=[],
                trace_outliers=[],
                log_signatures=[],
                deployment_events=[],
                system_events=[],
                alert_payload={},
            )

            # Test analysis
            root_causes = self.agent.incident_analyzer.analyze_incident(test_context)

            return {
                "passed": True,
                "root_causes_found": len(root_causes),
                "analyzer_functional": True,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _test_insight_engine(self) -> dict[str, Any]:
        """Test insight engine functionality"""
        try:
            # Create test insight
            test_context = IncidentContext(
                incident_id="TEST-001",
                timestamp=datetime.now(),
                duration_minutes=30,
                metric_anomalies=[],
                trace_outliers=[],
                log_signatures=[],
                deployment_events=[],
                system_events=[],
                alert_payload={},
            )

            # Test insight generation
            root_causes = self.agent.incident_analyzer.analyze_incident(test_context)
            insight = self.agent.insight_engine.generate_insight(
                test_context, root_causes
            )

            return {
                "passed": True,
                "insight_generated": True,
                "confidence_score": insight.confidence_score,
                "timeline_events": len(insight.timeline),
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _test_remediation_advisor(self) -> dict[str, Any]:
        """Test remediation advisor functionality"""
        try:
            # Create test insight
            test_context = IncidentContext(
                incident_id="TEST-001",
                timestamp=datetime.now(),
                duration_minutes=30,
                metric_anomalies=[],
                trace_outliers=[],
                log_signatures=[],
                deployment_events=[],
                system_events=[],
                alert_payload={},
            )

            root_causes = self.agent.incident_analyzer.analyze_incident(test_context)
            insight = self.agent.insight_engine.generate_insight(
                test_context, root_causes
            )

            # Test remediation generation
            actions = self.agent.remediation_advisor.generate_remediation_plan(insight)

            return {
                "passed": True,
                "actions_generated": len(actions),
                "advisor_functional": True,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}

    async def _test_postmortem_generator(self) -> dict[str, Any]:
        """Test postmortem generator functionality"""
        try:
            # Create test insight
            test_context = IncidentContext(
                incident_id="TEST-001",
                timestamp=datetime.now(),
                duration_minutes=30,
                metric_anomalies=[],
                trace_outliers=[],
                log_signatures=[],
                deployment_events=[],
                system_events=[],
                alert_payload={},
            )

            root_causes = self.agent.incident_analyzer.analyze_incident(test_context)
            insight = self.agent.insight_engine.generate_insight(
                test_context, root_causes
            )
            actions = self.agent.remediation_advisor.generate_remediation_plan(insight)

            # Test postmortem generation
            postmortem = self.agent.postmortem_generator.generate_postmortem(
                insight, actions, "Test resolution notes", "Test engineer notes"
            )

            return {
                "passed": True,
                "postmortem_generated": True,
                "sections_count": len(postmortem.sections),
                "file_created": True,
            }

        except Exception as e:
            return {"passed": False, "error": str(e)}


# CLI interface for testing
async def run_tests():
    """Run the test suite from command line"""

    # Create test configuration
    config = AgentConfig(
        prometheus_url="http://localhost:9090",
        jaeger_url="http://localhost:16686",
        loki_url="http://localhost:3100",
        reports_dir="/tmp/ai_agent_reports",  # Use temp directory for testing
    )

    # Initialize tester
    tester = IncidentAgentTester(config)

    print("🧪 AI Incident Agent Test Suite")
    print("=" * 50)

    # Run test scenarios
    print("\n📋 Running test scenarios...")
    scenario_results = await tester.run_test_suite()

    print("\n✅ Test Results:")
    print(f"   Total Scenarios: {scenario_results['total_scenarios']}")
    print(f"   Passed: {scenario_results['passed_scenarios']}")
    print(f"   Failed: {scenario_results['failed_scenarios']}")
    print(f"   Success Rate: {scenario_results['success_rate']:.1%}")

    # Run integration tests
    print("\n🔧 Running integration tests...")
    integration_results = await tester.run_integration_test()

    print("\n✅ Integration Test Results:")
    for component, result in integration_results.items():
        if component != "integration_test_timestamp":
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            print(f"   {component}: {status}")

    # Generate test report
    test_report = {
        "test_suite_results": scenario_results,
        "integration_test_results": integration_results,
        "test_timestamp": datetime.now().isoformat(),
    }

    # Save test report
    report_file = "/tmp/ai_agent_test_report.json"
    with open(report_file, "w") as f:
        json.dump(test_report, f, indent=2)

    print(f"\n📄 Test report saved to: {report_file}")

    return test_report


if __name__ == "__main__":
    asyncio.run(run_tests())
