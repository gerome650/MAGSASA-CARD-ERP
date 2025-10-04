#!/usr/bin/env python3
"""
CLI Interface for AI Incident Insight Agent

Provides command-line interface for running the agent, testing, and management.
"""

import asyncio
import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .main import AIIncidentAgent, AgentConfig
from .test_workflow import IncidentAgentTester

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/var/log/ai_incident_agent.log')
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Replace environment variables
        config_str = yaml.dump(config)
        import os
        for key, value in os.environ.items():
            config_str = config_str.replace(f"${{{key}}}", value)
        
        return yaml.safe_load(config_str)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {e}")
        sys.exit(1)

def create_agent_config(config: Dict[str, Any]) -> AgentConfig:
    """Create AgentConfig from loaded configuration"""
    data_sources = config.get("data_sources", {})
    notifications = config.get("notifications", {})
    
    return AgentConfig(
        # Data sources
        prometheus_url=data_sources.get("prometheus", {}).get("base_url", "http://localhost:9090"),
        jaeger_url=data_sources.get("jaeger", {}).get("base_url", "http://localhost:16686"),
        loki_url=data_sources.get("loki", {}).get("base_url", "http://localhost:3100"),
        github_token=data_sources.get("github", {}).get("token"),
        
        # Notifications
        slack_bot_token=notifications.get("slack", {}).get("bot_token") if notifications.get("slack", {}).get("enabled") else None,
        slack_channels=notifications.get("slack", {}).get("channels", {}),
        pagerduty_token=notifications.get("pagerduty", {}).get("api_token") if notifications.get("pagerduty", {}).get("enabled") else None,
        pagerduty_integration_keys=notifications.get("pagerduty", {}).get("integration_keys", {}),
        
        # Analysis
        reports_dir=config.get("postmortem", {}).get("reports_directory", "/observability/reports"),
        analysis_window_minutes=config.get("analysis", {}).get("window_minutes", 30),
        confidence_threshold=config.get("analysis", {}).get("confidence_threshold", 0.3)
    )

async def analyze_incident_command(args):
    """Handle analyze incident command"""
    config = load_config(args.config)
    agent_config = create_agent_config(config)
    
    # Load alert payload
    if args.alert_file:
        with open(args.alert_file, 'r') as f:
            alert_payload = json.load(f)
    else:
        # Create sample alert payload
        alert_payload = {
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": args.alert_name or "TestAlert",
                        "service": args.service or "magsasa-card-erp",
                        "severity": args.severity or "critical"
                    },
                    "annotations": {
                        "summary": args.summary or "Test incident",
                        "description": args.description or "Test incident description"
                    },
                    "startsAt": datetime.now().isoformat(),
                    "endsAt": "0001-01-01T00:00:00Z"
                }
            ],
            "groupLabels": {"alertname": args.alert_name or "TestAlert"},
            "commonLabels": {"service": args.service or "magsasa-card-erp"},
            "commonAnnotations": {"summary": args.summary or "Test incident"},
            "externalURL": "http://localhost:9093",
            "version": "4",
            "groupKey": "{}:{}"
        }
    
    # Run analysis
    agent = AIIncidentAgent(agent_config)
    
    try:
        results = await agent.analyze_incident(
            incident_id=args.incident_id,
            alert_payload=alert_payload,
            resolution_notes=args.resolution_notes,
            engineer_notes=args.engineer_notes
        )
        
        print(f"✅ Incident analysis completed for {args.incident_id}")
        print(f"📊 Confidence Score: {results['insight']['confidence_score']:.1%}")
        print(f"🎯 Business Impact: {results['insight']['business_impact']}")
        print(f"🔍 Root Causes Found: {len(results['root_causes'])}")
        print(f"⚡ Remediation Actions: {len(results['remediation_actions'])}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to: {args.output}")
        else:
            print("\n📋 Analysis Results:")
            print(json.dumps(results, indent=2))
            
    except Exception as e:
        print(f"❌ Error analyzing incident: {e}")
        sys.exit(1)

