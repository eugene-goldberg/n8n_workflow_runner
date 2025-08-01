#!/usr/bin/env python3
"""
Integration script to add deterministic routing to SpyroSolutions agent
"""

import sys
from pathlib import Path

# Template for modifying the SpyroSolutions agent
AGENT_MODIFICATION = '''
# Add this to /root/spyro-agentic-rag/app/agent/agent.py

import sys
sys.path.append('/root/langgraph-agentic-rag')
from app.agent.router import DeterministicRouter
from app.schemas.routing import RetrievalStrategy

# Initialize router globally
DETERMINISTIC_ROUTER = DeterministicRouter()

# Modify the existing SYSTEM_PROMPT to add routing instructions
def get_enhanced_system_prompt(base_prompt: str, query: str) -> str:
    """Enhance system prompt with deterministic routing decision"""
    
    # Get routing decision
    routing_decision = DETERMINISTIC_ROUTER.route(query)
    
    # Create routing instructions based on decision
    routing_instructions = {
        RetrievalStrategy.GRAPH: """
MANDATORY ROUTING INSTRUCTION:
This query requires accessing specific business data from the knowledge graph.
You MUST use one of these tools: get_entity_relationships or graph_search
DO NOT use vector_search for this query.
Detected entities: {entities}
""",
        RetrievalStrategy.VECTOR: """
MANDATORY ROUTING INSTRUCTION:
This query is asking for general concepts or documentation.
You MUST use the vector_search tool.
DO NOT use graph tools for this query.
""",
        RetrievalStrategy.HYBRID_SEQUENTIAL: """
MANDATORY ROUTING INSTRUCTION:
This query requires both semantic understanding and relationship exploration.
You MUST:
1. First use vector_search to find relevant concepts
2. Then use get_entity_relationships to explore specific entities
""",
        RetrievalStrategy.HYBRID_PARALLEL: """
MANDATORY ROUTING INSTRUCTION:
This is a comparative query requiring both data sources.
You MUST use BOTH vector_search AND graph_search tools.
Combine their results to provide a comprehensive answer.
""",
        RetrievalStrategy.NO_RETRIEVAL: """
This is a conversational query that doesn't require database access.
Respond directly without using any search tools.
"""
    }
    
    instruction = routing_instructions[routing_decision.strategy].format(
        entities=', '.join(routing_decision.detected_entities) or 'None'
    )
    
    # Log the routing decision for monitoring
    import logging
    logging.info(f"Router Decision - Query: {query[:50]}... Strategy: {routing_decision.strategy.value} Confidence: {routing_decision.confidence}")
    
    # Prepend routing instruction to the base prompt
    return instruction + "\\n\\n" + base_prompt

# In the existing agent class, modify the system prompt before each query
# For example, if using PydanticAI:

from pydantic_ai import Agent as PydanticAgent

class EnhancedSpyroAgent(PydanticAgent):
    """Enhanced agent with deterministic routing"""
    
    async def run(self, query: str, *args, **kwargs):
        # Get base system prompt
        original_prompt = self.system_prompt
        
        # Enhance with routing instructions
        self.system_prompt = get_enhanced_system_prompt(original_prompt, query)
        
        try:
            # Run with enhanced prompt
            result = await super().run(query, *args, **kwargs)
            
            # Log tool usage for monitoring
            if hasattr(result, 'tool_calls'):
                tools_used = [call.tool_name for call in result.tool_calls]
                routing_decision = DETERMINISTIC_ROUTER.route(query)
                
                # Check if tools match expectation
                expected_tools = {
                    RetrievalStrategy.GRAPH: ['get_entity_relationships', 'graph_search'],
                    RetrievalStrategy.VECTOR: ['vector_search'],
                    RetrievalStrategy.HYBRID_SEQUENTIAL: ['vector_search', 'get_entity_relationships'],
                    RetrievalStrategy.HYBRID_PARALLEL: ['vector_search', 'graph_search'],
                    RetrievalStrategy.NO_RETRIEVAL: []
                }
                
                expected = expected_tools.get(routing_decision.strategy, [])
                matches = any(tool in tools_used for tool in expected)
                
                logging.info(f"Tool Usage - Expected: {expected}, Actual: {tools_used}, Match: {matches}")
                
            return result
            
        finally:
            # Restore original prompt
            self.system_prompt = original_prompt
'''

print("Integration code for SpyroSolutions agent:")
print("=" * 80)
print(AGENT_MODIFICATION)
print("=" * 80)

# Also create a simpler prompt modification function
SIMPLE_PROMPT_MOD = '''
# Simpler integration - just modify the prompt

def enhance_prompt_with_routing(prompt: str, query: str) -> str:
    """Add routing instructions to any prompt"""
    from app.agent.router import DeterministicRouter
    
    router = DeterministicRouter()
    decision = router.route(query)
    
    if decision.strategy.value == "graph":
        return f"You MUST use graph_search or get_entity_relationships for this query. {prompt}"
    elif decision.strategy.value == "vector":
        return f"You MUST use vector_search for this query. {prompt}"
    elif decision.strategy.value == "hybrid_parallel":
        return f"You MUST use BOTH vector_search AND graph_search for this comparative query. {prompt}"
    else:
        return prompt
'''

print("\n\nSimpler prompt modification:")
print("=" * 80)
print(SIMPLE_PROMPT_MOD)