#!/usr/bin/env python3
"""
Focused test on tool selection accuracy with improved prompts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from contextlib import redirect_stdout
from src.agents.spyro_agent import create_agent
from src.utils.config import Config


def test_tool_selection_accuracy():
    """Test tool selection with comprehensive test cases"""
    
    config = Config.from_env()
    agent = create_agent(config)
    
    # Comprehensive test cases
    test_cases = [
        # GraphQuery cases
        ("Which customers have subscriptions over $5M?", "GraphQuery"),
        ("Count active subscriptions", "GraphQuery"),
        ("Show me all teams", "GraphQuery"),
        ("What is our total ARR?", "GraphQuery"),
        ("List all customers", "GraphQuery"),
        ("How many products do we have?", "GraphQuery"),
        ("Show risks for objectives", "GraphQuery"),
        ("Which teams support which products?", "GraphQuery"),
        
        # HybridSearch cases (product-specific)
        ("What are SpyroCloud features?", "HybridSearch"),
        ("Tell me about SpyroAI capabilities", "HybridSearch"),
        ("SpyroSecure security features", "HybridSearch"),
        ("How does SpyroCloud handle scaling?", "HybridSearch"),
        ("SpyroAI machine learning capabilities", "HybridSearch"),
        ("What makes SpyroSecure unique?", "HybridSearch"),
        ("SpyroCloud pricing model", "HybridSearch"),
        ("Compare SpyroAI with competitors", "HybridSearch"),
        
        # VectorSearch cases (general/conceptual)
        ("What makes our products unique?", "VectorSearch"),
        ("How do we help enterprises?", "VectorSearch"),
        ("What are the benefits of our platform?", "VectorSearch"),
        ("Explain our approach to innovation", "VectorSearch"),
        ("What is our company philosophy?", "VectorSearch"),
        ("How do we ensure customer success?", "VectorSearch"),
        ("What are best practices for SaaS?", "VectorSearch"),
        ("General benefits of cloud computing", "VectorSearch"),
    ]
    
    print("Tool Selection Accuracy Test")
    print("=" * 80)
    print(f"Testing {len(test_cases)} queries...")
    print("=" * 80)
    
    results = []
    correct = 0
    
    for i, (query, expected) in enumerate(test_cases, 1):
        # Capture tool selection
        f = io.StringIO()
        with redirect_stdout(f):
            agent.agent.verbose = True
            result = agent.query(query)
            agent.agent.verbose = False
        
        output = f.getvalue()
        
        # Determine which tool was used
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
            status = "✓"
        else:
            status = "✗"
        
        results.append({
            "query": query,
            "expected": expected,
            "actual": tool_used,
            "correct": is_correct
        })
        
        print(f"{i:2d}. [{status}] {query[:50]:<50} Expected: {expected:<12} Got: {tool_used}")
    
    # Summary
    accuracy = (correct / len(test_cases)) * 100
    print("\n" + "=" * 80)
    print(f"RESULTS: {correct}/{len(test_cases)} correct")
    print(f"ACCURACY: {accuracy:.1f}%")
    print(f"TARGET: ≥95%")
    print(f"STATUS: {'PASS' if accuracy >= 95 else 'FAIL'}")
    
    # Show failures
    if accuracy < 95:
        print("\nFAILURES:")
        print("-" * 40)
        for r in results:
            if not r["correct"]:
                print(f"Query: {r['query']}")
                print(f"  Expected: {r['expected']}, Got: {r['actual']}\n")
    
    agent.close()
    return accuracy


if __name__ == "__main__":
    accuracy = test_tool_selection_accuracy()