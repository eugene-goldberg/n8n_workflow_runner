#!/usr/bin/env python3
"""
Fast accuracy test - only tests the problematic cases
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from contextlib import redirect_stdout
from src.agents.spyro_agent import create_agent
from src.utils.config import Config


def test_critical_cases():
    """Test only the critical cases that were failing"""
    
    config = Config.from_env()
    agent = create_agent(config)
    
    # Focus on the problematic cases
    test_cases = [
        # Previously failing HybridSearch cases
        ("What are SpyroCloud features?", "HybridSearch"),
        ("Tell me about SpyroAI capabilities", "HybridSearch"),
        ("SpyroSecure security features", "HybridSearch"),
        ("How does SpyroCloud handle scaling?", "HybridSearch"),
        
        # Control cases that should still work
        ("Which customers have subscriptions over $5M?", "GraphQuery"),
        ("What makes our products unique?", "VectorSearch"),
        ("Show me all teams", "GraphQuery"),
        ("How do we help enterprises?", "VectorSearch"),
    ]
    
    print("Critical Tool Selection Test")
    print("=" * 60)
    
    results = []
    correct = 0
    
    for query, expected in test_cases:
        print(f"\nTesting: {query}")
        
        # Capture tool selection
        f = io.StringIO()
        with redirect_stdout(f):
            agent.agent.verbose = True
            try:
                result = agent.query(query)
            except Exception as e:
                print(f"Error: {e}")
                continue
            finally:
                agent.agent.verbose = False
        
        output = f.getvalue()
        
        # Quick parse for tool
        tool_used = "Unknown"
        if "Invoking: `GraphQuery`" in output:
            tool_used = "GraphQuery"
        elif "Invoking: `HybridSearch`" in output:
            tool_used = "HybridSearch"
        elif "Invoking: `VectorSearch`" in output:
            tool_used = "VectorSearch"
        
        is_correct = (tool_used == expected)
        if is_correct:
            correct += 1
            print(f"✓ Correct: {tool_used}")
        else:
            print(f"✗ Expected {expected}, got {tool_used}")
    
    accuracy = (correct / len(test_cases)) * 100
    print(f"\nAccuracy: {accuracy:.1f}% ({correct}/{len(test_cases)})")
    print(f"Status: {'PASS' if accuracy >= 95 else 'NEEDS IMPROVEMENT'}")
    
    agent.close()
    return accuracy


if __name__ == "__main__":
    test_critical_cases()