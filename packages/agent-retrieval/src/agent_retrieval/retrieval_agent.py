"""Retrieval Agent - Handles data retrieval and search operations."""

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


class RetrievalAgent(AgentProtocol):
    """Agent responsible for data retrieval and search operations."""

    def __init__(self) -> None:
        """Initialize the retrieval agent."""
        super().__init__("agent-retrieval")

    async def run(self, data: AgentInput) -> AgentOutput:
        """Process data retrieval requests."""
        logger.info("Processing retrieval request", request_id=data.request_id)

        try:
            # Simulate data retrieval processing
            await asyncio.sleep(0.15)

            query = data.payload.get("query", "")
            retrieved_data = {
                "query": query,
                "results_count": len(query.split()) if query else 0,
                "retrieved_at": time.time(),
                "processed_by": self.agent_type
            }

            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                result=retrieved_data,
                metadata={"retrieval_successful": True}
            )

        except Exception as e:
            logger.error("Retrieval processing failed", error=str(e))
            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="RETRIEVAL_ERROR"
            )

    async def health_check(self) -> bool:
        """Check if the retrieval agent is healthy."""
        return True

    async def validate_input(self, data: AgentInput) -> bool:
        """Validate input data for retrieval."""
        return isinstance(data.payload, dict)
