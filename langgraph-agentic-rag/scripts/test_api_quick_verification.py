#!/usr/bin/env python3
"""Quick verification of API fix - test specific questions that had issues"""

import requests
import json

API_URL = "http://localhost:8000"
API_KEY = "test-key-123"

# Questions that had different grounding results
test_questions = [
    # False positives in original API (should be NOT grounded)
    (21, 'Which products have the highest customer satisfaction scores?', False),
    (26, 'How much future revenue will be at risk if [Feature X] misses its deadline by 3 months?', False),
    
    # False negatives in original API (should be grounded)
    (7, 'What is the profitability margin for each product line?', True),
    (10, 'What is the cost-per-customer for each product, and how does it vary by region?', True),
    (17, 'Which features were promised to customers, and what is their delivery status?', True),
    (25, 'What is the adoption rate of new features released in the last 6 months?', True),
    (45, 'Which teams have the highest impact on customer success scores?', False),  # Actually should be False
    (46, 'Which projects are critical for maintaining current revenue?', True),
    (57, 'Which features give us competitive advantage in each market segment?', True)
]

def test_question_via_api(question: str):
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
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("=== QUICK VERIFICATION OF API FIX ===")
    print(f"Testing {len(test_questions)} questions that had grounding issues\n")
    
    correct_count = 0
    
    for idx, question, expected_grounded in test_questions:
        print(f"\nQ{idx}: {question[:60]}...")
        print(f"Expected grounded: {expected_grounded}")
        
        result = test_question_via_api(question)
        if result:
            actual_grounded = result['metadata']['grounded']
            is_correct = actual_grounded == expected_grounded
            
            print(f"Actual grounded: {actual_grounded} {'✅' if is_correct else '❌'}")
            
            if is_correct:
                correct_count += 1
            else:
                print(f"Answer preview: {result['answer'][:150]}...")
        else:
            print("Failed to get response")
    
    accuracy = correct_count / len(test_questions) * 100
    print(f"\n{'='*60}")
    print(f"Results: {correct_count}/{len(test_questions)} correct ({accuracy:.1f}%)")
    
    if accuracy == 100:
        print("✅ All test questions now have correct grounding!")
    else:
        print(f"❌ Still have {len(test_questions) - correct_count} incorrect grounding results")

if __name__ == "__main__":
    main()