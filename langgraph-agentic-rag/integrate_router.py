#!/usr/bin/env python3
"""
Integration script to test the deterministic router with the existing SpyroSolutions system
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.router import DeterministicRouter
from app.schemas.routing import RetrievalStrategy


def create_modified_agent_prompt(router_output):
    """
    Create a modified system prompt that enforces the router's decision
    """
    strategy_instructions = {
        RetrievalStrategy.GRAPH: """
MANDATORY: You MUST use the get_entity_relationships or graph_search tools for this query.
The query requires accessing specific business data from the knowledge graph.
DO NOT use vector_search for this query.
""",
        RetrievalStrategy.VECTOR: """
MANDATORY: You MUST use the vector_search tool for this query.
The query is asking for general concepts or documentation.
DO NOT use graph tools for this query.
""",
        RetrievalStrategy.HYBRID_SEQUENTIAL: """
MANDATORY: You MUST use a combination of tools in sequence:
1. First use vector_search to find relevant concepts
2. Then use get_entity_relationships to explore specific entities found
This query requires both semantic understanding and relationship exploration.
""",
        RetrievalStrategy.HYBRID_PARALLEL: """
MANDATORY: You MUST use both vector_search and graph_search tools.
Execute them and combine their results to answer this comparative query.
""",
        RetrievalStrategy.NO_RETRIEVAL: """
This is a conversational query that doesn't require database access.
Respond directly without using any search tools.
"""
    }
    
    base_prompt = """You are an intelligent AI assistant for SpyroSolutions with access to business data.

## ROUTING DECISION
Query: {query}
Selected Strategy: {strategy}
Confidence: {confidence}
Detected Entities: {entities}

{strategy_instructions}

## YOUR AVAILABLE TOOLS:
1. vector_search: For semantic/conceptual queries
2. graph_search: For relationship and entity queries  
3. get_entity_relationships: For specific entity data
4. hybrid_search: For complex queries needing both

Remember: Follow the routing decision above EXACTLY."""

    return base_prompt.format(
        query=router_output.query if hasattr(router_output, 'query') else '',
        strategy=router_output.strategy.value,
        confidence=router_output.confidence,
        entities=', '.join(router_output.detected_entities) or 'None',
        strategy_instructions=strategy_instructions[router_output.strategy]
    )


def test_integration():
    """Test the router integration with sample queries"""
    router = DeterministicRouter()
    
    test_queries = [
        "How much revenue is at risk if Disney churns?",
        "What is an SLA?",
        "Compare Disney and Netflix subscription models",
        "Show me the relationship between teams and their projects",
        "What are the top risks to our ARR targets?",
    ]
    
    print("🔧 Router Integration Test\n")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        # Route the query
        routing_decision = router.route(query)
        
        print(f"📍 Routing Decision:")
        print(f"   Strategy: {routing_decision.strategy.value}")
        print(f"   Confidence: {routing_decision.confidence:.2f}")
        print(f"   Entities: {routing_decision.detected_entities or 'None'}")
        print(f"   Reasoning: {routing_decision.reasoning}")
        
        # Generate modified prompt
        modified_prompt = create_modified_agent_prompt(routing_decision)
        
        print(f"\n📋 System Prompt Extract:")
        print("-" * 40)
        # Show just the strategy instructions part
        for line in modified_prompt.split('\n'):
            if 'MANDATORY:' in line or 'DO NOT' in line:
                print(f"   {line.strip()}")
        print("-" * 40)


def generate_integration_code():
    """Generate code to integrate with the existing SpyroSolutions agent"""
    
    integration_code = '''
# Integration code for app/agent/agent.py in SpyroSolutions

from langgraph_agentic_rag.app.agent.router import DeterministicRouter
from langgraph_agentic_rag.app.schemas.routing import RetrievalStrategy

class EnhancedSpyroAgent:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router = DeterministicRouter()
        
    async def process_query(self, query: str):
        """Process query with deterministic routing"""
        
        # Step 1: Route the query
        routing_decision = self.router.route(query)
        
        # Step 2: Modify the system prompt based on routing
        self._enforce_tool_selection(routing_decision)
        
        # Step 3: Execute with the existing agent
        return await super().process_query(query)
        
    def _enforce_tool_selection(self, routing_decision):
        """Modify agent behavior to enforce routing decision"""
        
        # Map strategies to tool names
        tool_mapping = {
            RetrievalStrategy.GRAPH: ["get_entity_relationships", "graph_search"],
            RetrievalStrategy.VECTOR: ["vector_search"],
            RetrievalStrategy.HYBRID_SEQUENTIAL: ["vector_search", "get_entity_relationships"],
            RetrievalStrategy.HYBRID_PARALLEL: ["vector_search", "graph_search"],
            RetrievalStrategy.NO_RETRIEVAL: []
        }
        
        # Get required tools
        required_tools = tool_mapping[routing_decision.strategy]
        
        # TODO: Implement actual tool enforcement logic
        # This could involve:
        # 1. Modifying the agent's tool list temporarily
        # 2. Adding routing instructions to the system prompt
        # 3. Using a custom tool selector
'''
    
    print("\n\n📦 Integration Code for SpyroSolutions:\n")
    print("=" * 80)
    print(integration_code)
    print("=" * 80)


if __name__ == "__main__":
    test_integration()
    generate_integration_code()