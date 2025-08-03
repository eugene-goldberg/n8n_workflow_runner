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

# Business questions
BUSINESS_QUESTIONS = {
    1: "What is our total ARR and how is it distributed across customer segments?",
    2: "Which customers have success scores below 50?",
    3: "What is the distribution of customer health scores?",
    4: "How many customers are at risk of churning?",
    5: "What percentage of our ARR comes from customers with low success scores?",
    6: "Which products have the highest adoption rates?",
    7: "What are the projected quarterly revenue trends for the next fiscal year?",
    8: "How many active risks are unmitigated and what is their financial impact?",
    9: "Which customers have declining success scores?",
    10: "What is the average contract value by customer segment?",
    11: "How many features are in each release stage?",
    12: "What percentage of customers are at risk of churn based on multiple factors?",
    13: "Which products have the highest adoption rates?",
    14: "What is the distribution of customers by revenue tier?",
    15: "How many integration issues are currently open?",
    16: "What are the top requested features by customer segment?",
    17: "Which teams have the highest operational costs?",
    18: "What is the health score distribution across all customers?",
    19: "How many customers have adopted our latest features?",
    20: "What is the correlation between support tickets and churn risk?",
    21: "Which customer segments generate the most ARR?",
    22: "How many risks are associated with each objective?",
    23: "What percentage of features are customer-requested vs internally driven?",
    24: "Which customers have the highest number of integration issues?",
    25: "What is the average time to value for new customers?",
    26: "How does product adoption vary by customer size?",
    27: "What are the most common risk categories?",
    28: "Which objectives have the highest number of unmitigated risks?",
    29: "How many customers are using deprecated features?",
    30: "What is the success score trend over the past quarters?",
    31: "Which teams are involved in the most projects?",
    32: "What percentage of our roadmap items are delayed?",
    33: "How many customers would be impacted by each potential service disruption?",
    34: "What is the adoption rate of features released in the last quarter?",
    35: "Which customer segments have the highest support ticket volume?",
    36: "How many objectives are at risk due to dependencies?",
    37: "What is the distribution of project priorities?",
    38: "Which products contribute most to recurring revenue?",
    39: "How many customers have success scores below 60?",
    40: "What are the most critical unmitigated risks by impact?",
    41: "Which features have the lowest adoption rates?",
    42: "How many cross-functional dependencies exist between teams?",
    43: "What percentage of customers are on the latest product version?",
    44: "Which objectives are blocked by external dependencies?",
    45: "How many high-value customers are at risk?",
    46: "What is the average health score by product line?",
    47: "Which customer segments have the highest growth rate?",
    48: "How many features are blocked by technical debt?",
    49: "What percentage of risks have approved mitigation plans?",
    50: "Which teams have the most skill gaps?",
    51: "How does customer satisfaction correlate with product adoption?",
    52: "What percentage of revenue is recurring vs one-time?",
    53: "Which marketing channels have the highest ROI?",
    54: "How many customers have multiple products deployed?",
    55: "What is the impact of seasonality on revenue projections?",
    56: "Which features drive the most customer value?",
    57: "How many objectives are dependent on external vendors?",
    58: "What percentage of customers have executive sponsors?",
    59: "Which products have the highest support burden?",
    60: "How many customers are in each lifecycle stage?"
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