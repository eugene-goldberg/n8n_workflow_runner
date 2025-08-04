"""Main LangGraph agent implementation."""

import logging
import uuid
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from config.settings import settings
from src.state.types import AgentState
# from src.state.checkpointer import checkpointer_manager  # Disabled for now - no PostgreSQL
from .nodes import (
    router_node,
    greeting_node,
    clarification_node,
    retrieval_node,
    synthesis_node,
    error_reflection_node,
    human_approval_node,
    route_after_router,
    route_after_retrieval,
    route_after_error_reflection,
    should_continue
)

logger = logging.getLogger(__name__)


def create_main_agent():
    """Create the main LangGraph agent with all nodes and edges.
    
    Returns:
        Compiled LangGraph agent
    """
    # Create the graph
    builder = StateGraph(AgentState)
    
    # Add all nodes
    builder.add_node("router", router_node)
    builder.add_node("greeting", greeting_node)
    builder.add_node("clarification", clarification_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("synthesis", synthesis_node)
    builder.add_node("error_reflection", error_reflection_node)
    builder.add_node("human_approval", human_approval_node)
    
    # Set entry point
    builder.set_entry_point("router")
    
    # Add conditional edges
    builder.add_conditional_edges("router", route_after_router)
    builder.add_conditional_edges("retrieval", route_after_retrieval)
    builder.add_conditional_edges("error_reflection", route_after_error_reflection)
    
    # Add regular edges
    builder.add_edge("greeting", END)
    builder.add_edge("clarification", END)
    builder.add_edge("synthesis", END)
    builder.add_edge("human_approval", "router")
    
    # Compile without checkpointer for now (no PostgreSQL setup)
    graph = builder.compile()
    
    logger.info("Main agent graph compiled successfully")
    return graph


class AgentRunner:
    """Runner class for the agentic RAG system."""
    
    def __init__(self):
        """Initialize the agent runner."""
        self.graph = create_main_agent()
        logger.info("Agent runner initialized")
    
    async def run(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the agent with a query.
        
        Args:
            query: User's query
            session_id: Optional session ID for continuity
            thread_id: Optional thread ID for conversation persistence
            
        Returns:
            Dict containing the response and metadata
        """
        # Generate IDs if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        if not thread_id:
            thread_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=query)],
            query=query,
            route_decision=None,
            retrieval_results=[],
            tool_calls=[],
            error=None,
            error_count=0,
            needs_approval=False,
            approval_request=None,
            human_feedback=None,
            final_answer=None,
            session_id=session_id,
            thread_id=thread_id,
            iteration_count=0,
            max_iterations=settings.app.max_iterations
        )
        
        # Configure for persistence
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": session_id
            }
        }
        
        try:
            # Run the graph
            logger.info(f"Running agent for query: {query[:100]}...")
            
            final_state = None
            async for event in self.graph.astream(initial_state, config=config):
                logger.debug(f"Event: {event}")
                final_state = event
            
            # Extract final answer
            if final_state and isinstance(final_state, dict):
                # Find the final state from the last node
                for node_name, node_state in final_state.items():
                    if isinstance(node_state, dict) and node_state.get("final_answer"):
                        return {
                            "answer": node_state["final_answer"],
                            "session_id": session_id,
                            "thread_id": thread_id,
                            "metadata": {
                                "route": node_state.get("route_decision", {}).get("route"),
                                "tools_used": [tc["tool_name"] for tc in node_state.get("tool_calls", [])],
                                "error_count": node_state.get("error_count", 0)
                            }
                        }
            
            # Fallback if no final answer
            return {
                "answer": "I couldn't generate a complete response. Please try rephrasing your question.",
                "session_id": session_id,
                "thread_id": thread_id,
                "metadata": {"error": "No final answer generated"}
            }
            
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "session_id": session_id,
                "thread_id": thread_id,
                "metadata": {"error": str(e)}
            }
    
    async def continue_conversation(
        self,
        query: str,
        thread_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Continue an existing conversation.
        
        Args:
            query: New user query
            thread_id: Existing thread ID
            session_id: Optional session ID
            
        Returns:
            Dict containing the response and metadata
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # The graph will automatically load the previous state from the checkpointer
        return await self.run(query, session_id, thread_id)