#!/usr/bin/env python3
"""Test enhanced vector search"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrievers.enhanced_vector import EnhancedVectorRetriever
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_enhanced_vector():
    """Test enhanced vector search functionality"""
    
    print("=== TESTING ENHANCED VECTOR SEARCH ===\n")
    
    # Initialize retriever
    retriever = EnhancedVectorRetriever()
    
    # Test queries
    test_queries = [
        ("customer health", None),
        ("revenue risk", None),
        ("product features", {"entity_type": "PRODUCT"}),
        ("team performance", {"entity_type": "TEAM"}),
        ("negative events", None)
    ]
    
    for query, filters in test_queries:
        print(f"\nQuery: '{query}'")
        if filters:
            print(f"Filters: {filters}")
        print("-" * 50)
        
        try:
            results = await retriever.retrieve(query, k=3, filters=filters)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\nResult {i}:")
                    if isinstance(result, dict):
                        print(f"Score: {result.get('score', 'N/A')}")
                        print(f"Content: {result.get('content', 'N/A')}")
                        print(f"Metadata: {result.get('metadata', {})}")
                    else:
                        print(f"Score: {result.score:.4f}")
                        print(result.content)
                        print(f"Metadata: {result.metadata}")
            else:
                print("No results found")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_vector())