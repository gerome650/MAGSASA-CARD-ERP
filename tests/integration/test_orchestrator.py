"""Integration tests for the Agent Orchestrator."""

import asyncio

import pytest
import pytest_asyncio
from core.models.contracts import AgentInput, AgentStatus, Priority


class TestOrchestratorIntegration:
    """Integration tests for the orchestrator."""

    @pytest_asyncio.fixture
    async def orchestrator(self):
        """Create an orchestrator instance for testing."""
        from agent_orchestrator.orchestrator import AgentOrchestrator

        orch = AgentOrchestrator()
        await orch.start()
        try:
            yield orch
        finally:
            await orch.stop()

    @pytest.mark.asyncio
    async def test_orchestrator_start_stop(self, orchestrator):
        """Test starting and stopping the orchestrator."""
        assert orchestrator.running is True

        await orchestrator.stop()
        assert orchestrator.running is False

    @pytest.mark.asyncio
    async def test_route_request_success(self, orchestrator):
        """Test successfully routing a request."""
        request = AgentInput(
            request_id="test-123",
            agent_type="agent-ingest",
            payload={"data": "test"},
            priority=Priority.NORMAL,
        )

        response = await orchestrator.route_request(request)

        assert response.request_id == "test-123"
        assert response.agent_type == "agent-ingest"
        assert response.status == AgentStatus.COMPLETED
        assert response.result is not None

    @pytest.mark.asyncio
    async def test_route_request_invalid_agent(self, orchestrator):
        """Test routing a request to a non-existent agent."""
        request = AgentInput(
            request_id="test-456",
            agent_type="nonexistent-agent",
            payload={"data": "test"},
        )

        response = await orchestrator.route_request(request)

        assert response.status == AgentStatus.FAILED
        assert response.error is not None
        assert "not found" in response.error.lower()

    @pytest.mark.asyncio
    async def test_get_system_status(self, orchestrator):
        """Test getting system status."""
        status = await orchestrator.get_system_status()

        assert "orchestrator" in status
        assert "agents" in status
        assert status["orchestrator"]["status"] == "running"
        assert status["orchestrator"]["registered_agents"] > 0

    @pytest.mark.asyncio
    async def test_get_agent_status(self, orchestrator):
        """Test getting individual agent status."""
        status = await orchestrator.get_agent_status("agent-ingest")

        assert "status" in status
        assert "info" in status
        assert status["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_multiple_requests(self, orchestrator):
        """Test handling multiple concurrent requests."""
        requests = [
            AgentInput(
                request_id=f"test-{i}",
                agent_type="agent-ingest",
                payload={"data": f"test-{i}"},
            )
            for i in range(5)
        ]

        # Process all requests concurrently
        responses = await asyncio.gather(
            *[orchestrator.route_request(req) for req in requests]
        )

        assert len(responses) == 5
        for response in responses:
            assert response.status == AgentStatus.COMPLETED
            assert response.result is not None

    @pytest.mark.asyncio
    async def test_different_agent_types(self, orchestrator):
        """Test routing to different agent types."""
        agent_types = [
            "agent-ingest",
            "agent-retrieval",
            "agent-scoring",
            "agent-notify",
            "agent-billing",
        ]

        for agent_type in agent_types:
            request = AgentInput(
                request_id=f"test-{agent_type}",
                agent_type=agent_type,
                payload={"data": "test"},
            )

            response = await orchestrator.route_request(request)

            assert response.status == AgentStatus.COMPLETED
            assert response.agent_type == agent_type
            assert response.result is not None
