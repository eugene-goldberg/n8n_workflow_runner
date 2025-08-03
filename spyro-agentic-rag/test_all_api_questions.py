#!/usr/bin/env python3
"""
Test all 60 business questions through the API
"""

import requests
import json
import time
from datetime import datetime
import os

# API configuration
API_URL = "http://localhost:8000"
API_KEY = os.getenv("SPYRO_API_KEY", "test-api-key-123")

# Business questions
BUSINESS_QUESTIONS = [
    {"id": 1, "question": "What is our total ARR and how is it distributed across customer segments?"},
    {"id": 2, "question": "Which customers have success scores below 50?"},
    {"id": 3, "question": "What is the distribution of customer health scores?"},
    {"id": 4, "question": "How many customers are at risk of churning?"},
    {"id": 5, "question": "What percentage of our ARR comes from customers with low success scores?"},
    {"id": 6, "question": "Which products have the highest adoption rates?"},
    {"id": 7, "question": "What are the projected quarterly revenue trends for the next fiscal year?"},
    {"id": 8, "question": "How many active risks are unmitigated and what is their financial impact?"},
    {"id": 9, "question": "Which customers have declining success scores?"},
    {"id": 10, "question": "What is the average contract value by customer segment?"},
    {"id": 11, "question": "How many features are in each release stage?"},
    {"id": 12, "question": "What percentage of customers are at risk of churn based on multiple factors?"},
    {"id": 13, "question": "Which products have the highest adoption rates?"},
    {"id": 14, "question": "What is the distribution of customers by revenue tier?"},
    {"id": 15, "question": "How many integration issues are currently open?"},
    {"id": 16, "question": "What are the top requested features by customer segment?"},
    {"id": 17, "question": "Which teams have the highest operational costs?"},
    {"id": 18, "question": "What is the health score distribution across all customers?"},
    {"id": 19, "question": "How many customers have adopted our latest features?"},
    {"id": 20, "question": "What is the correlation between support tickets and churn risk?"},
    {"id": 21, "question": "Which customer segments generate the most ARR?"},
    {"id": 22, "question": "How many risks are associated with each objective?"},
    {"id": 23, "question": "What percentage of features are customer-requested vs internally driven?"},
    {"id": 24, "question": "Which customers have the highest number of integration issues?"},
    {"id": 25, "question": "What is the average time to value for new customers?"},
    {"id": 26, "question": "How does product adoption vary by customer size?"},
    {"id": 27, "question": "What are the most common risk categories?"},
    {"id": 28, "question": "Which objectives have the highest number of unmitigated risks?"},
    {"id": 29, "question": "How many customers are using deprecated features?"},
    {"id": 30, "question": "What is the success score trend over the past quarters?"},
    {"id": 31, "question": "Which teams are involved in the most projects?"},
    {"id": 32, "question": "What percentage of our roadmap items are delayed?"},
    {"id": 33, "question": "How many customers would be impacted by each potential service disruption?"},
    {"id": 34, "question": "What is the adoption rate of features released in the last quarter?"},
    {"id": 35, "question": "Which customer segments have the highest support ticket volume?"},
    {"id": 36, "question": "How many objectives are at risk due to dependencies?"},
    {"id": 37, "question": "What is the distribution of project priorities?"},
    {"id": 38, "question": "Which products contribute most to recurring revenue?"},
    {"id": 39, "question": "How many customers have success scores below 60?"},
    {"id": 40, "question": "What are the most critical unmitigated risks by impact?"},
    {"id": 41, "question": "Which features have the lowest adoption rates?"},
    {"id": 42, "question": "How many cross-functional dependencies exist between teams?"},
    {"id": 43, "question": "What percentage of customers are on the latest product version?"},
    {"id": 44, "question": "Which objectives are blocked by external dependencies?"},
    {"id": 45, "question": "How many high-value customers are at risk?"},
    {"id": 46, "question": "What is the average health score by product line?"},
    {"id": 47, "question": "Which customer segments have the highest growth rate?"},
    {"id": 48, "question": "How many features are blocked by technical debt?"},
    {"id": 49, "question": "What percentage of risks have approved mitigation plans?"},
    {"id": 50, "question": "Which teams have the most skill gaps?"},
    {"id": 51, "question": "How does customer satisfaction correlate with product adoption?"},
    {"id": 52, "question": "What percentage of revenue is recurring vs one-time?"},
    {"id": 53, "question": "Which marketing channels have the highest ROI?"},
    {"id": 54, "question": "How many customers have multiple products deployed?"},
    {"id": 55, "question": "What is the impact of seasonality on revenue projections?"},
    {"id": 56, "question": "Which features drive the most customer value?"},
    {"id": 57, "question": "How many objectives are dependent on external vendors?"},
    {"id": 58, "question": "What percentage of customers have executive sponsors?"},
    {"id": 59, "question": "Which products have the highest support burden?"},
    {"id": 60, "question": "How many customers are in each lifecycle stage?"}
]

