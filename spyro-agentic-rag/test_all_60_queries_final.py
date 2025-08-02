#!/usr/bin/env python3
"""Final test of all 60 business questions"""
import requests
import json
import time
from typing import List, Dict, Tuple

# All 60 business questions
BUSINESS_QUESTIONS = [
    # REVENUE & FINANCIAL PERFORMANCE
    ("Revenue Risk Analysis", [
        "How much revenue will be at risk if TechCorp misses their SLA next month?",
        "What percentage of our ARR is dependent on customers with success scores below 70?",
        "Which customers generate 80% of our revenue, and what are their current risk profiles?",
        "How much revenue is at risk from customers experiencing negative events in the last quarter?",
        "What is the projected revenue impact if we miss our roadmap deadlines for committed features?"
    ]),
    ("Cost & Profitability", [
        "How much does it cost to run each product across all regions?",
        "What is the profitability margin for each product line?",
        "How do operational costs impact profitability for our top 10 customers?",
        "Which teams have the highest operational costs relative to the revenue they support?",
        "What is the cost-per-customer for each product, and how does it vary by region?"
    ]),
    
    # CUSTOMER SUCCESS & RETENTION
    ("Customer Health", [
        "What are the top 5 customers by revenue, and what are their current success scores?",
        "Which customers have declining success scores, and what events are driving the decline?",
        "How many customers have success scores below 60, and what is their combined ARR?",
        "What percentage of customers experienced negative events in the last 90 days?",
        "Which customers are at highest risk of churn based on success scores and recent events?"
    ]),
    ("Customer Commitments & Satisfaction", [
        "What are the top customer commitments, and what are the current risks to achieving them?",
        "Which features were promised to customers, and what is their delivery status?",
        "What are the top customer concerns, and what is currently being done to address them?",
        "How many customers are waiting for features currently on our roadmap?",
        "Which customers have unmet SLA commitments in the last quarter?"
    ]),
    
    # PRODUCT & FEATURE MANAGEMENT
    ("Product Performance", [
        "Which products have the highest customer satisfaction scores?",
        "What features drive the most value for our enterprise customers?",
        "How many customers use each product, and what is the average subscription value?",
        "Which products have the most operational issues impacting customer success?",
        "What is the adoption rate of new features released in the last 6 months?"
    ]),
    ("Roadmap & Delivery Risk", [
        "How much future revenue will be at risk if Multi-region deployment misses its deadline by 3 months?",
        "Which roadmap items are critical for customer retention?",
        "What percentage of roadmap items are currently behind schedule?",
        "Which teams are responsible for delayed roadmap items?",
        "How many customer commitments depend on roadmap items at risk?"
    ]),
    
    # RISK MANAGEMENT
    ("Strategic Risk Assessment", [
        "What are the top risks related to achieving Market Expansion objective?",
        "Which company objectives have the highest number of associated risks?",
        "What is the potential revenue impact of our top 5 identified risks?",
        "Which risks affect multiple objectives or customer segments?",
        "How many high-severity risks are currently without mitigation strategies?"
    ]),
    ("Operational Risk", [
        "Which teams are understaffed relative to their project commitments?",
        "What operational risks could impact product SLAs?",
        "Which products have the highest operational risk exposure?",
        "How do operational risks correlate with customer success scores?",
        "What percentage of projects are at risk of missing deadlines?"
    ]),
    
    # TEAM & RESOURCE MANAGEMENT
    ("Team Performance", [
        "Which teams support the most revenue-generating products?",
        "What is the revenue-per-team-member for each department?",
        "Which teams are working on the most critical customer commitments?",
        "How are teams allocated across products and projects?",
        "Which teams have the highest impact on customer success scores?"
    ]),
    ("Project Delivery", [
        "Which projects are critical for maintaining current revenue?",
        "What percentage of projects are delivering on schedule?",
        "Which projects have dependencies that could impact multiple products?",
        "How many projects are blocked by operational constraints?",
        "What is the success rate of projects by team and product area?"
    ]),
    
    # STRATEGIC PLANNING
    ("Growth & Expansion", [
        "Which customer segments offer the highest growth potential?",
        "What products have the best profitability-to-cost ratio for scaling?",
        "Which regions show the most promise for expansion based on current metrics?",
        "What features could we develop to increase customer success scores?",
        "Which objectives are most critical for achieving our growth targets?"
    ]),
    ("Competitive Positioning", [
        "How do our SLAs compare to industry standards by product?",
        "Which features give us competitive advantage in each market segment?",
        "What operational improvements would most impact customer satisfaction?",
        "How can we reduce operational costs while maintaining service quality?",
        "Which customer segments are we best positioned to serve profitably?"
    ])
]

GENERIC_INDICATORS = [
    "it seems there are no specific",
    "no specific entries in the knowledge graph",
    "not directly available",
    "unable to find specific",
    "no data found",
    "couldn't find specific",
    "no recorded",
    "might indicate",
    "this might suggest",
    "currently recorded as 0",
    "search did not return specific",
    "no specific data",
    "data is not directly linked",
    "not explicitly documented",
    "if you have more specific",
    "please let me know",
    "i can try another approach",
    "wasn't able to retrieve",
    "issue retrieving"
]

def test_query(question: str) -> Tuple[bool, str]:
    """Test a single query and return (is_specific, answer)"""
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": question},
            headers={"x-api-key": "spyro-secret-key-123"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            
            # Check if answer is generic
            answer_lower = answer.lower()
            is_generic = any(indicator in answer_lower for indicator in GENERIC_INDICATORS)
            
            return not is_generic, answer
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Run all tests and analyze results"""
    print("Testing All 60 Business Questions - Final Run")
    print("=" * 80)
    
    all_results = []
    generic_questions = []
    total_questions = 0
    successful_questions = 0
    
    for category, questions in BUSINESS_QUESTIONS:
        print(f"\n{category}:")
        print("-" * 40)
        
        for question in questions:
            total_questions += 1
            print(f"\n[{total_questions}] {question}")
            
            is_specific, answer = test_query(question)
            
            if is_specific:
                print("✅ SUCCESS")
                successful_questions += 1
            else:
                print("❌ GENERIC")
                generic_questions.append({
                    "category": category,
                    "question": question,
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer
                })
            
            all_results.append({
                "category": category,
                "question": question,
                "is_specific": is_specific,
                "answer": answer
            })
            
            time.sleep(1)
    
    # Summary
    success_rate = (successful_questions / total_questions) * 100
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total Questions: {total_questions}")
    print(f"Specific Answers: {successful_questions}")
    print(f"Generic Responses: {len(generic_questions)}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 83:
        print("\n🎉 SUCCESS: Achieved target of 83% or higher!")
    else:
        print(f"\n⚠️  Below target: {83 - success_rate:.1f}% more needed")
    
    # Save results
    with open("final_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total": total_questions,
                "specific": successful_questions,
                "generic": len(generic_questions),
                "success_rate": success_rate
            },
            "all_results": all_results,
            "generic_questions": generic_questions
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: final_test_results.json")

if __name__ == "__main__":
    main()