"""Notification Agent - Handles notifications and alerts."""

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


class NotifyAgent(AgentProtocol):
    """Agent responsible for notifications and alerts."""

    def __init__(self) -> None:
        """Initialize the notification agent."""
        super().__init__("agent-notify")

    async def run(self, data: AgentInput) -> AgentOutput:
        """Process notification requests."""
        logger.info("Processing notification request", request_id=data.request_id)

        try:
            # Simulate notification processing
            await asyncio.sleep(0.05)

            notification_data = {
                "message": data.payload.get("message", "Notification sent"),
                "sent_at": time.time(),
                "processed_by": self.agent_type
            }

            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                result=notification_data,
                metadata={"notification_sent": True}
            )

        except Exception as e:
            logger.error("Notification processing failed", error=str(e))
            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="NOTIFICATION_ERROR"
            )

    async def health_check(self) -> bool:
        """Check if the notification agent is healthy."""
        return True

    async def validate_input(self, data: AgentInput) -> bool:
        """Validate input data for notifications."""
        return isinstance(data.payload, dict)
