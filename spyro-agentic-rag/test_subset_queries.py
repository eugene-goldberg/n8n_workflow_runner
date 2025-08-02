#!/usr/bin/env python3
"""Test a subset of business questions to verify success rate"""
import json
import requests
import time
from typing import List, Dict, Tuple

# API configuration
API_URL = "http://localhost:8000/query"
API_KEY = "test_api_key_123"

# Test questions covering all categories
TEST_QUESTIONS = [
    # Revenue & Financial Performance (5 questions)
    "How much revenue will be at risk if TechCorp misses their SLA next month?",
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "Which customers generate 80% of our revenue, and what are their current risk profiles?",
    "How much revenue is at risk from customers experiencing negative events in the last quarter?",
    "What is the projected revenue impact if we miss our roadmap deadlines for committed features?",
    
    # Cost & Profitability (5 questions)
    "How much does it cost to run each product across all regions?",
    "What is the profitability margin for each product line?",
    "How do operational costs impact profitability for our top 10 customers?",
    "Which teams have the highest operational costs relative to the revenue they support?",
    "What is the cost-per-customer for each product, and how does it vary by region?",
    
    # Customer Success & Retention (5 questions)
    "What are the top 5 customers by revenue, and what are their current success scores?",
    "Which customers have declining success scores, and what events are driving the decline?",
    "How many customers have success scores below 60, and what is their combined ARR?",
    "What percentage of customers experienced negative events in the last 90 days?",
    "Which customers are at highest risk of churn based on success scores and recent events?",
    
    # Customer Commitments & Satisfaction (5 questions)
    "What are the top customer commitments, and what are the current risks to achieving them?",
    "Which features were promised to customers, and what is their delivery status?",
    "What are the top customer concerns, and what is currently being done to address them?",
    "How many customers are waiting for features currently on our roadmap?",
    "Which customers have unmet SLA commitments in the last quarter?",
    
    # Product & Feature Management (5 questions)
    "Which products have the highest customer satisfaction scores?",
    "What features drive the most value for our enterprise customers?",
    "How many customers use each product, and what is the average subscription value?",
    "Which products have the most operational issues impacting customer success?",
    "What is the adoption rate of new features released in the last 6 months?",
    
    # Risk Management (5 questions)
    "What are the top risks related to achieving Market Expansion objective?",
    "Which company objectives have the highest number of associated risks?",
    "What is the potential revenue impact of our top 5 identified risks?",
    "Which risks affect multiple objectives or customer segments?",
    "How many high-severity risks are currently without mitigation strategies?"
]

def test_query(question: str) -> Tuple[bool, str]:
    """Test a single query and return success status and answer"""
    try:
        headers = {"x-api-key": API_KEY}
        response = requests.post(
            API_URL,
            json={"question": question},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            # Check if answer is data-grounded (not generic)
            generic_indicators = [
                "I don't have",
                "not available",
                "no specific data",
                "could not find",
                "unable to find",
                "don't have access",
                "no data found"
            ]
            
            is_generic = any(indicator.lower() in answer.lower() for indicator in generic_indicators)
            
            # For some questions, check for specific data points
            if "revenue" in question.lower() and "$" not in answer and "%" not in answer:
                is_generic = True
            if "customers" in question.lower() and not any(name in answer for name in ["TechCorp", "GlobalRetail", "HealthNet", "AutoDrive"]):
                is_generic = True
            
            return not is_generic, answer
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Run subset test and calculate success rate"""
    print("Testing Subset of Business Questions")
    print("=" * 80)
    print(f"Testing {len(TEST_QUESTIONS)} questions across all categories\n")
    
    successes = 0
    category_results = {}
    current_category = ""
    
    for i, question in enumerate(TEST_QUESTIONS):
        # Determine category
        if i < 5:
            category = "Revenue & Financial Performance"
        elif i < 10:
            category = "Cost & Profitability"
        elif i < 15:
            category = "Customer Success & Retention"
        elif i < 20:
            category = "Customer Commitments & Satisfaction"
        elif i < 25:
            category = "Product & Feature Management"
        else:
            category = "Risk Management"
        
        if category != current_category:
            current_category = category
            category_results[category] = {"total": 0, "success": 0}
            print(f"\n{category}:")
            print("-" * 40)
        
        # Test query
        success, answer = test_query(question)
        status = "✓ Success" if success else "✗ Failed"
        
        category_results[category]["total"] += 1
        if success:
            successes += 1
            category_results[category]["success"] += 1
        
        print(f"[{i+1}] {question[:60]}...")
        print(f"   {status}")
        if success:
            print(f"   Answer preview: {answer[:100]}...")
        else:
            print(f"   Error: {answer}")
        
        # Small delay between queries
        time.sleep(1)
    
    # Calculate overall success rate
    success_rate = (successes / len(TEST_QUESTIONS)) * 100
    
    print("\n" + "=" * 80)
    print("RESULTS BY CATEGORY:")
    for category, results in category_results.items():
        cat_rate = (results["success"] / results["total"]) * 100
        print(f"{category}: {results['success']}/{results['total']} ({cat_rate:.1f}%)")
    
    print(f"\nOVERALL SUCCESS RATE: {successes}/{len(TEST_QUESTIONS)} ({success_rate:.1f}%)")
    
    if success_rate >= 83:
        print("✓ SUCCESS: Achieved target of >83% success rate!")
    else:
        print(f"✗ Need to improve by {83 - success_rate:.1f}% to reach target")

if __name__ == "__main__":
    main()