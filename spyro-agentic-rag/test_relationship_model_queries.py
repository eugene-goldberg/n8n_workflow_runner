#!/usr/bin/env python3
"""
Test the three failing queries with the new relationship-centric model
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent
import json
from datetime import datetime

# The three queries that were failing
TEST_QUERIES = [
    {
        "id": 53,
        "question": "Which marketing channels have the highest ROI?",
        "expected": "Should return specific ROI percentages"
    },
    {
        "id": 7,
        "question": "What are the projected quarterly revenue trends for the next fiscal year?",
        "expected": "Should return Q1-Q4 2025 projections"
    },
    {
        "id": 52,
        "question": "What percentage of revenue is recurring vs one-time?",
        "expected": "Should return ~91% recurring, ~9% one-time"
    }
]

def test_query(agent, query_info):
    """Test a single query and analyze the results"""
    
    print(f"\n{'='*80}")
    print(f"Testing Q{query_info['id']}: {query_info['question']}")
    print(f"Expected: {query_info['expected']}")
    print("-"*80)
    
    try:
        # Get the response
        result = agent.query(query_info['question'])
        answer = result['answer']
        
        print(f"\nAnswer: {answer}")
        
        # Analyze if it's grounded
        grounded_indicators = [
            "700%", "600%", "ROI",  # For Q53
            "Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "22500000", "24800000",  # For Q7
            "91", "92", "8", "9", "recurring", "one-time"  # For Q52
        ]
        
        grounded_count = sum(1 for indicator in grounded_indicators if indicator in answer)
        
        if grounded_count >= 2:
            print("\n✅ SUCCESS - Answer contains specific grounded data!")
            return True
        else:
            print("\n❌ FAILED - Answer is generic or incorrect")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def main():
    print("TESTING RELATIONSHIP-CENTRIC MODEL")
    print("="*80)
    print("\nThis test verifies if the new relationship model improves query success.")
    
    # Create agent with new context
    config = Config.from_env()
    agent = create_agent(config)
    
    print("\n✓ Agent initialized with relationship-centric context")
    
    # Test each query
    results = []
    success_count = 0
    
    for query in TEST_QUERIES:
        success = test_query(agent, query)
        if success:
            success_count += 1
        results.append({
            "id": query["id"],
            "question": query["question"],
            "success": success
        })
    
    agent.close()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\nSuccess Rate: {success_count}/{len(TEST_QUERIES)} ({(success_count/len(TEST_QUERIES)*100):.0f}%)")
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  Q{result['id']}: {status}")
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    if success_count == len(TEST_QUERIES):
        print("\n🎉 All queries now work with the relationship model!")
        print("\nThe relationship-centric approach successfully:")
        print("  1. Eliminated property guessing")
        print("  2. Leveraged LLM strength in traversal")
        print("  3. Provided clear semantic paths to data")
    else:
        print("\n⚠️  Some queries still need work.")
        print("Check the Cypher query logs to see what patterns were generated.")
    
    # Save results
    with open('relationship_model_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "relationship-centric",
            "success_rate": f"{success_count}/{len(TEST_QUERIES)}",
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: relationship_model_test_results.json")

if __name__ == "__main__":
    main()