#!/usr/bin/env python3
"""
Test direct graph queries to verify the data is accessible
"""

import requests
import json

API_URL = "http://localhost:8000"
API_KEY = "spyro-secret-key-123"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Test queries that should work with the actual graph structure
test_queries = [
    {
        "question": "Show me all customers and their subscription ARR values",
        "use_cypher": True,
        "explanation": "Direct graph query for Customer->Subscription"
    },
    {
        "question": "What are the subscription plans and ARR for each customer?",
        "use_cypher": True,
        "explanation": "Customer->SaaSSubscription traversal"
    },
    {
        "question": "List all teams and their responsibilities",
        "use_cypher": True,
        "explanation": "Team nodes query"
    },
    {
        "question": "What are the operational costs for all projects?",
        "use_cypher": True,
        "explanation": "Project->OperationalCost traversal"
    },
    {
        "question": "Show me customer success scores",
        "use_cypher": True,
        "explanation": "Customer->CustomerSuccessScore"
    }
]

print("Testing Graph Queries with Actual Structure")
print("=" * 60)

for i, query_info in enumerate(test_queries, 1):
    print(f"\nQuery {i}: {query_info['question']}")
    print(f"Purpose: {query_info['explanation']}")
    print("-" * 60)
    
    payload = {
        "question": query_info["question"],
        "use_cypher": query_info["use_cypher"],
        "top_k": 10
    }
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"Answer: {result['answer'][:300]}...")
        print(f"Context items: {result['context_items']}")
        print(f"Processing time: {result['processing_time_ms']:.2f}ms")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
print("Direct Cypher Query Test")
print("=" * 60)

# Let's also test with a direct Cypher query format
direct_cypher_query = {
    "question": "MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription) RETURN c.name as customer, s.plan as plan, s.ARR as arr",
    "use_cypher": True
}

print(f"\nDirect Cypher: {direct_cypher_query['question']}")
response = requests.post(f"{API_URL}/query", json=direct_cypher_query, headers=headers)
result = response.json()
print(f"Answer: {result['answer'][:500]}...")
print(f"Context items: {result['context_items']}")