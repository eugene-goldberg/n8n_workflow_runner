#!/usr/bin/env python3
"""
Test a single business question through the API
"""

import requests
import json
import sys
import os

# API configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("SPYRO_API_KEY", "spyro-secret-key-123")

# Business questions - matching the 71.7% success rate test
BUSINESS_QUESTIONS = {
    1: "What percentage of our ARR is dependent on customers with success scores below 70?",
    2: "Which customers are at high risk due to low product adoption?",
    3: "What is the impact on revenue if we lose our top 3 enterprise customers?",
    4: "How many customers have success scores below 60, and what is their combined ARR?",
    5: "What percentage of customers experienced negative events in the last 90 days?",
    6: "Which customers are at highest risk of churn based on success scores and recent events?",
    7: "What are the projected quarterly revenue trends for the next fiscal year?",
    8: "Which teams have the highest operational costs relative to their output?",
    9: "How many active risks are unmitigated, and what is their potential financial impact?",
    10: "What is the customer retention rate across different product lines?",
    11: "Which product features have the highest usage but lowest satisfaction scores?",
    12: "What is the average time to resolve critical customer issues by product?",
    13: "How many customers would be affected if SpyroCloud experiences an outage?",
    14: "What is the distribution of customers across different industry verticals?",
    15: "Which regions have the highest concentration of at-risk customers?",
    16: "What percentage of our customer base uses multiple products?",
    17: "How much ARR is at risk from customers with upcoming renewal dates?",
    18: "Which customers have the highest lifetime value?",
    19: "What is the correlation between team size and project completion rates?",
    20: "How many critical milestones are at risk of being missed this quarter?",
    21: "What is the average customer acquisition cost by product line?",
    22: "Which features are most commonly requested but not yet implemented?",
    23: "What is the ratio of operational costs to revenue for each product?",
    24: "How many customers have exceeded their usage limits in the past month?",
    25: "What percentage of projects are currently over budget?",
    26: "Which teams have the highest employee satisfaction scores?",
    27: "What is the average deal size for new enterprise customers?",
    28: "How many security incidents have been reported in the last quarter?",
    29: "What is the customer satisfaction trend over the past year?",
    30: "Which competitive threats pose the highest risk to our market share?",
    31: "What is the average time from lead to customer conversion?",
    32: "How many customers are using deprecated features?",
    33: "What percentage of our revenue comes from the top 10% of customers?",
    34: "Which SLAs are most frequently violated?",
    35: "What is the cost per customer for each support tier?",
    36: "How many expansion opportunities exist within our current customer base?",
    37: "What is the success rate of our customer onboarding process?",
    38: "Which product integrations are most valuable to customers?",
    39: "What is the average revenue per employee across different departments?",
    40: "How many customers have not been contacted in the last 60 days?",
    41: "What percentage of features are actively used by more than 50% of customers?",
    42: "Which customers have the highest support ticket volume?",
    43: "What is the trend in customer acquisition costs over time?",
    44: "How many high-value opportunities are in the pipeline?",
    45: "What percentage of customers are promoters (NPS score 9-10)?",
    46: "Which product updates have had the most positive impact on retention?",
    47: "What is the distribution of contract values across customer segments?",
    48: "How many days of runway do we have at current burn rate?",
    49: "Which customers are underutilizing their subscriptions?",
    50: "What is the ratio of customer success managers to customers?",
    51: "How many critical dependencies exist in our technology stack?",
    52: "What percentage of revenue is recurring vs one-time?",
    53: "Which marketing channels have the highest ROI?",
    54: "What is the average resolution time for different risk categories?",
    55: "How many customers have custom contractual terms?",
    56: "What is the relationship between product usage and renewal probability?",
    57: "Which teams are most effective at meeting their OKRs?",
    58: "What percentage of our codebase has technical debt?",
    59: "How many customers would benefit from upgrading their plan?",
    60: "What is the geographic distribution of our revenue?"
}

def test_query(question_id):
    """Test a single query through the API"""
    
    if question_id not in BUSINESS_QUESTIONS:
        print(f"Invalid question ID: {question_id}")
        return
    
    question = BUSINESS_QUESTIONS[question_id]
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "question": question
    }
    
    print(f"Q{question_id}: {question}")
    print("-" * 80)
    
    try:
        # Make API request
        response = requests.post(
            f"{API_URL}/query",
            headers=headers,
            json=payload,
            timeout=120  # 2 minute timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            metadata = result.get("metadata", {})
            
            print(f"Status: SUCCESS")
            print(f"Execution Time: {metadata.get('execution_time_seconds', 0):.1f}s")
            print(f"\nAnswer:\n{answer}")
            
            # Check if answer is grounded
            grounded_indicators = [
                any(char.isdigit() for char in answer),
                "%" in answer,
                any(name in answer for name in ["TechCorp", "FinanceHub", "SpyroCloud", "Engineering"]),
                "$" in answer,
                any(term in answer.lower() for term in ["arr", "score", "risk", "revenue", "cost"])
            ]
            
            is_grounded = sum(grounded_indicators) >= 2 and len(answer) > 50
            
            generic_phrases = [
                "I don't have specific data",
                "I cannot find",
                "No results found",
                "Unable to retrieve",
                "error processing"
            ]
            
            is_generic = any(phrase.lower() in answer.lower() for phrase in generic_phrases)
            
            if is_grounded and not is_generic:
                print(f"\n✅ GROUNDED - Answer contains specific data from Neo4j")
            else:
                print(f"\n❌ GENERIC - Answer does not contain specific grounded data")
                
        else:
            print(f"Status: FAILED")
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Status: ERROR")
        print(f"Error: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_single_api_question.py <question_id>")
        print(f"Question IDs: 1-{len(BUSINESS_QUESTIONS)}")
        sys.exit(1)
    
    try:
        question_id = int(sys.argv[1])
        test_query(question_id)
    except ValueError:
        print("Error: Question ID must be a number")
        sys.exit(1)

if __name__ == "__main__":
    main()