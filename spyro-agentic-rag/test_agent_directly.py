#!/usr/bin/env python3
"""Test the agent directly without going through the API"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_fixed import create_agent

def test_agent_directly():
    """Test the agent without the API layer"""
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    # Test query that fails via API
    question = "What percentage of our ARR is dependent on customers with success scores below 70?"
    
    print(f"Testing: {question}")
    result = agent.query(question)
    
    print(f"\nAnswer: {result['answer']}")
    print(f"\nExpected: ~20.6% (based on Neo4j data)")
    
    # Check if correct
    if "20" in result['answer'] or "20.6" in result['answer']:
        print("\n✅ SUCCESS: Agent returned correct answer")
    else:
        print("\n❌ FAILED: Agent did not return correct answer")
    
    agent.close()
    return result

if __name__ == "__main__":
    test_agent_directly()