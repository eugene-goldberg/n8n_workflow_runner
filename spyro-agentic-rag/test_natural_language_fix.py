#!/usr/bin/env python3
"""Test that the agent uses natural language with tools, not Cypher queries"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent

def test_natural_language_queries():
    """Test that agent passes natural language to tools"""
    
    print("Testing Natural Language Tool Usage")
    print("=" * 80)
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    # Test query
    question = "What percentage of our ARR is dependent on customers with success scores below 70?"
    
    print(f"\nQuestion: {question}")
    print("-" * 80)
    
    # Clear the log first
    if os.path.exists('cypher_queries.log'):
        with open('cypher_queries.log', 'a') as f:
            f.write("\n\n" + "="*80 + "\n")
            f.write("NATURAL LANGUAGE TEST START\n")
            f.write("="*80 + "\n\n")
    
    # Run query
    result = agent.query(question)
    
    print(f"\nAnswer: {result['answer'][:200]}...")
    
    # Wait a moment for logs to flush
    time.sleep(1)
    
    # Check the log to see what was passed to GraphQuery
    print("\nChecking cypher_queries.log for tool invocations...")
    
    with open('cypher_queries.log', 'r') as f:
        log_content = f.read()
        
    # Find the last GraphQuery invocation
    last_section = log_content.split("=== GraphQuery Tool Invoked ===")[-1]
    
    if "Agent Query:" in last_section:
        agent_query_line = [line for line in last_section.split('\n') if "Agent Query:" in line][0]
        agent_query = agent_query_line.split("Agent Query: ", 1)[1]
        
        print(f"\nAgent passed to GraphQuery tool: {agent_query[:100]}...")
        
        # Check if it's Cypher or natural language
        if any(keyword in agent_query.upper() for keyword in ['MATCH', 'WHERE', 'RETURN', ':CUSTOMER', '-[:']) :
            print("\n❌ ISSUE: Agent is still passing Cypher queries to the tool!")
            print("The agent should pass natural language questions, not Cypher.")
        else:
            print("\n✅ SUCCESS: Agent is passing natural language to the tool!")
    
    agent.close()

if __name__ == "__main__":
    test_natural_language_queries()