"""MCP stub adapter for Billing Agent."""

import asyncio
import random
import time

from core.adapters.mcp_base import MCPAdapter, MCPConfig
from core.models.contracts import AgentInput, AgentOutput, AgentStatus


class BillingMCPStub(MCPAdapter):
    """MCP stub adapter for billing agent."""

    def __init__(self, config: MCPConfig = None) -> None:
        """Initialize the billing MCP stub adapter."""
        super().__init__("agent-billing", config)

    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process billing request via MCP stub.

        Args:
            data: Input request data

        Returns:
            AgentOutput: Billing result
        """
        # Simulate billing processing
        await asyncio.sleep(0.3)

        billing_data = {
            "billed_at": time.time(),
            "amount": data.payload.get("amount", 0.0),
            "currency": data.payload.get("currency", "USD"),
            "transaction_id": f"txn_{int(time.time())}_{random.randint(1000, 9999)}",
            "status": "completed",
            "processed_by": self.agent_type,
            "mcp_adapter": "stub",
            "transport": self.config.transport,
        }

        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=billing_data,
            metadata={"billing_successful": True, "mcp_enabled": self.config.enabled},
            correlation_id=data.correlation_id,
        )
