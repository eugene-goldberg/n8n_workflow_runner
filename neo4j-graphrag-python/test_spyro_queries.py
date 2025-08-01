#!/usr/bin/env python3
"""
Test queries against SpyroSolutions Semantic Model
Shows how the hybrid RAG system works with the semantic model
"""

import requests
import json
import time

API_URL = "http://localhost:8000"

# Business-focused queries based on the semantic model
BUSINESS_QUERIES = [
    {
        "question": "What products does SpyroSolutions offer and what are their SLAs?",
        "use_cypher": False,
        "category": "Product Information"
    },
    {
        "question": "Which customers are using SpyroCloud Platform?",
        "use_cypher": True,
        "category": "Customer Relationships"
    },
    {
        "question": "What is the total Annual Recurring Revenue (ARR)?",
        "use_cypher": True,
        "category": "Financial Metrics"
    },
    {
        "question": "Which customers have high risk levels and why?",
        "use_cypher": True,
        "category": "Risk Assessment"
    },
    {
        "question": "What are the customer success scores for each customer?",
        "use_cypher": False,
        "category": "Customer Success"
    },
    {
        "question": "Which projects are contributing to profitability?",
        "use_cypher": True,
        "category": "Project Impact"
    },
    {
        "question": "What features are on the product roadmap?",
        "use_cypher": True,
        "category": "Product Roadmap"
    },
    {
        "question": "Which teams are responsible for which products?",
        "use_cypher": True,
        "category": "Team Assignments"
    },
    {
        "question": "What are the operational costs for active projects?",
        "use_cypher": False,
        "category": "Cost Analysis"
    },
    {
        "question": "What events have affected our customers?",
        "use_cypher": True,
        "category": "Event Tracking"
    }
]


def test_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
    except:
        print("❌ API is not responding")
        return False
    return False


def execute_query(question: str, use_cypher: bool = False):
    """Execute a single query"""
    payload = {
        "question": question,
        "use_cypher": use_cypher
    }
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}


def main():
    """Run all test queries"""
    print("SpyroSolutions Semantic Model Query Test")
    print("=" * 80)
    
    # Check API health
    if not test_api_health():
        print("\nPlease start the API first with: python3 run_spyro_api.py")
        return
    
    print("\nExecuting business queries...")
    print("=" * 80)
    
    for query_info in BUSINESS_QUERIES:
        print(f"\nCategory: {query_info['category']}")
        print(f"Question: {query_info['question']}")
        print(f"Using Cypher: {'Yes' if query_info['use_cypher'] else 'No'}")
        
        # Execute query
        start_time = time.time()
        result = execute_query(query_info['question'], query_info['use_cypher'])
        elapsed = time.time() - start_time
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Answer: {result.get('answer', 'No answer')}")
            print(f"   Context items: {result.get('context_items', 0)}")
            print(f"   Retriever: {result.get('retriever_type', 'unknown')}")
            print(f"   Time: {elapsed:.2f}s")
        
        print("-" * 80)
    
    # Summary
    print("\n" + "=" * 80)
    print("Query Test Complete!")
    print("\nNote: If answers are not retrieving context, ensure:")
    print("1. The knowledge graph was properly built")
    print("2. Vector and fulltext indexes exist")
    print("3. Chunks have the correct labels (__Chunk__)")


if __name__ == "__main__":
    main()