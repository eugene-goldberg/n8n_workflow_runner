#!/usr/bin/env python3
"""
Test integration of the deterministic router with SpyroSolutions API
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.router import DeterministicRouter
from app.schemas.routing import RetrievalStrategy


async def test_spyro_with_router():
    """Test SpyroSolutions API with router guidance"""
    
    router = DeterministicRouter()
    
    # Test queries that should use graph search
    test_queries = [
        "How much revenue is at risk if Disney churns?",
        "What are the top risks to our ARR targets?",
        "Show me the relationship between Disney and their subscription",
        "Which customers have MRR over $100k?",
        "What concerns have been raised about Netflix?"
    ]
    
    print("🧪 Testing SpyroSolutions with Deterministic Router\n")
    print("=" * 80)
    
    # SpyroSolutions API endpoint
    api_url = "http://localhost:8058/chat"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            
            # Route the query
            routing_decision = router.route(query)
            
            print(f"📍 Router Decision:")
            print(f"   Strategy: {routing_decision.strategy.value}")
            print(f"   Confidence: {routing_decision.confidence:.2f}")
            print(f"   Entities: {routing_decision.detected_entities or 'None'}")
            
            # Send to SpyroSolutions API
            try:
                response = await client.post(
                    api_url,
                    json={"message": query}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    print(f"\n🤖 SpyroSolutions Response:")
                    print(f"   Answer: {result.get('response', '')[:200]}...")
                    
                    # Check if tools used match router expectation
                    tools_used = result.get('tools_used', [])
                    print(f"   Tools Used: {tools_used}")
                    
                    # Verify tool selection
                    expected_tools = {
                        RetrievalStrategy.GRAPH: ['graph_search', 'get_entity_relationships'],
                        RetrievalStrategy.VECTOR: ['vector_search'],
                        RetrievalStrategy.HYBRID_SEQUENTIAL: ['vector_search', 'get_entity_relationships'],
                        RetrievalStrategy.HYBRID_PARALLEL: ['vector_search', 'graph_search']
                    }
                    
                    expected = expected_tools.get(routing_decision.strategy, [])
                    actual_used_expected = any(tool in tools_used for tool in expected)
                    
                    if actual_used_expected:
                        print("   ✅ Tool selection matches router expectation")
                    else:
                        print(f"   ❌ Tool mismatch! Expected: {expected}, Got: {tools_used}")
                        
                else:
                    print(f"   ❌ API Error: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Connection Error: {str(e)}")
                
            print("-" * 80)


async def test_router_enforcement():
    """Test how to enforce router decisions in API calls"""
    
    router = DeterministicRouter()
    query = "How much revenue at risk if Disney churns?"
    
    # Get routing decision
    decision = router.route(query)
    
    print(f"\n📋 Router Enforcement Example\n")
    print(f"Query: {query}")
    print(f"Router says: Use {decision.strategy.value}")
    
    # Create modified prompt that enforces tool selection
    enforced_prompt = f"""
MANDATORY INSTRUCTION: You MUST use the following tools for this query:
- Tool Strategy: {decision.strategy.value}
- Required Tools: {', '.join(['graph_search', 'get_entity_relationships']) if decision.strategy == RetrievalStrategy.GRAPH else 'vector_search'}

DO NOT use any other tools. This is a strict requirement.

User Query: {query}
"""
    
    print(f"\nEnforced Prompt:")
    print("-" * 40)
    print(enforced_prompt)
    print("-" * 40)


if __name__ == "__main__":
    print("Note: This test requires the SpyroSolutions API to be running on port 8058")
    print("If running remotely, use SSH port forwarding:")
    print("ssh -L 8058:localhost:8058 root@srv928466.hstgr.cloud")
    print()
    
    asyncio.run(test_spyro_with_router())
    asyncio.run(test_router_enforcement())