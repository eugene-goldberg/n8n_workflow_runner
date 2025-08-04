#!/usr/bin/env python3
"""Verify a sample of questions across all categories"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
from src.agents.main_agent import AgentRunner
import logging

logging.basicConfig(level=logging.WARNING)
for logger in ["httpx", "langsmith", "neo4j", "openai", "src"]:
    logging.getLogger(logger).setLevel(logging.ERROR)

# Sample 2 questions from each category
SAMPLE_QUESTIONS = [
    # Revenue Risk Analysis (Q1-5)
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "How much revenue is at risk from customers experiencing negative events in the last quarter?",
    
    # Cost & Profitability (Q6-10)
    "What is the profitability margin for each product line?",
    "What is the cost-per-customer for each product, and how does it vary by region?",
    
    # Customer Health (Q11-15)
    "How many customers have success scores below 60, and what is their combined ARR?",
    "Which customers are at highest risk of churn based on success scores and recent events?",
    
    # Customer Commitments (Q16-20)
    "What are the top customer concerns, and what is currently being done to address them?",
    "Which customers have unmet SLA commitments in the last quarter?",
    
    # Product Performance (Q21-25)
    "Which products have the highest customer satisfaction scores?",
    "Which products have the most operational issues impacting customer success?",
    
    # Roadmap & Delivery (Q26-30)
    "What percentage of roadmap items are currently behind schedule?",
    "How many customer commitments depend on roadmap items at risk?",
    
    # Strategic Risk (Q31-35)
    "Which company objectives have the highest number of associated risks?",
    "How many high-severity risks are currently without mitigation strategies?",
    
    # Operational Risk (Q36-40)
    "How do operational risks correlate with customer success scores?",
    "What percentage of projects are at risk of missing deadlines?",
    
    # Team Performance (Q41-45)
    "Which teams support the most revenue-generating products?",
    "What is the revenue-per-team-member for each department?",
    
    # Project Delivery (Q46-50)
    "How many projects are blocked by operational constraints?",
    "What is the success rate of projects by team and product area?",
    
    # Growth & Expansion (Q51-55)
    "Which customer segments offer the highest growth potential?",
    "Which objectives are most critical for achieving our growth targets?",
    
    # Competitive Positioning (Q56-60)
    "How do our SLAs compare to industry standards by product?",
    "Which customer segments are we best positioned to serve profitably?"
]

def is_grounded(answer: str) -> bool:
    """Check if answer is grounded in data"""
    negative = ["no results", "not available", "no specific", "sorry", 
                "unable to", "did not return", "no information"]
    return not any(n in answer.lower() for n in negative)

async def verify_questions():
    """Verify sample questions"""
    print("=== VERIFYING SAMPLE QUESTIONS ACROSS ALL CATEGORIES ===")
    print(f"Testing {len(SAMPLE_QUESTIONS)} questions (2 per category)\n")
    
    agent = AgentRunner()
    results = []
    grounded = 0
    
    for i, question in enumerate(SAMPLE_QUESTIONS, 1):
        category = ["Revenue Risk", "Cost & Prof", "Customer Health", "Commitments",
                   "Product Perf", "Roadmap", "Strategic Risk", "Op Risk",
                   "Team Perf", "Project", "Growth", "Competitive"][(i-1)//2]
        
        print(f"\n[{category}] Q{i}: {question[:60]}...")
        
        try:
            start = time.time()
            response = await agent.run(question)
            elapsed = time.time() - start
            
            answer = response.get('answer', '')
            grounded_status = is_grounded(answer)
            if grounded_status:
                grounded += 1
            
            print(f"Answer preview: {answer[:150]}...")
            print(f"Grounded: {'✅ YES' if grounded_status else '❌ NO'} ({elapsed:.1f}s)")
            
            results.append({
                'category': category,
                'question': question,
                'grounded': grounded_status
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)[:50]}")
            results.append({
                'category': category,
                'question': question,
                'grounded': False
            })
        
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    # By category
    category_stats = {}
    for r in results:
        cat = r['category']
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'grounded': 0}
        category_stats[cat]['total'] += 1
        if r['grounded']:
            category_stats[cat]['grounded'] += 1
    
    for cat, stats in category_stats.items():
        rate = stats['grounded'] / stats['total'] * 100
        print(f"{cat:<15} {stats['grounded']}/{stats['total']} ({rate:.0f}%)")
    
    overall_rate = grounded / len(SAMPLE_QUESTIONS) * 100
    print(f"\nOverall: {grounded}/{len(SAMPLE_QUESTIONS)} grounded ({overall_rate:.1f}%)")
    
    # Extrapolate to full 60
    estimated_total = int(60 * overall_rate / 100)
    print(f"\nEstimated for all 60 questions: ~{estimated_total}/60 ({overall_rate:.1f}%)")

if __name__ == "__main__":
    asyncio.run(verify_questions())