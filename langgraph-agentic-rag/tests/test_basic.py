"""Basic tests for the agentic RAG system."""

import pytest
from unittest.mock import Mock, patch

from src.state.types import AgentState, RouterDecision
from src.agents.router import create_router_agent


@pytest.mark.asyncio
async def test_router_simple_greeting():
    """Test router correctly identifies greetings."""
    with patch('src.agents.router.ChatOpenAI') as mock_llm:
        # Mock the LLM response
        mock_response = Mock()
        mock_response.content = '{"route": "simple_greeting", "reasoning": "User is greeting"}'
        mock_llm.return_value.ainvoke.return_value = mock_response
        
        router = create_router_agent()
        result = await router("Hello! How are you?")
        
        assert result["route"] == "simple_greeting"
        assert "reasoning" in result


@pytest.mark.asyncio
async def test_router_fact_lookup():
    """Test router correctly identifies fact lookups."""
    with patch('src.agents.router.ChatOpenAI') as mock_llm:
        # Mock the LLM response
        mock_response = Mock()
        mock_response.content = '{"route": "fact_lookup", "reasoning": "Simple definitional query"}'
        mock_llm.return_value.ainvoke.return_value = mock_response
        
        router = create_router_agent()
        result = await router("What is machine learning?")
        
        assert result["route"] == "fact_lookup"


def test_agent_state_initialization():
    """Test AgentState can be properly initialized."""
    state = AgentState(
        messages=[],
        query="Test query",
        route_decision=None,
        retrieval_results=[],
        tool_calls=[],
        error=None,
        error_count=0,
        needs_approval=False,
        approval_request=None,
        human_feedback=None,
        final_answer=None,
        session_id="test-session",
        thread_id="test-thread",
        iteration_count=0,
        max_iterations=10
    )
    
    assert state["query"] == "Test query"
    assert state["session_id"] == "test-session"
    assert state["max_iterations"] == 10


def test_router_decision_type():
    """Test RouterDecision type structure."""
    decision = RouterDecision(
        route="fact_lookup",
        reasoning="This is a simple fact query"
    )
    
    assert decision["route"] == "fact_lookup"
    assert decision["reasoning"] == "This is a simple fact query"