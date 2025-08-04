#!/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3
"""Verify improvements by testing previously failing questions"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import logging

# Suppress logging
logging.basicConfig(level=logging.ERROR)
for logger in ["httpx", "langsmith", "neo4j", "openai", "src", "httpcore", "langchain"]:
    logging.getLogger(logger).setLevel(logging.ERROR)

from src.agents.main_agent import AgentRunner


# Test questions from the weakest categories
TEST_QUESTIONS = [
    # Operational Risk (was 20%)
    ("Which teams are understaffed relative to their product support requirements?", "Operational Risk"),
    ("What operational risks could impact product SLAs?", "Operational Risk"),
    ("Which products have the highest operational risk exposure?", "Operational Risk"),
    ("How do operational risks correlate with customer success scores?", "Operational Risk"),
    ("What percentage of projects are at risk of missing deadlines?", "Operational Risk"),
    
    # Project Delivery (was 40%)
    ("Which projects are critical for maintaining current revenue?", "Project Delivery"),
    ("What percentage of projects are delivering on schedule?", "Project Delivery"),
    ("Which projects have dependencies that could impact multiple products?", "Project Delivery"),
    ("How many projects are blocked by operational constraints?", "Project Delivery"),
    ("What is the success rate of projects by team and product area?", "Project Delivery"),
    
    # Team Performance (was 40%)
    ("Which teams support the most revenue-generating products?", "Team Performance"),
    ("What is the revenue-per-team-member for each department?", "Team Performance"),
    ("Which teams are working on the most critical customer commitments?", "Team Performance"),
    ("How are teams allocated across products and projects?", "Team Performance"),
    ("Which teams have the highest impact on customer success?", "Team Performance"),
]


async def test_question(agent: AgentRunner, question: str) -> tuple[bool, str]:
    """Test a single question and return if it's grounded"""
    try:
        response = await agent.run(question)
        answer = response.get('answer', 'No answer')
        
        # Check if grounded
        negative = ["no results", "not available", "no specific", "sorry", 
                   "unable to", "did not return", "no information", "couldn't find"]
        is_grounded = not any(n in answer.lower() for n in negative) and len(answer) > 50
        
        return is_grounded, answer[:200] + "..."
    except Exception as e:
        return False, f"ERROR: {str(e)}"


async def main():
    print("=== VERIFYING IMPROVEMENTS ON PREVIOUSLY FAILING QUESTIONS ===\n")
    
    agent = AgentRunner()
    results = {"Operational Risk": [], "Project Delivery": [], "Team Performance": []}
    
    for i, (question, category) in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i:2d}/{len(TEST_QUESTIONS)}] {category[:15]:<15} {question[:50]}...")
        
        is_grounded, answer_preview = await test_question(agent, question)
        results[category].append(is_grounded)
        
        if is_grounded:
            print(f"       ✅ GROUNDED - {answer_preview[:100]}...")
        else:
            print(f"       ❌ NOT GROUNDED - {answer_preview[:100]}...")
        
        await asyncio.sleep(1)  # Rate limiting
    
    # Print summary
    print("\n" + "="*80)
    print("IMPROVEMENT SUMMARY")
    print("="*80)
    
    for category, category_results in results.items():
        grounded = sum(category_results)
        total = len(category_results)
        old_rate = {"Operational Risk": 20, "Project Delivery": 40, "Team Performance": 40}[category]
        new_rate = grounded / total * 100
        
        print(f"\n{category}:")
        print(f"  Previous: {old_rate}% grounded")
        print(f"  Current:  {new_rate:.0f}% grounded ({grounded}/{total})")
        print(f"  Change:   +{new_rate - old_rate:.0f} percentage points")
    
    # Overall
    total_grounded = sum(sum(r) for r in results.values())
    total_questions = sum(len(r) for r in results.values())
    overall_rate = total_grounded / total_questions * 100
    
    print(f"\nOVERALL:")
    print(f"  Grounded: {total_grounded}/{total_questions} ({overall_rate:.0f}%)")
    print(f"  Previously these 3 categories averaged: 33%")
    print(f"  Improvement: +{overall_rate - 33:.0f} percentage points")


if __name__ == "__main__":
    asyncio.run(main())