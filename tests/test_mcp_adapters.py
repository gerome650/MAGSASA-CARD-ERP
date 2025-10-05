"""Tests for MCP adapters."""

import asyncio
import pytest
from core.models.contracts import AgentInput, AgentOutput, AgentStatus, Priority
from core.adapters.mcp_base import MCPConfig


@pytest.mark.asyncio
async def test_ingest_mcp_stub():
    """Test IngestMCPStub adapter."""
    from agent_ingest.adapters.mcp_stub import IngestMCPStub
    
    adapter = IngestMCPStub(MCPConfig(enabled=True))
    
    # Create test input
    agent_input = AgentInput(
        request_id="test_req_001",
        agent_type="agent-ingest",
        payload={"data": "test", "source": "unittest"},
        priority=Priority.NORMAL
    )
    
    # Process request
    result = await adapter.send_request(agent_input)
    
    # Assertions
    assert isinstance(result, AgentOutput)
    assert result.request_id == "test_req_001"
    assert result.agent_type == "agent-ingest"
    assert result.status == AgentStatus.COMPLETED
    assert result.result is not None
    assert "ingested_at" in result.result
    assert "data_size" in result.result
    assert result.metadata["ingestion_successful"] is True


@pytest.mark.asyncio
async def test_retrieval_mcp_stub():
    """Test RetrievalMCPStub adapter."""
    from agent_retrieval.adapters.mcp_stub import RetrievalMCPStub
    
    adapter = RetrievalMCPStub(MCPConfig(enabled=True))
    
    agent_input = AgentInput(
        request_id="test_req_002",
        agent_type="agent-retrieval",
        payload={"query": {"term": "test"}, "limit": 10},
        priority=Priority.NORMAL
    )
    
    result = await adapter.send_request(agent_input)
    
    assert result.status == AgentStatus.COMPLETED
    assert "retrieved_at" in result.result
    assert "results_count" in result.result


@pytest.mark.asyncio
async def test_scoring_mcp_stub():
    """Test ScoringMCPStub adapter."""
    from agent_scoring.adapters.mcp_stub import ScoringMCPStub
    
    adapter = ScoringMCPStub(MCPConfig(enabled=True))
    
    agent_input = AgentInput(
        request_id="test_req_003",
        agent_type="agent-scoring",
        payload={"data": "test_item"},
        priority=Priority.HIGH
    )
    
    result = await adapter.send_request(agent_input)
    
    assert result.status == AgentStatus.COMPLETED
    assert "score" in result.result
    assert "confidence" in result.result
    assert 0.0 <= result.result["score"] <= 1.0


@pytest.mark.asyncio
async def test_notify_mcp_stub():
    """Test NotifyMCPStub adapter."""
    from agent_notify.adapters.mcp_stub import NotifyMCPStub
    
    adapter = NotifyMCPStub(MCPConfig(enabled=True))
    
    agent_input = AgentInput(
        request_id="test_req_004",
        agent_type="agent-notify",
        payload={"recipient": "test@example.com", "channel": "email"},
        priority=Priority.NORMAL
    )
    
    result = await adapter.send_request(agent_input)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.result["status"] == "sent"


@pytest.mark.asyncio
async def test_billing_mcp_stub():
    """Test BillingMCPStub adapter."""
    from agent_billing.adapters.mcp_stub import BillingMCPStub
    
    adapter = BillingMCPStub(MCPConfig(enabled=True))
    
    agent_input = AgentInput(
        request_id="test_req_005",
        agent_type="agent-billing",
        payload={"amount": 100.0, "currency": "USD"},
        priority=Priority.NORMAL
    )
    
    result = await adapter.send_request(agent_input)
    
    assert result.status == AgentStatus.COMPLETED
    assert result.result["amount"] == 100.0
    assert result.result["currency"] == "USD"
    assert "transaction_id" in result.result


@pytest.mark.asyncio
async def test_mcp_config():
    """Test MCPConfig environment variable support."""
    import os
    
    # Test with env var disabled
    os.environ["AGS_MCP_ENABLED"] = "false"
    config = MCPConfig()
    assert config.enabled is False
    
    # Test with env var enabled
    os.environ["AGS_MCP_ENABLED"] = "true"
    config = MCPConfig()
    assert config.enabled is True
    
    # Clean up
    os.environ.pop("AGS_MCP_ENABLED", None)


def test_mcp_adapter_diagnostics():
    """Test MCP adapter diagnostics."""
    from agent_ingest.adapters.mcp_stub import IngestMCPStub
    
    adapter = IngestMCPStub(MCPConfig(enabled=True))
    diagnostics = adapter.get_diagnostics()
    
    assert diagnostics["agent_type"] == "agent-ingest"
    assert diagnostics["mcp_enabled"] is True
    assert diagnostics["protocol_version"] == "1.0.0"
    assert diagnostics["transport"] == "stdio"
    assert diagnostics["protocol_compliant"] is True


@pytest.mark.asyncio
async def test_parallel_agent_execution():
    """Test parallel execution of multiple agents."""
    from agent_ingest.adapters.mcp_stub import IngestMCPStub
    from agent_retrieval.adapters.mcp_stub import RetrievalMCPStub
    from agent_scoring.adapters.mcp_stub import ScoringMCPStub
    
    config = MCPConfig(enabled=True)
    
    # Create adapters
    ingest = IngestMCPStub(config)
    retrieval = RetrievalMCPStub(config)
    scoring = ScoringMCPStub(config)
    
    # Create inputs
    inputs = [
        AgentInput(
            request_id=f"test_req_{i}",
            agent_type=f"agent-{agent}",
            payload={"test": "data"},
            priority=Priority.NORMAL
        )
        for i, agent in enumerate(["ingest", "retrieval", "scoring"])
    ]
    
    # Execute in parallel
    results = await asyncio.gather(
        ingest.send_request(inputs[0]),
        retrieval.send_request(inputs[1]),
        scoring.send_request(inputs[2])
    )
    
    # Verify all succeeded
    assert all(r.status == AgentStatus.COMPLETED for r in results)
    assert len(results) == 3

