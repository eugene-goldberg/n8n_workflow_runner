"""Node implementations for the LangGraph agent."""

import logging
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import END

from config.settings import settings
from src.state.types import AgentState, ToolCall
from src.tools import ALL_SEARCH_TOOLS
from .router import create_router_agent

logger = logging.getLogger(__name__)


# Initialize router
router = create_router_agent()

# Initialize LLM for responses
response_llm = ChatOpenAI(
    api_key=settings.openai.api_key,
    model=settings.openai.model,
    temperature=settings.openai.temperature
)


async def router_node(state: AgentState) -> Dict[str, Any]:
    """Router node that analyzes the query and decides on retrieval strategy."""
    logger.info(f"Routing query: {state['query']}")
    
    # Get routing decision
    route_decision = await router(state["query"])
    
    # Update state with routing decision
    return {
        "route_decision": route_decision,
        "messages": [AIMessage(content=f"Routing to: {route_decision['route']}")],
    }


async def greeting_node(state: AgentState) -> Dict[str, Any]:
    """Handle simple greetings without retrieval."""
    logger.info("Handling greeting")
    
    response = await response_llm.ainvoke([
        SystemMessage(content="You are a helpful AI assistant. Respond warmly to the user's greeting."),
        HumanMessage(content=state["query"])
    ])
    
    return {
        "final_answer": response.content,
        "messages": [response]
    }


async def clarification_node(state: AgentState) -> Dict[str, Any]:
    """Ask for clarification on ambiguous queries."""
    logger.info("Requesting clarification")
    
    response = await response_llm.ainvoke([
        SystemMessage(content="The user's query is ambiguous. Ask for clarification in a helpful way."),
        HumanMessage(content=state["query"])
    ])
    
    return {
        "messages": [response],
        "needs_approval": True,
        "approval_request": "Please clarify your question"
    }


async def retrieval_node(state: AgentState) -> Dict[str, Any]:
    """Execute multi-strategy agentic retrieval."""
    query = state["query"]
    
    logger.info(f"Executing agentic multi-strategy retrieval for: {query}")
    
    # Get all retrieval results from multiple strategies
    all_results = []
    all_tool_calls = []
    
    # Always try multiple strategies for comprehensive coverage
    strategies = [
        ("graph_query_tool", "Graph query for relationships and aggregations"),
        ("vector_search_tool", "Semantic search for conceptual information"),
        ("hybrid_search_tool", "Hybrid search for specific entities")
    ]
    
    # Try each strategy
    for tool_name, description in strategies:
        logger.info(f"Trying {tool_name}: {description}")
        
        # Find the tool
        tool = next((t for t in ALL_SEARCH_TOOLS if t.name == tool_name), None)
        if not tool:
            logger.error(f"Tool not found: {tool_name}")
            continue
        
        try:
            # Execute the tool
            result = await tool.ainvoke({"query": query})
            
            # Always include results, even if they say "no results"
            # The synthesis will determine how to use them
            all_results.append({
                "content": result,
                "metadata": {"strategy": description},
                "source": tool_name,
                "score": 1.0
            })
            
            # Record the tool call
            tool_call = ToolCall(
                tool_name=tool_name,
                arguments={"query": query},
                result=result,
                error=None
            )
            all_tool_calls.append(tool_call)
            
        except Exception as e:
            logger.error(f"Error in {tool_name}: {e}")
            tool_call = ToolCall(
                tool_name=tool_name,
                arguments={"query": query},
                result=None,
                error=str(e)
            )
            all_tool_calls.append(tool_call)
    
    return {
        "retrieval_results": all_results,
        "tool_calls": all_tool_calls,
        "messages": [AIMessage(content=f"Executed {len(all_tool_calls)} retrieval strategies")]
    }


