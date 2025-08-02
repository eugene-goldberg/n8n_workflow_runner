#!/usr/bin/env python3
"""Test critical business queries to verify fixes"""

import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000/query"

# Critical test queries
test_queries = [
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "How much revenue will be at risk if TechCorp misses their SLA next month?",
    "Which customers generate 80% of our revenue, and what are their current risk profiles?",
    "Which customer commitments are at high risk?",
    "What are the satisfaction scores for each product?",
    "Which teams have the highest operational costs relative to revenue?"
]

def test_query(query):
    """Test a single query"""
    try:
        response = requests.post(
            API_URL,
            json={"question": query},
            headers={
                "Content-Type": "application/json",
                "x-api-key": "spyro-secret-key-123"  # Add API key header
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer provided")
            
            # Check if answer contains actual data
            has_data = any([
                "$" in answer,  # Currency values
                "%" in answer,  # Percentages
                any(name in answer for name in ["TechCorp", "GlobalRetail", "SpyroCloud", "SpyroAI"]),
                any(word in answer.lower() for word in ["score", "revenue", "cost", "team"])
            ])
            
            status = "✅ SUCCESS" if has_data else "⚠️  GENERIC"
            print(f"\n{status}: {query}")
            print(f"Answer preview: {answer[:200]}...")
            
            return has_data
        else:
            print(f"\n❌ ERROR: {query}")
            print(f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ EXCEPTION: {query}")
        print(f"Error: {str(e)}")
        return False

def main():
    print("Testing Critical Business Queries")
    print("=" * 80)
    
    successful = 0
    total = len(test_queries)
    
    for query in test_queries:
        if test_query(query):
            successful += 1
        time.sleep(1)  # Small delay between queries
    
    print(f"\n{'-' * 80}")
    print(f"Results: {successful}/{total} queries returned data-grounded answers")
    print(f"Success Rate: {(successful/total)*100:.1f}%")

if __name__ == "__main__":
    main()