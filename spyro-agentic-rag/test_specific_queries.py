#!/usr/bin/env python3
"""Test specific queries to verify the fix"""

import requests
import json

API_URL = "http://localhost:8000/query"
API_KEY = "spyro-secret-key-123"

def test_query(question):
    """Test a single query"""
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}")
    
    response = requests.post(
        API_URL,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json={"question": question}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Answer: {data['answer']}")
        print(f"\nMetadata:")
        print(f"- Execution Time: {data['metadata']['execution_time_seconds']}s")
        print(f"- Tokens Used: {data['metadata']['tokens_used']}")
        print(f"- Schemas Accessed: {data['metadata'].get('schemas_accessed', 'N/A')}")
    else:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)

# Test key queries
test_queries = [
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "What are the top 5 customers by revenue, and what are their current success scores?",
    "How much revenue will be at risk if TechCorp misses their SLA next month?",
    "Which customers generate 80% of our revenue, and what are their current risk profiles?"
]

for query in test_queries:
    test_query(query)