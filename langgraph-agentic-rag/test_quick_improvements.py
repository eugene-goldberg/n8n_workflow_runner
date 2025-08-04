#!/usr/bin/env python3
"""Quick test of improvements on a few key questions"""

import sys
import os

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("langsmith").setLevel(logging.ERROR)
logging.getLogger("neo4j").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("src").setLevel(logging.ERROR)

# Test a few key questions
TEST_QUESTIONS = [
    "What percentage of our ARR is dependent on customers with success scores below 70?",
    "Which teams have the highest operational costs relative to the revenue they support?",
    "What is the revenue-per-team-member for each department?",
    "Which company objectives have the highest number of associated risks?",
    "How many projects are blocked by operational constraints?"
]


async def test_question(agent: AgentRunner, question: str, index: int):
    """Test a single question"""
    print(f"\nQ{index}: {question}")
    print("-" * 80)
    
    start_time = time.time()
    try:
        response = await agent.run(question)
        elapsed = time.time() - start_time
        
        answer = response.get('answer', 'No answer provided')
        
        # Check if answer is grounded
        answer_lower = answer.lower()
        is_grounded = not any(phrase in answer_lower for phrase in [
            "no results", "not available", "no specific", "sorry",
            "unable to", "did not return", "no information"
        ])
        
        # Show first 300 chars of answer
        print(f"Answer: {answer[:300]}..." if len(answer) > 300 else f"Answer: {answer}")
        print(f"\nGrounded: {'✅ YES' if is_grounded else '❌ NO'}")
        print(f"Time: {elapsed:.2f}s")
        
        return is_grounded
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False


async def test_quick():
    """Quick test of improvements"""
    print("=== QUICK TEST OF IMPROVEMENTS ===")
    print(f"Testing {len(TEST_QUESTIONS)} key questions...\n")
    
    # Initialize agent
    agent = AgentRunner()
    
    # Test each question
    grounded_count = 0
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        is_grounded = await test_question(agent, question, i)
        if is_grounded:
            grounded_count += 1
        
        # Rate limiting
        if i < len(TEST_QUESTIONS):
            await asyncio.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print(f"SUMMARY: {grounded_count}/{len(TEST_QUESTIONS)} grounded answers ({grounded_count/len(TEST_QUESTIONS)*100:.0f}%)")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_quick())