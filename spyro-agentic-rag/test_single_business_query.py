#!/usr/bin/env python3
"""Test a single business query and append results to tracking file"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent

# All 60 business questions
BUSINESS_QUESTIONS = [
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "Which customers are at high risk due to low product adoption?",
    "What is the impact on revenue if we lose our top 3 enterprise customers?",
    "How many customers have success scores below 60, and what is their combined ARR?",
    "What percentage of customers experienced negative events in the last 90 days?",
    "Which customers are at highest risk of churn based on success scores and recent events?",
    "What are the projected quarterly revenue trends for the next fiscal year?",
    "Which teams have the highest operational costs relative to their output?",
    "How many active risks are unmitigated, and what is their potential financial impact?",
    "What is the customer retention rate across different product lines?",
    "Which product features have the highest usage but lowest satisfaction scores?",
    "What is the average time to resolve critical customer issues by product?",
    "How many customers would be affected if SpyroCloud experiences an outage?",
    "What is the distribution of customers across different industry verticals?",
    "Which regions have the highest concentration of at-risk customers?",
    "What percentage of our customer base uses multiple products?",
    "How much ARR is at risk from customers with upcoming renewal dates?",
    "Which customers have the highest lifetime value?",
    "What is the correlation between team size and project completion rates?",
    "How many critical milestones are at risk of being missed this quarter?",
    "What is the average customer acquisition cost by product line?",
    "Which features are most commonly requested but not yet implemented?",
    "What is the ratio of operational costs to revenue for each product?",
    "How many customers have exceeded their usage limits in the past month?",
    "What percentage of projects are currently over budget?",
    "Which teams have the highest employee satisfaction scores?",
    "What is the average deal size for new enterprise customers?",
    "How many security incidents have been reported in the last quarter?",
    "What is the customer satisfaction trend over the past year?",
    "Which competitive threats pose the highest risk to our market share?",
    "What is the average time from lead to customer conversion?",
    "How many customers are using deprecated features?",
    "What percentage of our revenue comes from the top 10% of customers?",
    "Which SLAs are most frequently violated?",
    "What is the cost per customer for each support tier?",
    "How many expansion opportunities exist within our current customer base?",
    "What is the success rate of our customer onboarding process?",
    "Which product integrations are most valuable to customers?",
    "What is the average revenue per employee across different departments?",
    "How many customers have not been contacted in the last 60 days?",
    "What percentage of features are actively used by more than 50% of customers?",
    "Which customers have the highest support ticket volume?",
    "What is the trend in customer acquisition costs over time?",
    "How many high-value opportunities are in the pipeline?",
    "What percentage of customers are promoters (NPS score 9-10)?",
    "Which product updates have had the most positive impact on retention?",
    "What is the distribution of contract values across customer segments?",
    "How many days of runway do we have at current burn rate?",
    "Which customers are underutilizing their subscriptions?",
    "What is the ratio of customer success managers to customers?",
    "How many critical dependencies exist in our technology stack?",
    "What percentage of revenue is recurring vs one-time?",
    "Which marketing channels have the highest ROI?",
    "What is the average resolution time for different risk categories?",
    "How many customers have custom contractual terms?",
    "What is the relationship between product usage and renewal probability?",
    "Which teams are most effective at meeting their OKRs?",
    "What percentage of our codebase has technical debt?",
    "How many customers would benefit from upgrading their plan?",
    "What is the geographic distribution of our revenue?"
]

def analyze_response(question, answer):
    """Analyze if response is grounded in Neo4j data or generic"""
    
    # Indicators of grounded responses
    grounded_indicators = [
        # Specific numbers/percentages
        "%", "$", "M", "million", "thousand", "customers", "teams", "products",
        # Specific entity names
        "TechCorp", "SpyroCloud", "SpyroAI", "SpyroSecure", "GlobalRetail", 
        "FinanceHub", "StartupXYZ", "RetailPlus", "EduTech", "HealthTech",
        # Specific metrics
        "ARR", "revenue", "score", "operational cost", "adoption rate",
        # Specific counts
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    ]
    
    # Indicators of generic/failed responses
    generic_indicators = [
        "no data available", "no results found", "unable to retrieve",
        "it seems", "it appears", "technical issue", "error",
        "cannot provide", "don't have access", "missing data",
        "no direct results", "could not find", "not available",
        "typically", "generally", "usually", "commonly"
    ]
    
    answer_lower = answer.lower()
    
    # Count indicators
    grounded_count = sum(1 for indicator in grounded_indicators if indicator.lower() in answer_lower)
    generic_count = sum(1 for indicator in generic_indicators if indicator in answer_lower)
    
    # Determine if grounded
    is_grounded = grounded_count > 2 and generic_count < 2 and len(answer) > 50
    
    return {
        "grounded": is_grounded,
        "grounded_indicators": grounded_count,
        "generic_indicators": generic_count,
        "answer_length": len(answer)
    }

def test_single_query(query_number):
    """Test a single query by number (1-60)"""
    
    if query_number < 1 or query_number > 60:
        print("Query number must be between 1 and 60")
        return
    
    question = BUSINESS_QUESTIONS[query_number - 1]
    
    print(f"\n{'='*80}")
    print(f"Testing Query #{query_number}/60")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print("-" * 80)
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    try:
        start_time = time.time()
        result = agent.query(question)
        execution_time = time.time() - start_time
        
        answer = result['answer']
        print(f"\nFull Answer:")
        print(answer)
        
        # Analyze response
        analysis = analyze_response(question, answer)
        
        print(f"\n{'='*80}")
        print("ANALYSIS")
        print(f"{'='*80}")
        
        if analysis['grounded']:
            print("✅ GROUNDED - Contains specific Neo4j data")
        else:
            print("❌ GENERIC - No specific data found")
        
        print(f"Grounded indicators found: {analysis['grounded_indicators']}")
        print(f"Generic indicators found: {analysis['generic_indicators']}")
        print(f"Answer length: {analysis['answer_length']} characters")
        print(f"Execution time: {execution_time:.2f} seconds")
        
        # Save result
        result_data = {
            "id": query_number,
            "question": question,
            "answer": answer,
            "grounded": analysis['grounded'],
            "grounded_indicators": analysis['grounded_indicators'],
            "generic_indicators": analysis['generic_indicators'],
            "answer_length": analysis['answer_length'],
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Append to results file
        results_file = "60_queries_results_progressive.json"
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                all_results = json.load(f)
        else:
            all_results = {"results": []}
        
        # Update or append result
        existing_index = next((i for i, r in enumerate(all_results["results"]) if r["id"] == query_number), None)
        if existing_index is not None:
            all_results["results"][existing_index] = result_data
        else:
            all_results["results"].append(result_data)
        
        # Sort by ID
        all_results["results"].sort(key=lambda x: x["id"])
        
        # Calculate summary
        grounded_count = sum(1 for r in all_results["results"] if r["grounded"])
        total_count = len(all_results["results"])
        
        all_results["summary"] = {
            "total_tested": total_count,
            "grounded": grounded_count,
            "generic": total_count - grounded_count,
            "success_rate": (grounded_count / total_count * 100) if total_count > 0 else 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Save updated results
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n✅ Result saved to {results_file}")
        print(f"Progress: {total_count}/60 queries tested")
        print(f"Current success rate: {all_results['summary']['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        # Save error result
        result_data = {
            "id": query_number,
            "question": question,
            "answer": f"ERROR: {str(e)}",
            "grounded": False,
            "error": True,
            "execution_time": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Append error to results
        results_file = "60_queries_results_progressive.json"
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                all_results = json.load(f)
        else:
            all_results = {"results": []}
        
        all_results["results"].append(result_data)
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
    
    finally:
        agent.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_number = int(sys.argv[1])
    else:
        print("Usage: python test_single_business_query.py <query_number>")
        print("Example: python test_single_business_query.py 1")
        print("\nAvailable queries (1-60):")
        for i, q in enumerate(BUSINESS_QUESTIONS, 1):
            print(f"{i}. {q}")
        sys.exit(1)
    
    test_single_query(query_number)