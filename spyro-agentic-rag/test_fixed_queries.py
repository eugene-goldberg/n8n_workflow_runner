#!/usr/bin/env python3
"""Test fixed queries with new data"""
import requests
import json
import time

# Previously failing queries that should now work
TEST_QUERIES = [
    "Which features were promised to customers, and what is their delivery status?",
    "What is the adoption rate of new features released in the last 6 months?",
    "What are the top risks related to achieving Market Expansion objective?",
    "Which company objectives have the highest number of associated risks?",
    "What are the top customer concerns, and what is currently being done to address them?",
    "Which roadmap items are critical for customer retention?",
    "What percentage of roadmap items are currently behind schedule?",
    "Which teams are responsible for delayed roadmap items?"
]

def test_query(question):
    """Test a single query"""
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": question},
            headers={"x-api-key": "spyro-secret-key-123"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "No answer")
        else:
            return f"Error: HTTP {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("Testing Fixed Queries")
    print("=" * 80)
    
    success_count = 0
    
    for i, question in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}] {question}")
        print("-" * 40)
        
        answer = test_query(question)
        
        # Check if answer is specific (not generic)
        generic_indicators = [
            "no specific entries",
            "not directly available",
            "unable to find",
            "no data found",
            "might suggest",
            "seems there are no",
            "couldn't find specific",
            "if you have more"
        ]
        
        is_generic = any(indicator in answer.lower() for indicator in generic_indicators)
        
        if not is_generic and len(answer) > 50:
            print("✅ SUCCESS - Specific answer received")
            success_count += 1
            print(f"Answer preview: {answer[:200]}...")
        else:
            print("❌ FAILED - Generic or empty response")
            print(f"Answer: {answer[:200]}...")
        
        time.sleep(2)
    
    print(f"\n\nSUMMARY: {success_count}/{len(TEST_QUERIES)} queries successful")
    print(f"Success Rate: {(success_count/len(TEST_QUERIES)*100):.1f}%")

if __name__ == "__main__":
    main()