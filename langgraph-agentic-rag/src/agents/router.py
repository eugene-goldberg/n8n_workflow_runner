"""Router agent for intelligent query routing."""

import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from config.settings import settings
from src.state.types import RouterDecision

logger = logging.getLogger(__name__)

# Router prompt template
ROUTER_PROMPT = """You are a query router for an advanced RAG system. Analyze the user's query and determine the best retrieval strategy.

Available routes:
1. "simple_greeting" - For greetings, thanks, or other social interactions that don't require retrieval
2. "fact_lookup" - For simple factual questions that can be answered with semantic search on documents
3. "relational_query" - For questions about:
   - Relationships between entities (customers, products, teams, etc.)
   - Aggregations and calculations (percentages, counts, sums)
   - Time-based analysis (events in last X days)
   - Multi-hop queries requiring graph traversal
4. "hybrid_search" - For queries containing specific names, acronyms, or technical terms
5. "ambiguous" - For unclear queries that need clarification

Analyze this query: {query}

Respond with a JSON object containing:
- "route": one of the above route options
- "reasoning": brief explanation of why you chose this route

Examples:
- "What is machine learning?" -> {{"route": "fact_lookup", "reasoning": "Simple definitional query"}}
- "Find documents about Project Titan from 2023" -> {{"route": "hybrid_search", "reasoning": "Contains specific project name and date"}}
- "Who directed movies starring actors from Top Gun?" -> {{"route": "relational_query", "reasoning": "Multi-hop query about relationships"}}
- "What percentage of customers have success scores below 60?" -> {{"route": "relational_query", "reasoning": "Requires aggregation and calculation on customer data"}}
- "How many customers experienced negative events in the last 90 days?" -> {{"route": "relational_query", "reasoning": "Time-based analysis of customer-event relationships"}}
"""


def create_router_agent():
    """Create the router agent for query classification."""
    
    llm = ChatOpenAI(
        api_key=settings.openai.api_key,
        model=settings.openai.model,
        temperature=0  # Deterministic routing
    )
    
    parser = JsonOutputParser()
    
    async def route_query(query: str) -> RouterDecision:
        """Route a query to the appropriate retrieval strategy.
        
        Args:
            query: The user's query
            
        Returns:
            RouterDecision with route and reasoning
        """
        try:
            messages = [
                SystemMessage(content=ROUTER_PROMPT.format(query=query))
            ]
            
            response = await llm.ainvoke(messages)
            result = parser.parse(response.content)
            
            # Validate the route
            valid_routes = ["simple_greeting", "fact_lookup", "relational_query", "hybrid_search", "ambiguous"]
            if result.get("route") not in valid_routes:
                logger.warning(f"Invalid route: {result.get('route')}. Defaulting to fact_lookup.")
                result["route"] = "fact_lookup"
            
            logger.info(f"Routed query to: {result['route']} - {result.get('reasoning', '')}")
            
            return RouterDecision(
                route=result["route"],
                reasoning=result.get("reasoning", "")
            )
            
        except Exception as e:
            logger.error(f"Error in routing: {e}")
            # Default to fact lookup on error
            return RouterDecision(
                route="fact_lookup",
                reasoning="Error in routing, defaulting to fact lookup"
            )
    
    return route_query