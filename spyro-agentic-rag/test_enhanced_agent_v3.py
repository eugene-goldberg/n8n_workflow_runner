#!/usr/bin/env python3
"""Test the enhanced agent v3 with previously failed queries"""

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent

# Test queries that previously failed
TEST_QUERIES = [
    {
        "id": 1,
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "expected": "~20.6%",
        "previous_issue": "Agent couldn't find customers with low scores"
    },
    {
        "id": 2,
        "question": "Which customers are at high risk due to low product adoption?",
        "expected": "List with specific adoption metrics",
        "previous_issue": "Generic response without metrics"
    },
    {
        "id": 5,
        "question": "What percentage of customers experienced negative events in the last 90 days?",
        "expected": "Percentage based on event data",
        "previous_issue": "Returned 100% incorrectly, events lack dates"
    },
    {
        "id": 7,
        "question": "What are the projected quarterly revenue trends for the next fiscal year?",
        "expected": "Quarterly projections",
        "previous_issue": "Couldn't find subscription values"
    },
    {
        "id": 9,
        "question": "How many active risks are unmitigated, and what is their potential financial impact?",
        "expected": "10 active risks, $20.4M impact",
        "previous_issue": "Used wrong status and property names"
    },
    {
        "id": 10,
        "question": "What is the customer retention rate across different product lines?",
        "expected": "Retention rates by product",
        "previous_issue": "Looked for non-existent 'retained' property"
    },
    {
        "id": 11,
        "question": "Which product features have the highest usage but lowest satisfaction scores?",
        "expected": "Features with adoption rates",
        "previous_issue": "Wrong relationships, couldn't adapt"
    }
]

def test_enhanced_agent():
    """Test the enhanced agent with improved context"""
    
    print("=" * 80)
    print("Testing Enhanced Agent v3 with Comprehensive Data Model Context")
    print("=" * 80)
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    results = []
    
    for test in TEST_QUERIES:
        print(f"\n\nTest #{test['id']}: {test['question']}")
        print(f"Expected: {test['expected']}")
        print(f"Previous Issue: {test['previous_issue']}")
        print("-" * 80)
        
        try:
            # Run the query
            result = agent.query(test['question'])
            
            print(f"Answer: {result['answer']}")
            print(f"\nMetadata:")
            print(f"- Execution time: {result['metadata']['execution_time_seconds']}s")
            print(f"- Schema sources: {result['metadata'].get('schema_sources', {})}")
            
            # Simple success check
            answer_lower = result['answer'].lower()
            is_success = (
                "no results" not in answer_lower and
                "error" not in answer_lower and
                "seems there" not in answer_lower and
                "not available" not in answer_lower and
                len(result['answer']) > 50  # Not a generic short response
            )
            
            results.append({
                "id": test['id'],
                "question": test['question'],
                "success": is_success,
                "answer_length": len(result['answer']),
                "execution_time": result['metadata']['execution_time_seconds']
            })
            
            print(f"\nResult: {'✅ SUCCESS' if is_success else '❌ FAILED'}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "id": test['id'],
                "question": test['question'],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r.get('success', False))
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"Total Queries: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate < 80:
        print("\n⚠️  Success rate is below 80%. Check cypher_queries.log for generated queries.")
    else:
        print("\n✅ Success rate meets or exceeds target!")
    
    # Save results
    with open("test_results_v3.json", "w") as f:
        json.dump({
            "timestamp": str(datetime.now()),
            "success_rate": success_rate,
            "results": results
        }, f, indent=2)
    
    agent.close()
    return success_rate

if __name__ == "__main__":
    from datetime import datetime
    success_rate = test_enhanced_agent()
    
    print("\n📝 Check cypher_queries.log for all generated Cypher queries")
    print("📊 Detailed results saved to test_results_v3.json")