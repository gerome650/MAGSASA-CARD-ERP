"""Billing Agent - Handles billing and payment processing."""

import asyncio
import time

import structlog
from core.models.contracts import (
    AgentInput,
    AgentOutput,
    AgentProtocol,
    AgentStatus,
)

logger = structlog.get_logger(__name__)


class BillingAgent(AgentProtocol):
    """Agent responsible for billing and payment processing."""

    def __init__(self) -> None:
        """Initialize the billing agent."""
        super().__init__("agent-billing")

    async def run(self, data: AgentInput) -> AgentOutput:
        """Process billing requests."""
        logger.info("Processing billing request", request_id=data.request_id)

        try:
            # Simulate billing processing
            await asyncio.sleep(0.3)

            billing_data = {
                "amount": data.payload.get("amount", 0),
                "currency": data.payload.get("currency", "USD"),
                "processed_at": time.time(),
                "processed_by": self.agent_type
            }

            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                result=billing_data,
                metadata={"billing_successful": True}
            )

        except Exception as e:
            logger.error("Billing processing failed", error=str(e))
            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="BILLING_ERROR"
            )

    async def health_check(self) -> bool:
        """Check if the billing agent is healthy."""
        return True

    async def validate_input(self, data: AgentInput) -> bool:
        """Validate input data for billing."""
        return isinstance(data.payload, dict)
