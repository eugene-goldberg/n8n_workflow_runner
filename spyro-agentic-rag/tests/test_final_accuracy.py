#!/usr/bin/env python3
"""
Final comprehensive accuracy test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from src.agents.spyro_agent import create_agent
from src.utils.config import Config
import json
from datetime import datetime


def extract_tool_from_verbose(agent, query):
    """Extract which tool was used by capturing verbose output"""
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        agent.agent.verbose = True
        try:
            agent.query(query)
        except:
            pass
        agent.agent.verbose = False
    
    output = f.getvalue()
    
    if "Invoking: `GraphQuery`" in output:
        return "GraphQuery"
    elif "Invoking: `HybridSearch`" in output:
        return "HybridSearch"
    elif "Invoking: `VectorSearch`" in output:
        return "VectorSearch"
    return "Unknown"


def main():
    config = Config.from_env()
    agent = create_agent(config)
    
    # Comprehensive test suite
    test_cases = [
        # GraphQuery cases (10)
        ("Which customers have subscriptions over $5M?", "GraphQuery"),
        ("Count active subscriptions", "GraphQuery"),
        ("Show me all teams", "GraphQuery"),
        ("What is our total ARR?", "GraphQuery"),
        ("List all customers", "GraphQuery"),
        ("How many products do we have?", "GraphQuery"),
        ("Show risks for objectives", "GraphQuery"),
        ("Which teams support which products?", "GraphQuery"),
        ("Find customers by region", "GraphQuery"),
        ("What are TechCorp's subscription details?", "GraphQuery"),
        
        # HybridSearch cases (10)
        ("What are SpyroCloud features?", "HybridSearch"),
        ("Tell me about SpyroAI capabilities", "HybridSearch"),
        ("SpyroSecure security features", "HybridSearch"),
        ("How does SpyroCloud handle scaling?", "HybridSearch"),
        ("SpyroAI machine learning capabilities", "HybridSearch"),
        ("What makes SpyroSecure unique?", "HybridSearch"),
        ("SpyroCloud pricing model", "HybridSearch"),
        ("SpyroAI automation features", "HybridSearch"),
        ("SpyroSecure compliance capabilities", "HybridSearch"),
        ("Features of SpyroCloud platform", "HybridSearch"),
        
        # VectorSearch cases (10)
        ("What makes our products unique?", "VectorSearch"),
        ("How do we help enterprises?", "VectorSearch"),
        ("What are the benefits of our platform?", "VectorSearch"),
        ("Explain our approach to innovation", "VectorSearch"),
        ("What is our company philosophy?", "VectorSearch"),
        ("How do we ensure customer success?", "VectorSearch"),
        ("What are best practices for SaaS?", "VectorSearch"),
        ("General benefits of cloud computing", "VectorSearch"),
        ("How to achieve digital transformation?", "VectorSearch"),
        ("What defines a successful product?", "VectorSearch"),
    ]
    
    print("FINAL ACCURACY TEST - 30 Test Cases")
    print("=" * 80)
    
    results = []
    correct_count = 0
    
    # Test in batches to show progress
    for i, (query, expected) in enumerate(test_cases):
        print(f"\r[{i+1}/30] Testing...", end="", flush=True)
        
        actual = extract_tool_from_verbose(agent, query)
        is_correct = (actual == expected)
        
        if is_correct:
            correct_count += 1
        
        results.append({
            "query": query,
            "expected": expected,
            "actual": actual,
            "correct": is_correct
        })
    
    print("\n" + "=" * 80)
    
    # Calculate accuracy
    accuracy = (correct_count / len(test_cases)) * 100
    
    # Show results by category
    print("\nRESULTS BY CATEGORY:")
    print("-" * 40)
    
    for tool in ["GraphQuery", "HybridSearch", "VectorSearch"]:
        tool_results = [r for r in results if r["expected"] == tool]
        tool_correct = sum(1 for r in tool_results if r["correct"])
        tool_accuracy = (tool_correct / len(tool_results)) * 100 if tool_results else 0
        print(f"{tool}: {tool_correct}/{len(tool_results)} correct ({tool_accuracy:.0f}%)")
    
    # Show failures if any
    failures = [r for r in results if not r["correct"]]
    if failures:
        print("\nFAILURES:")
        print("-" * 40)
        for f in failures:
            print(f"Query: '{f['query']}'")
            print(f"  Expected: {f['expected']}, Got: {f['actual']}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print(f"OVERALL ACCURACY: {accuracy:.1f}% ({correct_count}/{len(test_cases)})")
    print(f"TARGET: ≥95%")
    print(f"STATUS: {'✅ PASS' if accuracy >= 95 else '❌ FAIL'}")
    print("=" * 80)
    
    # Save detailed results
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_cases),
        "correct": correct_count,
        "accuracy": accuracy,
        "pass": accuracy >= 95,
        "results": results
    }
    
    with open("final_accuracy_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: final_accuracy_report.json")
    
    agent.close()
    return accuracy >= 95


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)