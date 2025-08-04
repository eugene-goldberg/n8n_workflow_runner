#!/usr/bin/env python3
"""Test improvements with key business questions"""

import sys
import os

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
from typing import List, Dict, Any

from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("langsmith").setLevel(logging.ERROR)
logging.getLogger("neo4j").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)

# Key questions that previously failed
TEST_QUESTIONS = [
    # Revenue Risk Analysis
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "Which customers generate 80% of our revenue, and what are their current risk profiles?",
    
    # Cost & Profitability  
    "How do operational costs impact profitability for our top 10 customers?",
    "Which teams have the highest operational costs relative to the revenue they support?",
    
    # Customer Health
    "Which customers have declining success scores, and what events are driving the decline?",
    "What percentage of customers experienced negative events in the last 90 days?",
    "Which customers are at highest risk of churn based on success scores and recent events?",
    
    # Customer Commitments
    "What are the top customer commitments, and what are the current risks to achieving them?",
    "Which features were promised to customers, and what is their delivery status?",
    "How many customers are waiting for features currently on our roadmap?",
    "Which customers have unmet SLA commitments in the last quarter?",
    
    # Product Performance
    "How many customers use each product, and what is the average subscription value?",
    "Which products have the most operational issues impacting customer success?",
    "What is the adoption rate of new features released in the last 6 months?",
    
    # Roadmap & Delivery
    "What percentage of roadmap items are currently behind schedule?",
    
    # Strategic Risk
    "Which company objectives have the highest number of associated risks?",
    "Which risks affect multiple objectives or customer segments?",
    
    # Team Performance
    "What is the revenue-per-team-member for each department?",
    "Which teams are working on the most critical customer commitments?",
    
    # Project Delivery
    "How many projects are blocked by operational constraints?",
    "What is the success rate of projects by team and product area?",
    
    # Growth & Expansion
    "Which customer segments offer the highest growth potential?",
    "What products have the best profitability-to-cost ratio for scaling?",
    "Which regions show the most promise for expansion based on current metrics?",
    
    # Competitive Positioning
    "How do our SLAs compare to industry standards by product?",
    "Which features give us competitive advantage in each market segment?"
]


async def test_single_question(agent: AgentRunner, question: str, index: int) -> Dict[str, Any]:
    """Test a single question and return results"""
    print(f"\n{'='*80}")
    print(f"Q{index}: {question}")
    print("="*80)
    
    start_time = time.time()
    try:
        response = await agent.run(question)
        elapsed = time.time() - start_time
        
        answer = response.get('answer', 'No answer provided')
        metadata = response.get('metadata', {})
        
        # Check if answer is grounded
        answer_lower = answer.lower()
        is_grounded = not any(phrase in answer_lower for phrase in [
            "no results", "not available", "no specific", "sorry",
            "unable to", "did not return", "no information",
            "does not contain", "not found"
        ])
        
        # Check if it used enhanced queries
        used_enhanced = False
        if 'router_metadata' in metadata:
            routes = metadata.get('router_metadata', {}).get('routes_used', [])
            if 'graph_query' in routes:
                # Check retrieval metadata for enhanced query usage
                for retrieval in metadata.get('retrievals', []):
                    if retrieval.get('metadata', {}).get('enhanced_query'):
                        used_enhanced = True
                        break
        
        print(f"\nAnswer: {answer[:500]}..." if len(answer) > 500 else f"\nAnswer: {answer}")
        print(f"\nGrounded: {'✅ Yes' if is_grounded else '❌ No'}")
        print(f"Enhanced Query: {'✅ Yes' if used_enhanced else '❌ No'}")
        print(f"Time: {elapsed:.2f}s")
        
        return {
            'question': question,
            'answer': answer,
            'is_grounded': is_grounded,
            'used_enhanced': used_enhanced,
            'elapsed': elapsed
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return {
            'question': question,
            'answer': f"ERROR: {str(e)}",
            'is_grounded': False,
            'used_enhanced': False,
            'elapsed': 0
        }


async def test_improvements():
    """Test improvements on key questions"""
    print("=== TESTING LANGGRAPH IMPROVEMENTS ===")
    print(f"\nTesting {len(TEST_QUESTIONS)} key business questions...")
    print("Using GPT-3.5-Turbo\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent ready\n")
    
    # Test each question
    results = []
    grounded_count = 0
    enhanced_count = 0
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        result = await test_single_question(agent, question, i)
        results.append(result)
        
        if result['is_grounded']:
            grounded_count += 1
        if result['used_enhanced']:
            enhanced_count += 1
        
        # Rate limiting
        if i < len(TEST_QUESTIONS):
            await asyncio.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Questions: {len(TEST_QUESTIONS)}")
    print(f"Grounded Answers: {grounded_count} ({grounded_count/len(TEST_QUESTIONS)*100:.1f}%)")
    print(f"Used Enhanced Queries: {enhanced_count} ({enhanced_count/len(TEST_QUESTIONS)*100:.1f}%)")
    print(f"\nTarget: >83% grounded answers")
    print(f"Current: {grounded_count/len(TEST_QUESTIONS)*100:.1f}% grounded answers")
    
    if grounded_count/len(TEST_QUESTIONS) > 0.83:
        print("\n✅ SUCCESS: Achieved target of >83% grounded answers!")
    else:
        print(f"\n❌ Need {int(0.83 * len(TEST_QUESTIONS)) - grounded_count} more grounded answers to reach target")
    
    # Show which questions still need work
    ungrounded = [r for r in results if not r['is_grounded']]
    if ungrounded:
        print("\nQuestions still needing data:")
        for r in ungrounded[:5]:
            print(f"  - {r['question'][:80]}...")


if __name__ == "__main__":
    asyncio.run(test_improvements())