def test_query(question_data):
    """Test a single query through the API"""
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "question": question_data["question"]
    }
    
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
            
            # Check if answer is grounded (contains specific data)
            grounded_indicators = [
                # Numbers
                any(char.isdigit() for char in answer),
                # Percentages
                "%" in answer,
                # Customer/Product/Team names
                any(name in answer for name in ["TechCorp", "FinanceHub", "SpyroCloud", "Engineering Team"]),
                # Financial values
                "$" in answer,
                # Specific metrics
                any(term in answer.lower() for term in ["arr", "score", "risk", "revenue", "cost"])
            ]
            
            is_grounded = sum(grounded_indicators) >= 2 and len(answer) > 50
            
            # Check for generic responses
            generic_phrases = [
                "I don't have specific data",
                "I cannot find",
                "No results found",
                "Unable to retrieve",
                "error processing"
            ]
            
            is_generic = any(phrase.lower() in answer.lower() for phrase in generic_phrases)
            
            return {
                "success": True,
                "grounded": is_grounded and not is_generic,
                "answer": answer,
                "execution_time": metadata.get("execution_time_seconds", 0),
                "error": None
            }
        else:
            return {
                "success": False,
                "grounded": False,
                "answer": None,
                "execution_time": 0,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "grounded": False,
            "answer": None,
            "execution_time": 0,
            "error": str(e)
        }

def main():
    print("TESTING ALL 60 BUSINESS QUESTIONS THROUGH API")
    print("=" * 80)
    print(f"API URL: {API_URL}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Check API health first
    try:
        health_response = requests.get(f"{API_URL}/health")
        if health_response.status_code != 200:
            print("ERROR: API is not healthy!")
            return
        print("✓ API is healthy")
    except Exception as e:
        print(f"ERROR: Cannot connect to API: {e}")
        return
    
    print("\nTesting Questions...")
    print("-" * 80)
    
    results = []
    grounded_count = 0
    
    for question in BUSINESS_QUESTIONS:
        print(f"\nQ{question['id']}: {question['question']}")
        
        # Test the query
        result = test_query(question)
        
        if result["success"]:
            if result["grounded"]:
                print(f"✅ GROUNDED - {result['execution_time']:.1f}s")
                print(f"   Answer preview: {result['answer'][:150]}...")
                grounded_count += 1
            else:
                print(f"❌ GENERIC - {result['execution_time']:.1f}s")
                print(f"   Answer: {result['answer'][:150]}...")
        else:
            print(f"❌ FAILED - {result['error']}")
        
        results.append({
            "id": question["id"],
            "question": question["question"],
            "grounded": result["grounded"],
            "success": result["success"],
            "answer": result["answer"],
            "error": result["error"],
            "execution_time": result["execution_time"]
        })
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_queries = len(BUSINESS_QUESTIONS)
    successful_queries = sum(1 for r in results if r["success"])
    failed_queries = sum(1 for r in results if not r["success"])
    
    print(f"\nTotal Queries: {total_queries}")
    print(f"Successful: {successful_queries}")
    print(f"Failed: {failed_queries}")
    print(f"Grounded: {grounded_count}")
    print(f"Generic: {successful_queries - grounded_count}")
    print(f"\nSuccess Rate: {(grounded_count/total_queries)*100:.1f}%")
    
    # Failed queries analysis
    if failed_queries > 0:
        print(f"\n{failed_queries} FAILED QUERIES:")
        for r in results:
            if not r["success"]:
                print(f"  Q{r['id']}: {r['error']}")
    
    # Generic responses analysis
    generic_queries = [r for r in results if r["success"] and not r["grounded"]]
    if generic_queries:
        print(f"\n{len(generic_queries)} GENERIC RESPONSES:")
        for r in generic_queries:
            print(f"  Q{r['id']}: {r['question']}")
    
    # Save detailed results
    with open('api_test_results.json', 'w') as f:
        json.dump({
            "test_date": datetime.now().isoformat(),
            "summary": {
                "total": total_queries,
                "successful": successful_queries,
                "failed": failed_queries,
                "grounded": grounded_count,
                "generic": successful_queries - grounded_count,
                "success_rate": (grounded_count/total_queries)*100
            },
            "results": results
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: api_test_results.json")

if __name__ == "__main__":
    main()