#!/usr/bin/env python3
"""
Test individual components to identify issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.agents.spyro_agent import create_agent
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging(__name__, format_type="console")


def test_graph_query():
    """Test Text2Cypher directly"""
    print("\n=== Testing Text2Cypher Retriever ===")
    
    config = Config.from_env()
    agent = create_agent(config)
    
    # Test the Text2Cypher retriever directly
    retriever = agent.text2cypher_retriever
    
    test_queries = [
        "Which customers have subscriptions worth more than $5M?",
        "Show me all customers",
        "What is the total revenue?",
        "List all products"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = retriever.search(query_text=query)
            if result.items:
                print(f"Found {len(result.items)} results:")
                for item in result.items[:3]:
                    print(f"  - {item.content}")
            else:
                print("No results found")
                
            # Show the generated Cypher query if available
            if hasattr(result, 'metadata') and result.metadata:
                if 'cypher' in result.metadata:
                    print(f"Generated Cypher: {result.metadata['cypher']}")
                    
        except Exception as e:
            print(f"Error: {e}")
    
    agent.close()


def test_vector_search():
    """Test Vector search directly"""
    print("\n=== Testing Vector Retriever ===")
    
    config = Config.from_env()
    agent = create_agent(config)
    
    # Test the Vector retriever directly
    rag = agent.vector_rag
    
    test_queries = [
        "What are the features of SpyroCloud?",
        "Tell me about security",
        "How does SpyroAI work?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = rag.search(query_text=query, retriever_config={"top_k": 3})
            print(f"Answer: {result.answer[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    agent.close()


def test_tool_functions():
    """Test the tool functions directly"""
    print("\n=== Testing Tool Functions ===")
    
    config = Config.from_env()
    agent = create_agent(config)
    
    # Get the tools
    tools = {tool.name: tool for tool in agent.tools}
    
    # Test GraphQuery tool
    print("\n1. Testing GraphQuery tool:")
    graph_tool = tools['GraphQuery']
    result = graph_tool.func("Which customers have subscriptions worth more than $5M?")
    print(f"Result: {result}")
    
    # Test HybridSearch tool
    print("\n2. Testing HybridSearch tool:")
    hybrid_tool = tools['HybridSearch']
    result = hybrid_tool.func("What are SpyroCloud features?")
    print(f"Result: {result[:200]}...")
    
    # Test VectorSearch tool
    print("\n3. Testing VectorSearch tool:")
    vector_tool = tools['VectorSearch']
    result = vector_tool.func("What makes our products unique?")
    print(f"Result: {result[:200]}...")
    
    agent.close()


def main():
    """Run all component tests"""
    print("Testing Individual Components")
    print("=" * 60)
    
    # Test each component
    test_graph_query()
    test_vector_search()
    test_tool_functions()
    
    print("\n" + "=" * 60)
    print("Component testing complete!")


if __name__ == "__main__":
    main()