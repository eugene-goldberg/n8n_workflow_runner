#!/usr/bin/env python3
"""Test a single question to verify agent improvements"""

import requests
import json
import sys

API_URL = "http://localhost:8000/query"
API_KEY = "spyro-secret-key-123"

def test_question(question):
    """Test a single question against the API"""
    print(f"Testing: {question}")
    print("-" * 80)
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "question": question
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: SUCCESS")
            # Try different response field names
            answer = result.get('answer') or result.get('response') or result.get('result') or str(result)
            print(f"Answer: {answer}")
            
            # Check for partial response indicators
            answer_lower = str(answer).lower()
            if 'no data' in answer_lower or 'no specific data' in answer_lower:
                print("⚠️  WARNING: Answer indicates no data found")
            elif 'it seems' in answer_lower or 'typically' in answer_lower or 'can vary' in answer_lower:
                print("⚠️  WARNING: Answer appears generic")
            else:
                print("✅ Answer contains specific data")
                
        else:
            print(f"Status: FAILED ({response.status_code})")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Status: ERROR")
        print(f"Error: {str(e)}")
    
    print()

# Test key questions that should now work
test_questions = [
    "How much does it cost to run each product across all regions?",
    "What is the cost-per-customer for SpyroAI by region?",
    "Which customer commitments are at high risk?",
    "What are the satisfaction scores for each product?",
    "Which teams have the highest costs relative to revenue?"
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test custom question
        test_question(" ".join(sys.argv[1:]))
    else:
        # Test predefined questions
        for q in test_questions:
            test_question(q)
            print("\n" + "="*80 + "\n")