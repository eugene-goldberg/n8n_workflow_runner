#!/usr/bin/env python3
"""
Run the Hybrid RAG Demo
"""

import asyncio
import sys
from hybrid_rag_implementation import test_queries

async def main():
    """Run the test queries"""
    print("Starting Hybrid RAG Demo...")
    print("This will:")
    print("1. Build a knowledge graph from business data")
    print("2. Create vector and fulltext indexes")
    print("3. Test different retriever types")
    print("-" * 50)
    
    try:
        await test_queries()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())