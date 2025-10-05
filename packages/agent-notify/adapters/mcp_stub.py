"""MCP stub adapter for Notify Agent."""

import asyncio
import time

from core.adapters.mcp_base import MCPAdapter, MCPConfig
from core.models.contracts import AgentInput, AgentOutput, AgentStatus


class NotifyMCPStub(MCPAdapter):
    """MCP stub adapter for notification agent."""

    def __init__(self, config: MCPConfig = None) -> None:
        """Initialize the notify MCP stub adapter."""
        super().__init__("agent-notify", config)

    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process notification request via MCP stub.
        
        Args:
            data: Input request data
            
        Returns:
            AgentOutput: Notification result
        """
        # Simulate notification processing
        await asyncio.sleep(0.1)

        notification_data = {
            "notified_at": time.time(),
            "recipient": data.payload.get("recipient", "unknown"),
            "channel": data.payload.get("channel", "email"),
            "status": "sent",
            "processed_by": self.agent_type,
            "mcp_adapter": "stub",
            "transport": self.config.transport
        }

        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=notification_data,
            metadata={
                "notification_successful": True,
                "mcp_enabled": self.config.enabled
            },
            correlation_id=data.correlation_id
        )

