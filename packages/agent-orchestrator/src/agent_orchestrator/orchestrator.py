"""Agent Orchestrator - Central coordination for all AgSense agents."""

import asyncio
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

import structlog
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from agsense_core.models.contracts import (
    AgentInput, 
    AgentOutput, 
    AgentProtocol, 
    AgentRegistry,
    AgentStatus,
    Priority
)

logger = structlog.get_logger(__name__)


class AgentOrchestrator:
    """Central orchestrator for managing and coordinating all AgSense agents."""
    
    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        """Initialize the orchestrator."""
        self.registry = registry or AgentRegistry()
        self.client = httpx.AsyncClient(timeout=30.0)
        self.running = False
        
    async def start(self) -> None:
        """Start the orchestrator service."""
        logger.info("Starting Agent Orchestrator")
        self.running = True
        
        # Register built-in agents
        await self._register_builtin_agents()
        
        # Start health monitoring
        asyncio.create_task(self._health_monitor())
        
        logger.info("Agent Orchestrator started successfully")
    
    async def stop(self) -> None:
        """Stop the orchestrator service."""
        logger.info("Stopping Agent Orchestrator")
        self.running = False
        await self.client.aclose()
        logger.info("Agent Orchestrator stopped")
    
    async def _register_builtin_agents(self) -> None:
        """Register all built-in agents."""
        agents_to_register = [
            "agent-ingest",
            "agent-retrieval", 
            "agent-scoring",
            "agent-notify",
            "agent-billing"
        ]
        
        for agent_name in agents_to_register:
            try:
                # For now, create placeholder agents
                # In a real implementation, these would be actual agent instances
                agent = PlaceholderAgent(agent_name)
                self.registry.register(agent)
                logger.info(f"Registered agent: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to register agent {agent_name}: {e}")
    
    async def _health_monitor(self) -> None:
        """Monitor health of all registered agents."""
        while self.running:
            try:
                health_status = await self.registry.health_check_all()
                unhealthy_agents = [
                    agent for agent, healthy in health_status.items() 
                    if not healthy
                ]
                
                if unhealthy_agents:
                    logger.warning(
                        "Unhealthy agents detected", 
                        unhealthy_agents=unhealthy_agents
                    )
                else:
                    logger.debug("All agents healthy")
                    
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def route_request(self, request: AgentInput) -> AgentOutput:
        """
        Route a request to the appropriate agent.
        
        Args:
            request: The agent input request
            
        Returns:
            AgentOutput: The response from the agent
        """
        start_time = time.time()
        
        try:
            logger.info(
                "Routing request",
                request_id=request.request_id,
                agent_type=request.agent_type,
                priority=request.priority
            )
            
            # Get the appropriate agent
            agent = self.registry.get_agent(request.agent_type)
            if not agent:
                return AgentOutput(
                    request_id=request.request_id,
                    agent_type=request.agent_type,
                    status=AgentStatus.FAILED,
                    error=f"Agent type '{request.agent_type}' not found",
                    error_code="AGENT_NOT_FOUND"
                )
            
            # Validate input
            if not await agent.validate_input(request):
                return AgentOutput(
                    request_id=request.request_id,
                    agent_type=request.agent_type,
                    status=AgentStatus.FAILED,
                    error="Invalid input data",
                    error_code="INVALID_INPUT"
                )
            
            # Execute the agent
            result = await self._execute_agent(agent, request)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(
                "Request completed",
                request_id=request.request_id,
                agent_type=request.agent_type,
                status=result.status,
                execution_time=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Request failed",
                request_id=request.request_id,
                agent_type=request.agent_type,
                error=str(e),
                execution_time=execution_time
            )
            
            return AgentOutput(
                request_id=request.request_id,
                agent_type=request.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                error_code="ORCHESTRATOR_ERROR",
                execution_time=execution_time
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _execute_agent(self, agent: AgentProtocol, request: AgentInput) -> AgentOutput:
        """Execute an agent with retry logic."""
        return await agent.run(request)
    
    async def get_agent_status(self, agent_type: str) -> Dict[str, Any]:
        """Get status information for a specific agent."""
        agent = self.registry.get_agent(agent_type)
        if not agent:
            return {"status": "not_found"}
        
        try:
            is_healthy = await agent.health_check()
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "info": agent.get_agent_info()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        agents_info = self.registry.list_agents()
        health_status = await self.registry.health_check_all()
        
        return {
            "orchestrator": {
                "status": "running" if self.running else "stopped",
                "registered_agents": len(agents_info)
            },
            "agents": {
                agent_type: {
                    "info": info,
                    "healthy": health_status.get(agent_type, False)
                }
                for agent_type, info in agents_info.items()
            }
        }


class PlaceholderAgent(AgentProtocol):
    """Placeholder agent implementation for testing."""
    
    def __init__(self, agent_type: str) -> None:
        """Initialize the placeholder agent."""
        super().__init__(agent_type)
    
    async def run(self, data: AgentInput) -> AgentOutput:
        """Execute the placeholder agent logic."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        return AgentOutput(
            request_id=data.request_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result={
                "message": f"Processed by {self.agent_type}",
                "payload_size": len(str(data.payload)),
                "timestamp": time.time()
            },
            metadata={"processed_by": "placeholder_agent"}
        )
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy."""
        return True
    
    async def validate_input(self, data: AgentInput) -> bool:
        """Validate the input data."""
        return (
            data.request_id is not None and 
            data.agent_type is not None and 
            data.payload is not None
        )
