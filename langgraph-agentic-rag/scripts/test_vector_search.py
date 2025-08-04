#!/usr/bin/env python3
"""Test vector search directly"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrievers.vector import VectorRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_vector_search():
    """Test vector search functionality"""
    
    print("=== TESTING VECTOR SEARCH ===\n")
    
    # Initialize retriever
    retriever = VectorRetriever(use_neo4j=True)
    
    # Test queries
    test_queries = [
        "negative events",
        "customer events",
        "event impact",
        "customer success score",
        "revenue",
        "high risk"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 50)
        
        try:
            results = await retriever.retrieve(query, k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i} (score: {result.score:.4f}):")
                    print(f"Content: {result.content[:200]}...")
                    print(f"Metadata: {result.metadata}")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_vector_search())