"""Core contracts and protocols for AgSense agent orchestration."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class Priority(str, Enum):
    """Request priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AgentInput(BaseModel):
    """Input contract for agent requests."""

    request_id: str = Field(..., description="Unique request identifier")
    agent_type: str = Field(..., description="Type of agent to execute")
    payload: dict[str, Any] = Field(..., description="Request payload data")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata for the request"
    )
    priority: Priority = Field(
        default=Priority.NORMAL,
        description="Request priority level"
    )
    timeout: int | None = Field(
        default=30,
        description="Request timeout in seconds"
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            # Add custom encoders if needed
        }


class AgentOutput(BaseModel):
    """Output contract for agent responses."""

    request_id: str = Field(..., description="Request identifier")
    agent_type: str = Field(..., description="Type of agent that processed the request")
    status: AgentStatus = Field(..., description="Execution status")
    result: dict[str, Any] | None = Field(
        default=None,
        description="Successful execution result"
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed"
    )
    error_code: str | None = Field(
        default=None,
        description="Error code for programmatic handling"
    )
    execution_time: float | None = Field(
        default=None,
        description="Execution time in seconds"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional response metadata"
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class AgentProtocol(ABC):
    """Abstract base class for all AgSense agents."""

    def __init__(self, agent_type: str) -> None:
        """Initialize the agent with its type."""
        self.agent_type = agent_type

    @abstractmethod
    async def run(self, data: AgentInput) -> AgentOutput:
        """
        Execute the agent logic.
        
        Args:
            data: The input data for the agent
            
        Returns:
            AgentOutput: The result of the agent execution
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement run method")

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the agent is healthy and ready to process requests.
        
        Returns:
            bool: True if agent is healthy, False otherwise
        """
        raise NotImplementedError("Subclasses must implement health_check method")

    @abstractmethod
    async def validate_input(self, data: AgentInput) -> bool:
        """
        Validate the input data before processing.
        
        Args:
            data: The input data to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate_input method")

    def get_agent_info(self) -> dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dict containing agent metadata
        """
        return {
            "agent_type": self.agent_type,
            "version": "0.1.0",
            "status": "active"
        }


class AgentRegistry:
    """Registry for managing available agents."""

    def __init__(self) -> None:
        """Initialize the agent registry."""
        self._agents: dict[str, AgentProtocol] = {}

    def register(self, agent: AgentProtocol) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: The agent to register
        """
        self._agents[agent.agent_type] = agent

    def get_agent(self, agent_type: str) -> AgentProtocol | None:
        """
        Get an agent by type.
        
        Args:
            agent_type: The type of agent to retrieve
            
        Returns:
            AgentProtocol if found, None otherwise
        """
        return self._agents.get(agent_type)

    def list_agents(self) -> dict[str, dict[str, Any]]:
        """
        List all registered agents with their information.
        
        Returns:
            Dict mapping agent types to their info
        """
        return {
            agent_type: agent.get_agent_info()
            for agent_type, agent in self._agents.items()
        }

    async def health_check_all(self) -> dict[str, bool]:
        """
        Check health of all registered agents.
        
        Returns:
            Dict mapping agent types to their health status
        """
        health_status = {}
        for agent_type, agent in self._agents.items():
            try:
                health_status[agent_type] = await agent.health_check()
            except Exception:
                health_status[agent_type] = False
        return health_status


# Global agent registry instance
agent_registry = AgentRegistry()
