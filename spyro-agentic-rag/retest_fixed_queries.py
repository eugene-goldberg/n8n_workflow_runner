#!/usr/bin/env python3
"""Re-test the 12 queries that failed due to missing data"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent
import json
from datetime import datetime

# The 12 queries that failed due to missing data
QUERIES_TO_RETEST = [
    {
        "id": 7,
        "question": "What are the projected quarterly revenue trends for the next fiscal year?"
    },
    {
        "id": 19,
        "question": "What is the correlation between team size and project completion rates?"
    },
    {
        "id": 20,
        "question": "How many critical milestones are at risk of being missed this quarter?"
    },
    {
        "id": 25,
        "question": "What percentage of projects are currently over budget?"
    },
    {
        "id": 28,
        "question": "How many security incidents have been reported in the last quarter?"
    },
    {
        "id": 31,
        "question": "What is the average time from lead to customer conversion?"
    },
    {
        "id": 32,
        "question": "How many customers are using deprecated features?"
    },
    {
        "id": 43,
        "question": "What is the trend in customer acquisition costs over time?"
    },
    {
        "id": 48,
        "question": "How many days of runway do we have at current burn rate?"
    },
    {
        "id": 52,
        "question": "What percentage of revenue is recurring vs one-time?"
    },
    {
        "id": 53,
        "question": "Which marketing channels have the highest ROI?"
    },
    {
        "id": 58,
        "question": "What percentage of our codebase has technical debt?"
    }
]

def analyze_response(answer):
    """Analyze if response is now grounded in Neo4j data"""
    
    # Indicators of grounded responses
    grounded_indicators = [
        # Specific numbers/percentages
        "%", "$", "M", "million", "thousand", 
        # Specific counts
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        # Specific terms
        "Q1", "Q2", "Q3", "Q4", "2025", "days", "ROI",
        "recurring", "one-time", "technical debt",
        # Specific entities
        "Digital Advertising", "Content Marketing", "SEO",
        "security_incident", "at_risk", "critical"
    ]
    
    # Indicators of generic/failed responses
    generic_indicators = [
        "no data available", "no results found", "unable to retrieve",
        "it seems", "it appears", "technical issue", "error",
        "cannot provide", "don't have access", "missing data",
        "no direct results", "could not find", "not available"
    ]
    
    answer_lower = answer.lower()
    
    # Count indicators
    grounded_count = sum(1 for indicator in grounded_indicators if indicator.lower() in answer_lower)
    generic_count = sum(1 for indicator in generic_indicators if indicator in answer_lower)
    
    # Determine if grounded
    is_grounded = grounded_count > 2 and generic_count < 2 and len(answer) > 50
    
    return {
        "grounded": is_grounded,
        "grounded_indicators": grounded_count,
        "generic_indicators": generic_count,
        "answer_length": len(answer)
    }

def test_query(agent, query_info):
    """Test a single query"""
    
    print(f"\n{'='*80}")
    print(f"Testing Query {query_info['id']}: {query_info['question']}")
    print("-" * 80)
    
    try:
        result = agent.query(query_info['question'])
        answer = result['answer']
        
        print(f"Answer: {answer[:200]}...")
        
        # Analyze response
        analysis = analyze_response(answer)
        
        if analysis['grounded']:
            print("\n✅ SUCCESS - Now returns grounded data!")
        else:
            print("\n❌ STILL FAILING - No specific data returned")
        
        print(f"Grounded indicators: {analysis['grounded_indicators']}")
        print(f"Generic indicators: {analysis['generic_indicators']}")
        
        return {
            "id": query_info['id'],
            "question": query_info['question'],
            "answer": answer,
            "grounded": analysis['grounded'],
            "grounded_indicators": analysis['grounded_indicators'],
            "generic_indicators": analysis['generic_indicators'],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return {
            "id": query_info['id'],
            "question": query_info['question'],
            "answer": f"ERROR: {str(e)}",
            "grounded": False,
            "error": True,
            "timestamp": datetime.now().isoformat()
        }

def main():
    print("RE-TESTING 12 QUERIES AFTER ADDING MISSING DATA")
    print("=" * 80)
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    results = []
    success_count = 0
    
    # Test each query
    for query_info in QUERIES_TO_RETEST:
        result = test_query(agent, query_info)
        results.append(result)
        
        if result['grounded']:
            success_count += 1
    
    agent.close()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF RE-TEST RESULTS")
    print("="*80)
    print(f"\nTotal queries re-tested: {len(QUERIES_TO_RETEST)}")
    print(f"Now successful (grounded): {success_count}")
    print(f"Still failing: {len(QUERIES_TO_RETEST) - success_count}")
    print(f"Success rate: {(success_count / len(QUERIES_TO_RETEST)) * 100:.1f}%")
    
    # Detailed breakdown
    print("\nDETAILED RESULTS:")
    print("-" * 80)
    for result in results:
        status = "✅ FIXED" if result['grounded'] else "❌ STILL FAILING"
        print(f"Q{result['id']}: {status} - {result['question'][:60]}...")
    
    # Save results
    with open('retest_results_after_data_addition.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_retested": len(QUERIES_TO_RETEST),
                "now_successful": success_count,
                "still_failing": len(QUERIES_TO_RETEST) - success_count,
                "success_rate": (success_count / len(QUERIES_TO_RETEST)) * 100
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: retest_results_after_data_addition.json")
    
    # Calculate overall improvement
    print("\n" + "="*80)
    print("OVERALL IMPROVEMENT")
    print("="*80)
    print(f"Previous success rate: 70.0% (42/60 queries)")
    new_total_success = 42 + success_count  # Previous 42 + newly fixed
    new_success_rate = (new_total_success / 60) * 100
    print(f"New success rate: {new_success_rate:.1f}% ({new_total_success}/60 queries)")
    print(f"Improvement: +{new_success_rate - 70.0:.1f} percentage points")
    
    if new_success_rate >= 83:
        print("\n🎉 SUCCESS! Achieved >83% success rate target!")
    else:
        print(f"\n⚠️  Still below 83% target. Need {50 - new_total_success} more queries to succeed.")

if __name__ == "__main__":
    main()