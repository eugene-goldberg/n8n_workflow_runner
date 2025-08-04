#!/usr/bin/env python3
"""Test Neo4j retrieval with spyro data"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrievers import VectorRetriever, GraphRetriever
from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_retrievers():
    """Test different retrievers with spyro data"""
    
    print("=== TESTING NEO4J RETRIEVERS ===\n")
    
    # Test 1: Vector Retriever
    print("1. Testing Vector Retriever:")
    print("-" * 50)
    try:
        vector_retriever = VectorRetriever(use_neo4j=True)
        results = await vector_retriever.retrieve("What customers have high ARR?", k=5)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results[:3]):
                print(f"\nResult {i+1} (score: {result['score']:.3f}):")
                print(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Graph Retriever
    print("\n\n2. Testing Graph Retriever:")
    print("-" * 50)
    try:
        graph_retriever = GraphRetriever()
        results = await graph_retriever.retrieve("Which customers are using SpyroCloud?", k=5)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results[:3]):
                print(f"\nResult {i+1}:")
                print(result['content'])
                if 'cypher_query' in result['metadata']:
                    print(f"Query: {result['metadata']['cypher_query']}")
        else:
            print("No results found")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Full Agent
    print("\n\n3. Testing Full Agent:")
    print("-" * 50)
    
    test_queries = [
        "What products does TechCorp use?",
        "Which teams have the highest operational costs?", 
        "What are the main risks in our projects?",
        "Show me customers with success scores below 70"
    ]
    
    try:
        agent = AgentRunner()
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 30)
            
            result = await agent.run(query)
            print(f"Answer: {result['answer'][:300]}..." if len(result['answer']) > 300 else f"Answer: {result['answer']}")
            print(f"Route: {result['metadata'].get('route')}")
            print(f"Tools used: {result['metadata'].get('tools_used')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_retrievers())