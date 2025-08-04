#!/usr/bin/env python3
"""Quick verification of grounded questions from the list"""

import requests
import json
import time

API_URL = "http://localhost:8000"
API_KEY = "test-key-123"

# Questions that were marked as grounded in Customer Health category
customer_health_questions = [
    "What are the top 5 customers by revenue, and what are their current success scores?",
    "Which customers have declining success scores, and what events are driving the decline?",
    "How many customers have success scores below 60, and what is their combined ARR?",
    "What percentage of customers experienced negative events in the last 90 days?",
    "Which customers are at highest risk of churn based on success scores and recent events?"
]

def test_question(question):
    """Test a single question through the API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {"question": question}
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['metadata']['grounded'], data['answer']
        else:
            return False, f"Error: {response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

print("Verifying Customer Health questions...")
print("="*60)

grounded_count = 0
for i, question in enumerate(customer_health_questions, 1):
    print(f"\n{i}. {question[:60]}...")
    is_grounded, answer = test_question(question)
    
    if is_grounded:
        grounded_count += 1
        print(f"   ✅ GROUNDED")
    else:
        print(f"   ❌ NOT GROUNDED")
        print(f"   Answer: {answer[:150]}...")
    
    time.sleep(1)  # Small delay between requests

print(f"\n{'='*60}")
print(f"Results: {grounded_count}/{len(customer_health_questions)} grounded")

if grounded_count < len(customer_health_questions):
    print("\n⚠️  Some questions are no longer returning grounded answers!")
    print("The grounded questions list needs to be updated.")