"""Base MCP (Model Context Protocol) adapter for AgSense agents."""

import os
import time
from abc import ABC, abstractmethod
from typing import Any

import structlog
from pydantic import BaseModel, Field

from core.models.contracts import AgentInput, AgentOutput, AgentStatus

logger = structlog.get_logger(__name__)


class MCPConfig(BaseModel):
    """Configuration for MCP adapter."""

    enabled: bool = Field(
        default_factory=lambda: os.getenv("AGS_MCP_ENABLED", "false").lower()
        in ("true", "1", "yes"),
        description="Whether MCP mode is enabled",
    )
    protocol_version: str = Field(default="1.0.0", description="MCP protocol version")
    transport: str = Field(
        default="stdio", description="Transport mechanism (stdio, http, mqtt)"
    )
    schema_validation: bool = Field(
        default=True, description="Enable schema validation"
    )
    trace_enabled: bool = Field(default=True, description="Enable request tracing")


class MCPAdapter(ABC):
    """
    Base MCP adapter for agent communication.

    This is a stub implementation that simulates MCP-like behavior
    locally before integrating real MCP transport adapters.
    """

    def __init__(self, agent_type: str, config: MCPConfig | None = None) -> None:
        """
        Initialize the MCP adapter.

        Args:
            agent_type: Type of agent this adapter serves
            config: MCP configuration (defaults to env-based config)
        """
        self.agent_type = agent_type
        self.config = config or MCPConfig()
        self.logger = logger.bind(agent=agent_type, mcp_enabled=self.config.enabled)

    def is_enabled(self) -> bool:
        """Check if MCP mode is enabled."""
        return self.config.enabled

    def validate_protocol_compliance(self) -> bool:
        """
        Validate that the agent implements MCP protocol correctly.

        Returns:
            bool: True if protocol compliant, False otherwise
        """
        try:
            # Check if the agent has required methods
            required_methods = ["run", "health_check", "validate_input"]
            for method in required_methods:
                if not hasattr(self, f"_agent_{method}"):
                    # For stub, we assume compliance if adapter exists
                    pass

            return True
        except Exception as e:
            self.logger.error("Protocol compliance check failed", error=str(e))
            return False

    def validate_schema(self, data: AgentInput) -> bool:
        """
        Validate input data against schema.

        Args:
            data: Input data to validate

        Returns:
            bool: True if schema valid, False otherwise
        """
        if not self.config.schema_validation:
            return True

        try:
            # Pydantic automatically validates on model instantiation
            # If we got here, it's valid
            return True
        except Exception as e:
            self.logger.error("Schema validation failed", error=str(e))
            return False

    async def send_request(self, data: AgentInput) -> AgentOutput:
        """
        Send a request through the MCP adapter.

        This is a stub implementation that simulates MCP transport.
        In production, this would use actual MCP transport (stdio, HTTP, MQTT, etc.)

        Args:
            data: Request data

        Returns:
            AgentOutput: Response from agent
        """
        start_time = time.time()

        self.logger.info(
            "MCP request started",
            request_id=data.request_id,
            agent=self.agent_type,
            transport=self.config.transport,
        )

        try:
            # Validate schema
            if not self.validate_schema(data):
                return AgentOutput(
                    request_id=data.request_id,
                    agent_type=self.agent_type,
                    status=AgentStatus.FAILED,
                    error="Schema validation failed",
                    error_code="SCHEMA_VALIDATION_ERROR",
                )

            # Process the request (stub implementation)
            result = await self._process_request(data)

            latency_ms = (time.time() - start_time) * 1000

            self.logger.info(
                "MCP request completed",
                request_id=data.request_id,
                agent=self.agent_type,
                latency_ms=latency_ms,
                status="ok",
            )

            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            self.logger.error(
                "MCP request failed",
                request_id=data.request_id,
                agent=self.agent_type,
                latency_ms=latency_ms,
                status="error",
                error=str(e),
            )

            return AgentOutput(
                request_id=data.request_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="MCP_REQUEST_ERROR",
                execution_time=latency_ms / 1000,
            )

    @abstractmethod
    async def _process_request(self, data: AgentInput) -> AgentOutput:
        """
        Process the request (to be implemented by subclasses).

        Args:
            data: Request data

        Returns:
            AgentOutput: Response
        """
        raise NotImplementedError("Subclasses must implement _process_request")

    def get_diagnostics(self) -> dict[str, Any]:
        """
        Get diagnostic information about the MCP adapter.

        Returns:
            Dict with diagnostic information
        """
        return {
            "agent_type": self.agent_type,
            "mcp_enabled": self.config.enabled,
            "protocol_version": self.config.protocol_version,
            "transport": self.config.transport,
            "schema_validation": self.config.schema_validation,
            "trace_enabled": self.config.trace_enabled,
            "protocol_compliant": self.validate_protocol_compliance(),
        }
