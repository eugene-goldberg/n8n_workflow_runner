#!/usr/bin/env python3
"""Test the dual-schema compatible Spyro RAG agent"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.spyro_agent_compatible import create_agent
from utils.config import Config

# Load environment variables
load_dotenv()

def test_dual_schema_queries():
    """Test queries that should work with both schemas"""
    
    # Create agent
    config = Config()
    agent = create_agent(config)
    
    print("=== TESTING DUAL-SCHEMA COMPATIBLE AGENT ===\n")
    
    # Test queries
    test_queries = [
        # Basic entity queries
        "Show me all customers",
        "List customers with their subscription values",
        "Which customers have subscriptions over $5M?",
        
        # New entities from LlamaIndex
        "Tell me about InnovateTech Solutions",
        "What is the subscription value for Global Manufacturing Corp?",
        
        # Mixed queries
        "Count all customers by source (original vs new)",
        "Show me all teams and their products",
        "What are the risks for all customers?",
        
        # Aggregation queries
        "What is our total ARR?",
        "Count products by type",
        
        # Feature queries
        "What are SpyroCloud features?",
        "Tell me about SpyroAI capabilities"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: {query}")
        print('='*60)
        
        try:
            result = agent.query(query)
            print(f"\nAnswer: {result['answer']}")
            print(f"\nMetadata:")
            print(f"- Execution time: {result['metadata']['execution_time_seconds']:.2f}s")
            print(f"- Tokens used: {result['metadata'].get('tokens_used', 'N/A')}")
            print(f"- Schema support: {result['metadata'].get('schema_support', 'N/A')}")
        except Exception as e:
            print(f"\nError: {e}")
    
    # Clean up
    agent.close()
    print("\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_dual_schema_queries()