#!/usr/bin/env python3
"""
Analyze tool selection patterns and optimize for accuracy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.spyro_agent import create_agent
from src.utils.config import Config

def analyze_misclassifications():
    """Analyze why certain queries are misclassified"""
    
    print("Tool Selection Analysis")
    print("=" * 60)
    
    # Failures from the test:
    # "What are SpyroCloud features?" - Expected HybridSearch, got VectorSearch
    # "Tell me about SpyroAI capabilities" - Expected HybridSearch, got VectorSearch
    
    print("\nMisclassified Queries:")
    print("-" * 40)
    
    misclassified = [
        {
            "query": "What are SpyroCloud features?",
            "expected": "HybridSearch (specific product + features)",
            "actual": "VectorSearch (general features question)",
            "issue": "Agent sees 'What are... features?' as conceptual"
        },
        {
            "query": "Tell me about SpyroAI capabilities",
            "expected": "HybridSearch (specific product + capabilities)",
            "actual": "VectorSearch (general capabilities question)",
            "issue": "Agent sees 'Tell me about... capabilities' as conceptual"
        }
    ]
    
    for case in misclassified:
        print(f"\nQuery: '{case['query']}'")
        print(f"Expected: {case['expected']}")
        print(f"Actual: {case['actual']}")
        print(f"Issue: {case['issue']}")
    
    print("\n\nRoot Cause Analysis:")
    print("-" * 40)
    print("The agent is correctly identifying these as 'feature/capability' questions")
    print("but not recognizing that they mention SPECIFIC PRODUCTS (SpyroCloud, SpyroAI)")
    print("which should trigger HybridSearch for better results.")
    
    print("\n\nProposed Solution:")
    print("-" * 40)
    print("1. Update HybridSearch description to emphasize specific product names")
    print("2. Update VectorSearch to de-emphasize product-specific queries")
    print("3. Add examples to tool descriptions")
    print("4. Enhance system prompt to recognize product names")


def test_current_tools():
    """Test current tool descriptions"""
    config = Config.from_env()
    agent = create_agent(config)
    
    print("\n\nCurrent Tool Descriptions:")
    print("=" * 60)
    
    for tool in agent.tools:
        print(f"\n{tool.name}:")
        print(f"{tool.description}")
    
    agent.close()


if __name__ == "__main__":
    analyze_misclassifications()
    test_current_tools()