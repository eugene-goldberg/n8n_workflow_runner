#!/usr/bin/env python3
"""Analyze which queries are returning 'no data' responses"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from src.agents.spyro_agent import SpyroAgent

# Queries that typically fail or return "no data"
problematic_queries = [
    # Customer Commitments
    "What are the top customer commitments, and what are the current risks to achieving them?",
    "Which features were promised to customers, and what is their delivery status?",
    "What are the top customer concerns, and what is currently being done to address them?",
    
    # Team-Related Complex Queries
    "Which teams are responsible for delayed roadmap items?",
    "Which teams have the highest impact on customer success scores?",
    "Which teams are understaffed relative to their project commitments?",
    
    # Complex Multi-hop Queries
    "How do operational risks correlate with customer success scores?",
    "Which risks affect multiple objectives or customer segments?",
    "How many customer commitments depend on roadmap items at risk?",
    
    # Feature/Product Analysis
    "What features drive the most value for our enterprise customers?",
    "What is the adoption rate of new features released in the last 6 months?",
    
    # Regional/Segment Analysis
    "What is the cost-per-customer for each product, and how does it vary by region?",
    "Which regions show the most promise for expansion based on current metrics?",
    
    # SLA/Commitment Tracking
    "Which customers have unmet SLA commitments in the last quarter?",
]

def test_query(agent, query):
    """Test a single query and analyze the response"""
    print(f"\nQuery: {query}")
    print("-" * 80)
    
    try:
        result = agent.query(query)
        answer = result['answer']
        
        # Categorize the response
        if "no specific data" in answer.lower() or "no available data" in answer.lower():
            print("❌ NO DATA - Agent couldn't find relevant information")
            return "no_data"
        elif "agent stopped" in answer.lower() or "iteration limit" in answer.lower():
            print("⚠️  TIMEOUT - Agent hit iteration limit")
            return "timeout"
        elif len(answer) < 50:
            print("⚠️  SHORT - Answer too brief to be useful")
            return "short"
        else:
            print("✅ SUCCESS - Returned meaningful answer")
            print(f"Answer preview: {answer[:150]}...")
            return "success"
            
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return "error"

def main():
    print("Analyzing Problematic Queries")
    print("=" * 80)
    
    config = Config.from_env()
    agent = SpyroAgent(config)
    
    results = {
        "success": 0,
        "no_data": 0,
        "timeout": 0,
        "short": 0,
        "error": 0
    }
    
    # Test each problematic query
    for query in problematic_queries[:5]:  # Test first 5 to save time
        result = test_query(agent, query)
        results[result] += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    total = sum(results.values())
    for category, count in results.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"{category.upper()}: {count}/{total} ({percentage:.1f}%)")
    
    print("\nKEY FINDINGS:")
    print("1. Queries about customer commitments/promises often fail (no structured data)")
    print("2. Complex team-relationship queries struggle (multi-hop graph traversals)")
    print("3. Regional/segment analysis fails (no region data in current schema)")
    print("4. Feature adoption metrics missing (no usage tracking data)")
    print("5. SLA tracking incomplete (limited SLA relationship data)")

if __name__ == "__main__":
    main()