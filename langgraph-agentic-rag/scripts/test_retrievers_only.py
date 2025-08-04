#!/usr/bin/env python3
"""Test only the retrievers without the full agent"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrievers import GraphRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_graph_retriever():
    """Test graph retriever with spyro data"""
    
    print("=== TESTING GRAPH RETRIEVER ===\n")
    
    test_queries = [
        "How many customers do we have?",
        "Which customers are using SpyroCloud?",
        "What products have high adoption rates?",
        "Which teams have operational costs above 100000?",
        "Show me all high severity risks"
    ]
    
    try:
        graph_retriever = GraphRetriever()
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            print("-" * 50)
            
            results = await graph_retriever.retrieve(query, k=5)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results[:3]):
                    print(f"\nResult {i+1}:")
                    print(result['content'][:200] + "..." if len(result['content']) > 200 else result['content'])
                    if 'cypher_query' in result['metadata']:
                        print(f"Cypher: {result['metadata']['cypher_query']}")
            else:
                print("No results found")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graph_retriever())