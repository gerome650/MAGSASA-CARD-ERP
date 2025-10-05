"""MCP stub adapter for Ingest Agent."""

import asyncio
import time

from core.adapters.mcp_base import MCPAdapter, MCPConfig
from core.models.contracts import AgentInput, AgentOutput, AgentStatus


class IngestMCPStub(MCPAdapter):
    """MCP stub adapter for data ingestion agent."""

    def __init__(self, config: MCPConfig = None) -> None:
        """Initialize the ingest MCP stub adapter."""
        super().__init__("agent-ingest", config)

    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process ingestion request via MCP stub.
        
        Args:
            data: Input request data
            
        Returns:
            AgentOutput: Processing result
        """
        # Simulate data ingestion processing
        await asyncio.sleep(0.2)

        processed_data = {
            "ingested_at": time.time(),
            "data_size": len(str(data.payload)),
            "source": data.metadata.get("source", "unknown") if data.metadata else "unknown",
            "processed_by": self.agent_type,
            "mcp_adapter": "stub",
            "transport": self.config.transport
        }

        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=processed_data,
            metadata={
                "ingestion_successful": True,
                "mcp_enabled": self.config.enabled
            },
            correlation_id=data.correlation_id
        )