async def synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Synthesize final answer with true agentic behavior."""
    logger.info("Synthesizing final answer with agentic approach")
    
    # Build context from all retrieval results
    context_parts = []
    strategies_used = []
    
    for result in state.get("retrieval_results", []):
        source = result.get('source', 'unknown')
        content = result.get('content', '')
        context_parts.append(f"[{source}]:\n{content}")
        strategies_used.append(result.get('metadata', {}).get('strategy', source))
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No context retrieved."
    
    # Build improved synthesis prompt
    messages = [
        SystemMessage(content="""You are an advanced agentic RAG assistant. Your goal is to find and synthesize the best possible answer using ALL available information.

CRITICAL INSTRUCTIONS:
1. ALWAYS attempt to provide a meaningful answer based on the retrieved context
2. Look for partial information across different retrievers that can be combined
3. If exact data isn't available, provide the closest relevant information you have
4. Use inference and reasoning to connect related pieces of information
5. If one retriever says "no results" but another has partial data, USE the partial data
6. NEVER simply say "the information is not available" without first attempting to:
   - Combine partial results from different sources
   - Infer relationships from available data
   - Provide related information that addresses the spirit of the question
   - Explain what you CAN determine from the available data

Only as a LAST RESORT, if absolutely NO relevant information exists across ALL retrievers, explain what specific data would be needed.

Remember: Your job is to be helpful and find answers by being creative with the available information, not to give up when the first retriever fails."""),
        HumanMessage(content=f"""Question: {state['query']}

Retrieved Context from {len(strategies_used)} strategies ({', '.join(set(strategies_used))}):
{context}

Based on ALL the retrieved information, provide the most comprehensive answer possible. Be creative in combining information from different sources.""")
    ]
    
    response = await response_llm.ainvoke(messages)
    
    return {
        "final_answer": response.content,
        "messages": [response]
    }


async def error_reflection_node(state: AgentState) -> Dict[str, Any]:
    """Reflect on errors and suggest corrections."""
    logger.info("Reflecting on error")
    
    error_msg = state.get("error", "Unknown error")
    query = state["query"]
    
    messages = [
        SystemMessage(content="""An error occurred while processing the query. 
        Analyze the error and suggest how to proceed. Be helpful and suggest alternatives."""),
        HumanMessage(content=f"Query: {query}\nError: {error_msg}")
    ]
    
    response = await response_llm.ainvoke(messages)
    
    # Clear error flag for retry
    return {
        "messages": [response],
        "error": None,
        "error_count": state.get("error_count", 0)
    }


async def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """Node for human-in-the-loop approval."""
    logger.info("Awaiting human approval")
    
    # This node would integrate with an external UI/API for human feedback
    # For now, we'll simulate approval
    return {
        "needs_approval": False,
        "human_feedback": "Approved",
        "messages": [HumanMessage(content="Human approval received")]
    }


# Conditional edge functions

def route_after_router(state: AgentState) -> str:
    """Determine next node after routing."""
    if not state.get("route_decision"):
        return "router"
    
    route = state["route_decision"]["route"]
    
    if route == "simple_greeting":
        return "greeting"
    elif route == "ambiguous":
        return "clarification"
    else:
        return "retrieval"


def route_after_retrieval(state: AgentState) -> str:
    """Determine next node after retrieval."""
    if state.get("error"):
        if state.get("error_count", 0) >= 3:
            return "synthesis"  # Give up after 3 errors
        return "error_reflection"
    return "synthesis"


def route_after_error_reflection(state: AgentState) -> str:
    """Determine next node after error reflection."""
    if state.get("error_count", 0) >= 3:
        return "synthesis"  # Give up after 3 errors
    return "retrieval"  # Retry retrieval


def should_continue(state: AgentState) -> str:
    """Determine if we should continue or end."""
    if state.get("final_answer"):
        return END
    
    if state.get("needs_approval"):
        return "human_approval"
    
    if state.get("iteration_count", 0) >= state.get("max_iterations", 10):
        return END
    
    return "router"