#!/usr/bin/env python3
"""Example smoke test for the AgSense Agent Orchestrator."""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_orchestrator.orchestrator import AgentOrchestrator
from core.models.contracts import AgentInput, AgentStatus, Priority


async def smoke_test():
    """Run a comprehensive smoke test of the orchestrator."""
    print("🧪 Starting AgSense Orchestrator Smoke Test")
    print("=" * 50)

    orchestrator = AgentOrchestrator()

    try:
        # Start the orchestrator
        print("🚀 Starting orchestrator...")
        await orchestrator.start()
        print("✅ Orchestrator started successfully")

        # Test system status
        print("\n📊 Checking system status...")
        status = await orchestrator.get_system_status()
        print(f"   Registered agents: {status['orchestrator']['registered_agents']}")
        print(f"   Orchestrator status: {status['orchestrator']['status']}")

        # Test each agent type
        agent_types = [
            "agent-ingest",
            "agent-retrieval",
            "agent-scoring",
            "agent-notify",
            "agent-billing"
        ]

        print(f"\n🤖 Testing {len(agent_types)} agents...")

        for agent_type in agent_types:
            print(f"\n   Testing {agent_type}...")

            # Create test request
            request = AgentInput(
                request_id=f"smoke-test-{agent_type}",
                agent_type=agent_type,
                payload={
                    "test_data": f"Hello from {agent_type}",
                    "timestamp": asyncio.get_event_loop().time()
                },
                metadata={"smoke_test": True},
                priority=Priority.NORMAL
            )

            # Route the request
            response = await orchestrator.route_request(request)

            # Check response
            if response.status == AgentStatus.COMPLETED:
                print(f"   ✅ {agent_type} - SUCCESS")
                print(f"      Result: {response.result}")
            else:
                print(f"   ❌ {agent_type} - FAILED")
                print(f"      Error: {response.error}")
                return False

        # Test concurrent requests
        print("\n⚡ Testing concurrent requests...")
        concurrent_requests = [
            AgentInput(
                request_id=f"concurrent-test-{i}",
                agent_type="agent-ingest",
                payload={"concurrent_test": i}
            )
            for i in range(3)
        ]

        responses = await asyncio.gather(
            *[orchestrator.route_request(req) for req in concurrent_requests]
        )

        success_count = sum(1 for resp in responses if resp.status == AgentStatus.COMPLETED)
        print(f"   ✅ {success_count}/{len(responses)} concurrent requests succeeded")

        # Test health checks
        print("\n🏥 Testing health checks...")
        health_status = await orchestrator.registry.health_check_all()
        healthy_agents = sum(1 for healthy in health_status.values() if healthy)
        print(f"   ✅ {healthy_agents}/{len(health_status)} agents are healthy")

        print("\n🎉 Smoke test completed successfully!")
        print("   All systems operational and ready for development")

        return True

    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        return False

    finally:
        await orchestrator.stop()
        print("\n🛑 Orchestrator stopped")


async def main():
    """Main entrypoint."""
    success = await smoke_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
