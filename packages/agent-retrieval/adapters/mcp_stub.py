"""MCP stub adapter for Retrieval Agent."""

import asyncio
import time

from core.adapters.mcp_base import MCPAdapter, MCPConfig
from core.models.contracts import AgentInput, AgentOutput, AgentStatus


class RetrievalMCPStub(MCPAdapter):
    """MCP stub adapter for data retrieval agent."""

    def __init__(self, config: MCPConfig = None) -> None:
        """Initialize the retrieval MCP stub adapter."""
        super().__init__("agent-retrieval", config)

    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process retrieval request via MCP stub.

        Args:
            data: Input request data

        Returns:
            AgentOutput: Retrieved data
        """
        # Simulate data retrieval processing
        await asyncio.sleep(0.15)

        query = data.payload.get("query", {})
        retrieved_data = {
            "retrieved_at": time.time(),
            "query": query,
            "results_count": 10,  # Simulated
            "processed_by": self.agent_type,
            "mcp_adapter": "stub",
            "transport": self.config.transport,
        }

        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=retrieved_data,
            metadata={"retrieval_successful": True, "mcp_enabled": self.config.enabled},
            correlation_id=data.correlation_id,
        )
