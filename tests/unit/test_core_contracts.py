"""Unit tests for core contracts and models."""

import pytest
from agsense_core.models.contracts import (
    AgentInput,
    AgentOutput,
    AgentProtocol,
    AgentRegistry,
    AgentStatus,
    Priority
)


class TestAgentInput:
    """Test cases for AgentInput model."""
    
    def test_agent_input_creation(self):
        """Test creating an AgentInput instance."""
        data = AgentInput(
            request_id="test-123",
            agent_type="test-agent",
            payload={"key": "value"}
        )
        
        assert data.request_id == "test-123"
        assert data.agent_type == "test-agent"
        assert data.payload == {"key": "value"}
        assert data.priority == Priority.NORMAL
        assert data.timeout == 30
    
    def test_agent_input_with_metadata(self):
        """Test AgentInput with metadata."""
        data = AgentInput(
            request_id="test-456",
            agent_type="test-agent",
            payload={"key": "value"},
            metadata={"source": "test"},
            priority=Priority.HIGH,
            timeout=60
        )
        
        assert data.metadata == {"source": "test"}
        assert data.priority == Priority.HIGH
        assert data.timeout == 60


class TestAgentOutput:
    """Test cases for AgentOutput model."""
    
    def test_agent_output_creation(self):
        """Test creating an AgentOutput instance."""
        output = AgentOutput(
            request_id="test-123",
            agent_type="test-agent",
            status=AgentStatus.COMPLETED,
            result={"processed": True}
        )
        
        assert output.request_id == "test-123"
        assert output.agent_type == "test-agent"
        assert output.status == AgentStatus.COMPLETED
        assert output.result == {"processed": True}
        assert output.error is None
    
    def test_agent_output_with_error(self):
        """Test AgentOutput with error."""
        output = AgentOutput(
            request_id="test-456",
            agent_type="test-agent",
            status=AgentStatus.FAILED,
            error="Test error",
            error_code="TEST_ERROR"
        )
        
        assert output.status == AgentStatus.FAILED
        assert output.error == "Test error"
        assert output.error_code == "TEST_ERROR"


class TestAgentRegistry:
    """Test cases for AgentRegistry."""
    
    def test_registry_creation(self):
        """Test creating an AgentRegistry."""
        registry = AgentRegistry()
        assert len(registry._agents) == 0
    
    def test_register_agent(self):
        """Test registering an agent."""
        registry = AgentRegistry()
        
        class TestAgent(AgentProtocol):
            def __init__(self):
                super().__init__("test-agent")
            
            async def run(self, data):
                return AgentOutput(
                    request_id=data.request_id,
                    agent_type=self.agent_type,
                    status=AgentStatus.COMPLETED
                )
            
            async def health_check(self):
                return True
            
            async def validate_input(self, data):
                return True
        
        agent = TestAgent()
        registry.register(agent)
        
        assert len(registry._agents) == 1
        assert registry.get_agent("test-agent") == agent
    
    def test_get_nonexistent_agent(self):
        """Test getting a non-existent agent."""
        registry = AgentRegistry()
        assert registry.get_agent("nonexistent") is None
    
    def test_list_agents(self):
        """Test listing all agents."""
        registry = AgentRegistry()
        
        class TestAgent(AgentProtocol):
            def __init__(self, agent_type):
                super().__init__(agent_type)
            
            async def run(self, data):
                pass
            
            async def health_check(self):
                return True
            
            async def validate_input(self, data):
                return True
        
        agent1 = TestAgent("agent-1")
        agent2 = TestAgent("agent-2")
        
        registry.register(agent1)
        registry.register(agent2)
        
        agents = registry.list_agents()
        assert len(agents) == 2
        assert "agent-1" in agents
        assert "agent-2" in agents


@pytest.mark.asyncio
class TestAgentProtocol:
    """Test cases for AgentProtocol."""
    
    async def test_agent_protocol_abstract_methods(self):
        """Test that AgentProtocol raises NotImplementedError for abstract methods."""
        
        class TestAgent(AgentProtocol):
            def __init__(self):
                super().__init__("test-agent")
        
        agent = TestAgent()
        
        with pytest.raises(NotImplementedError):
            await agent.run(AgentInput(
                request_id="test",
                agent_type="test",
                payload={}
            ))
        
        with pytest.raises(NotImplementedError):
            await agent.health_check()
        
        with pytest.raises(NotImplementedError):
            await agent.validate_input(AgentInput(
                request_id="test",
                agent_type="test",
                payload={}
            ))
    
    async def test_agent_info(self):
        """Test getting agent information."""
        
        class TestAgent(AgentProtocol):
            def __init__(self):
                super().__init__("test-agent")
            
            async def run(self, data):
                pass
            
            async def health_check(self):
                return True
            
            async def validate_input(self, data):
                return True
        
        agent = TestAgent()
        info = agent.get_agent_info()
        
        assert info["agent_type"] == "test-agent"
        assert info["version"] == "0.1.0"
        assert info["status"] == "active"
