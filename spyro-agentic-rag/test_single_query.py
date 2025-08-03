#!/usr/bin/env python3
"""Test a single query with detailed analysis"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_fixed import create_agent

def test_single_query(question: str):
    """Test a single query and show detailed results"""
    
    print(f"\n{'='*80}")
    print(f"Testing: {question}")
    print(f"{'='*80}\n")
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    # Run the query
    result = agent.query(question)
    
    print("AGENT RESPONSE:")
    print(f"Answer: {result['answer']}")
    print(f"\nMetadata:")
    print(f"- Execution time: {result['metadata']['execution_time_seconds']:.2f}s")
    print(f"- Tokens used: {result['metadata']['tokens_used']}")
    print(f"- Cost: ${result['metadata']['cost_usd']:.4f}")
    
    agent.close()
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("Enter question: ")
    
    test_single_query(question)