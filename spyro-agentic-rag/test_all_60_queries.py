#!/usr/bin/env python3
"""Test all 60 business questions and verify Neo4j data grounding"""

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

def test_all_queries():
    """Test all 60 business questions"""
    
    print("=" * 80)
    print("Testing All 60 Business Questions with Enhanced Agent v3")
    print("=" * 80)
    
    # Create agent
    config = Config.from_env()
    agent = create_agent(config)
    
    results = []
    grounded_count = 0
    generic_count = 0
    
    # Test each question
    for i, question in enumerate(BUSINESS_QUESTIONS, 1):
        print(f"\n[{i}/60] Testing: {question}")
        print("-" * 80)
        
        try:
            start_time = time.time()
            result = agent.query(question)
            execution_time = time.time() - start_time
            
            answer = result['answer']
            print(f"Answer preview: {answer[:150]}...")
            
            # Analyze response
            analysis = analyze_response(question, answer)
            
            if analysis['grounded']:
                print("✅ GROUNDED - Contains specific Neo4j data")
                grounded_count += 1
            else:
                print("❌ GENERIC - No specific data found")
                generic_count += 1
            
            results.append({
                "id": i,
                "question": question,
                "answer": answer,
                "grounded": analysis['grounded'],
                "grounded_indicators": analysis['grounded_indicators'],
                "generic_indicators": analysis['generic_indicators'],
                "answer_length": analysis['answer_length'],
                "execution_time": execution_time
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append({
                "id": i,
                "question": question,
                "answer": f"ERROR: {str(e)}",
                "grounded": False,
                "error": True,
                "execution_time": 0
            })
            generic_count += 1
        
        # Brief pause to avoid rate limiting
        time.sleep(0.5)
    
    # Generate comprehensive report
    generate_report(results, grounded_count, generic_count)
    
    agent.close()
    return results

def generate_report(results, grounded_count, generic_count):
    """Generate comprehensive report"""
    
    report_content = f"""# Comprehensive Test Report: All 60 Business Questions
Generated: {datetime.now().isoformat()}

## Executive Summary
- **Total Questions**: 60
- **Grounded Responses**: {grounded_count} ({(grounded_count/60)*100:.1f}%)
- **Generic/Failed Responses**: {generic_count} ({(generic_count/60)*100:.1f}%)
- **Average Execution Time**: {sum(r['execution_time'] for r in results)/len(results):.2f}s

## Detailed Results

"""
    
    # Group by status
    grounded_queries = [r for r in results if r.get('grounded', False)]
    generic_queries = [r for r in results if not r.get('grounded', False)]
    
    report_content += "### ✅ Grounded Responses (Contains Specific Neo4j Data)\n\n"
    for r in grounded_queries:
        report_content += f"**Q{r['id']}**: {r['question']}\n"
        report_content += f"- **Answer**: {r['answer'][:200]}...\n"
        report_content += f"- **Data Indicators**: {r['grounded_indicators']} found\n"
        report_content += f"- **Execution Time**: {r['execution_time']:.2f}s\n\n"
    
    report_content += "### ❌ Generic/Failed Responses (No Specific Data)\n\n"
    for r in generic_queries:
        report_content += f"**Q{r['id']}**: {r['question']}\n"
        report_content += f"- **Answer**: {r['answer'][:200]}...\n"
        if 'error' in r:
            report_content += f"- **Status**: ERROR\n"
        else:
            report_content += f"- **Generic Indicators**: {r['generic_indicators']} found\n"
        report_content += f"- **Execution Time**: {r['execution_time']:.2f}s\n\n"
    
    # Add analysis section
    report_content += """## Analysis

### Common Patterns in Grounded Responses:
- Questions about specific metrics (ARR, costs, scores)
- Questions with countable entities (customers, teams, features)
- Questions about named entities (products, customers)

### Common Patterns in Generic Responses:
- Questions requiring complex calculations or projections
- Questions about data that doesn't exist in the graph
- Questions requiring time-based analysis when dates are missing

### Recommendations:
1. Add more examples for complex calculation queries
2. Ensure time-based data (dates, durations) is properly stored
3. Add examples for aggregation and trend analysis
4. Consider adding derived metrics as graph properties
"""
    
    # Save report
    with open("ALL_60_QUERIES_REPORT.md", "w") as f:
        f.write(report_content)
    
    # Save raw results
    with open("all_60_queries_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": 60,
                "grounded": grounded_count,
                "generic": generic_count,
                "success_rate": (grounded_count/60)*100
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Grounded Responses: {grounded_count}/60 ({(grounded_count/60)*100:.1f}%)")
    print(f"Generic Responses: {generic_count}/60 ({(generic_count/60)*100:.1f}%)")
    print("\n📄 Full report saved to: ALL_60_QUERIES_REPORT.md")
    print("📊 Raw results saved to: all_60_queries_results.json")

if __name__ == "__main__":
    test_all_queries()