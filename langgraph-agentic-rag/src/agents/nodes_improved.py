"""Improved node implementations for true agentic RAG behavior."""

import logging
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
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


async def retrieval_node_improved(state: AgentState) -> Dict[str, Any]:
    """Execute comprehensive multi-strategy retrieval."""
    query = state["query"]
    
    logger.info(f"Executing multi-strategy retrieval for: {query}")
    
    # Get all retrieval results from multiple strategies
    all_results = []
    all_tool_calls = []
    
    # Define retrieval strategies to try
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
            
            # Check if result contains meaningful data
            if result and not any(phrase in result.lower() for phrase in [
                "no results", "not found", "no data", "unable to", "did not return"
            ]):
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
    
    # If no meaningful results, try query reformulation
    if not all_results:
        logger.info("No results found with direct strategies, trying query reformulation")
        
        # Reformulate query for better retrieval
        reformulation_prompt = f"""The following query didn't return results: "{query}"
        
Please reformulate this query in 2-3 different ways that might help find relevant information:
1. Break it down into simpler sub-queries
2. Use different terminology or synonyms
3. Focus on different aspects of the question

Provide the reformulated queries as a numbered list."""
        
        reformulation_response = await response_llm.ainvoke([
            SystemMessage(content=reformulation_prompt)
        ])
        
        # Store reformulation suggestion for synthesis
        all_results.append({
            "content": f"Query reformulation suggested:\n{reformulation_response.content}",
            "metadata": {"strategy": "reformulation"},
            "source": "query_reformulator",
            "score": 0.5
        })
    
    return {
        "retrieval_results": all_results,
        "tool_calls": all_tool_calls,
        "messages": [AIMessage(content=f"Executed {len(all_tool_calls)} retrieval strategies")]
    }


async def synthesis_node_improved(state: AgentState) -> Dict[str, Any]:
    """Synthesize final answer with emphasis on finding an answer."""
    logger.info("Synthesizing final answer with agentic approach")
    
    # Build context from all retrieval results
    context_parts = []
    strategies_used = []
    
    for result in state.get("retrieval_results", []):
        context_parts.append(f"[{result['source']}]:\n{result['content']}")
        strategies_used.append(result.get('metadata', {}).get('strategy', result['source']))
    
    context = "\n\n---\n\n".join(context_parts) if context_parts else "No context retrieved."
    
    # Build improved synthesis prompt
    messages = [
        SystemMessage(content="""You are an advanced agentic RAG assistant. Your goal is to find and synthesize the best possible answer using ALL available information.

CRITICAL INSTRUCTIONS:
1. ALWAYS attempt to provide a meaningful answer based on the retrieved context
2. Look for partial information that can be combined to form a complete answer
3. If exact data isn't available, provide the closest relevant information you have
4. Use inference and reasoning to connect related pieces of information
5. NEVER simply say "the information is not available" without first attempting to:
   - Combine partial results from different sources
   - Infer relationships from available data
   - Provide related information that addresses the spirit of the question

Only as a LAST RESORT, if absolutely NO relevant information exists, explain what specific data would be needed and suggest how the query could be reformulated.

Remember: Your job is to be helpful and find answers, not to give up easily."""),
        HumanMessage(content=f"""Question: {state['query']}

Retrieved Context from {len(strategies_used)} strategies:
{context}

Based on ALL the retrieved information, provide the most comprehensive answer possible. If you see query reformulation suggestions, explain how those could help get better results.""")
    ]
    
    response = await response_llm.ainvoke(messages)
    
    return {
        "final_answer": response.content,
        "messages": [response]
    }