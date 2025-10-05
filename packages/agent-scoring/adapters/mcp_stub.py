"""MCP stub adapter for Scoring Agent."""

import asyncio
import random
import time

from core.adapters.mcp_base import MCPAdapter, MCPConfig
from core.models.contracts import AgentInput, AgentOutput, AgentStatus


class ScoringMCPStub(MCPAdapter):
    """MCP stub adapter for data scoring agent."""

    def __init__(self, config: MCPConfig = None) -> None:
        """Initialize the scoring MCP stub adapter."""
        super().__init__("agent-scoring", config)

    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process scoring request via MCP stub.

        Args:
            data: Input request data

        Returns:
            AgentOutput: Scoring results
        """
        # Simulate scoring processing
        await asyncio.sleep(0.25)

        scoring_data = {
            "scored_at": time.time(),
            "score": round(random.uniform(0.5, 1.0), 2),  # Simulated score
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "processed_by": self.agent_type,
            "mcp_adapter": "stub",
            "transport": self.config.transport,
        }

        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=scoring_data,
            metadata={"scoring_successful": True, "mcp_enabled": self.config.enabled},
            correlation_id=data.correlation_id,
        )
