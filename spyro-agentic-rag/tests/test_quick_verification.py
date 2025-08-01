#!/usr/bin/env python3
"""
Quick verification test for key functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from src.agents.spyro_agent import create_agent
from src.utils.config import Config

def main():
    """Quick test of key queries"""
    config = Config.from_env()
    agent = create_agent(config)
    
    test_queries = [
        ("GraphQuery test", "Which customers have subscriptions worth more than $5M?"),
        ("HybridSearch test", "What are the features of SpyroCloud?"),
        ("VectorSearch test", "What makes our products unique?"),
        ("Complex test", "Tell me about TechCorp's subscription and products they use")
    ]
    
    print("Quick Verification Test")
    print("=" * 60)
    
    for test_name, query in test_queries:
        print(f"\n{test_name}: {query}")
        print("-" * 40)
        
        start = time.time()
        result = agent.query(query)
        elapsed = time.time() - start
        
        print(f"Answer: {result['answer'][:200]}...")
        print(f"Time: {elapsed:.2f}s")
        print(f"Tokens: {result['metadata'].get('tokens_used', 'N/A')}")
        
    agent.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()