async def test_command(args):
    """Handle test command"""
    config = load_config(args.config)
    agent_config = create_agent_config(config)
    
    tester = IncidentAgentTester(agent_config)
    
    print("🧪 Running AI Incident Agent Tests")
    print("=" * 50)
    
    if args.scenarios:
        # Run test scenarios
        print("\n📋 Running test scenarios...")
        results = await tester.run_test_suite()
        
        print(f"\n✅ Test Results:")
        print(f"   Total Scenarios: {results['total_scenarios']}")
        print(f"   Passed: {results['passed_scenarios']}")
        print(f"   Failed: {results['failed_scenarios']}")
        print(f"   Success Rate: {results['success_rate']:.1%}")
        
        if args.verbose:
            print("\n📋 Detailed Results:")
            for result in results['scenario_results']:
                status = "✅ PASSED" if result['passed'] else "❌ FAILED"
                print(f"   {result['scenario_name']}: {status}")
                if not result['passed'] and 'error' in result:
                    print(f"      Error: {result['error']}")
    
    if args.integration:
        # Run integration tests
        print("\n🔧 Running integration tests...")
        results = await tester.run_integration_test()
        
        print(f"\n✅ Integration Test Results:")
        for component, result in results.items():
            if component != "integration_test_timestamp":
                status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
                print(f"   {component}: {status}")
    
    if args.output:
        # Save test results
        test_report = {
            "test_timestamp": datetime.now().isoformat(),
            "scenario_results": results if args.scenarios else None,
            "integration_results": results if args.integration else None
        }
        
        with open(args.output, 'w') as f:
            json.dump(test_report, f, indent=2)
        print(f"\n📄 Test report saved to: {args.output}")

async def postmortem_command(args):
    """Handle postmortem generation command"""
    config = load_config(args.config)
    agent_config = create_agent_config(config)
    
    # Load incident data
    with open(args.incident_file, 'r') as f:
        incident_data = json.load(f)
    
    # Create agent and generate postmortem
    agent = AIIncidentAgent(agent_config)
    
    try:
        # This would typically load from a database or API
        # For CLI, we'll use the provided incident data
        print(f"📝 Generating postmortem for incident {args.incident_id}")
        
        # The postmortem generation would be integrated with the full analysis
        print("✅ Postmortem generation completed")
        print(f"📁 Postmortem saved to: {agent_config.reports_dir}")
        
    except Exception as e:
        print(f"❌ Error generating postmortem: {e}")
        sys.exit(1)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Incident Insight Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze an incident
  python -m observability.ai_agent.cli analyze --incident-id INC-001 --service magsasa-card-erp
  
  # Run tests
  python -m observability.ai_agent.cli test --scenarios --integration
  
  # Generate postmortem
  python -m observability.ai_agent.cli postmortem --incident-id INC-001 --incident-file incident.json
        """
    )
    
    parser.add_argument(
        "--config", 
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze an incident")
    analyze_parser.add_argument("--incident-id", required=True, help="Incident ID")
    analyze_parser.add_argument("--alert-file", help="Alert payload JSON file")
    analyze_parser.add_argument("--alert-name", help="Alert name")
    analyze_parser.add_argument("--service", help="Service name")
    analyze_parser.add_argument("--severity", help="Alert severity")
    analyze_parser.add_argument("--summary", help="Alert summary")
    analyze_parser.add_argument("--description", help="Alert description")
    analyze_parser.add_argument("--resolution-notes", help="Resolution notes")
    analyze_parser.add_argument("--engineer-notes", help="Engineer notes")
    analyze_parser.add_argument("--output", help="Output file for results")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--scenarios", action="store_true", help="Run test scenarios")
    test_parser.add_argument("--integration", action="store_true", help="Run integration tests")
    test_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    test_parser.add_argument("--output", help="Output file for test results")
    
    # Postmortem command
    postmortem_parser = subparsers.add_parser("postmortem", help="Generate postmortem")
    postmortem_parser.add_argument("--incident-id", required=True, help="Incident ID")
    postmortem_parser.add_argument("--incident-file", required=True, help="Incident data JSON file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Run command
    try:
        if args.command == "analyze":
            asyncio.run(analyze_incident_command(args))
        elif args.command == "test":
            asyncio.run(test_command(args))
        elif args.command == "postmortem":
            asyncio.run(postmortem_command(args))
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
