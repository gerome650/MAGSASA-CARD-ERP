"""Ingest Agent - Handles data ingestion and processing."""

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


class IngestAgent(AgentProtocol):
    """Agent responsible for data ingestion and initial processing."""

    def __init__(self) -> None:
        """Initialize the ingest agent."""
        super().__init__("agent-ingest")

    async def run(self, data: AgentInput) -> AgentOutput:
        """Process incoming data for ingestion."""
        logger.info("Processing ingest request", request_id=data.request_id)

        try:
            # Simulate data ingestion processing
            await asyncio.sleep(0.2)

            processed_data = {
                "ingested_at": time.time(),
                "data_size": len(str(data.payload)),
                "source": (
                    data.metadata.get("source", "unknown")
                    if data.metadata
                    else "unknown"
                ),
                "processed_by": self.agent_type,
            }

            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                result=processed_data,
                metadata={"ingestion_successful": True},
            )

        except Exception as e:
            logger.error("Ingest processing failed", error=str(e))
            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="INGEST_ERROR",
            )

    async def health_check(self) -> bool:
        """Check if the ingest agent is healthy."""
        return True

    async def validate_input(self, data: AgentInput) -> bool:
        """Validate input data for ingestion."""
        return data.payload is not None
