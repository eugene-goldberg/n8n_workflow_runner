#!/usr/bin/env python3
"""Test the LangGraph agent with a single business question"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Suppress some verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langsmith").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

async def test_single_question():
    """Test agent with a single business question"""
    
    print("=== TESTING LANGGRAPH AGENT WITH SINGLE BUSINESS QUESTION ===\n")
    
    # Test question
    question = "How many customers have success scores below 60, and what is their combined ARR?"
    
    try:
        agent = AgentRunner()
        
        print(f"Question: {question}")
        print(f"{'='*80}\n")
        
        result = await agent.run(question)
        
        print(f"\n📊 Answer:")
        print(f"{result['answer']}")
        
        print(f"\n🔍 Metadata:")
        print(f"  - Route: {result['metadata'].get('route')}")
        print(f"  - Tools used: {result['metadata'].get('tools_used')}")
        print(f"  - Errors: {result['metadata'].get('error_count', 0)}")
    
    except Exception as e:
        print(f"Failed to run agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_question())