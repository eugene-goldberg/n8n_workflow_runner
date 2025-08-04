#!/usr/bin/env python3
"""Test questions in small batches to avoid timeouts"""

import sys
import os

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
import json
from typing import List, Dict, Any

from src.agents.main_agent import AgentRunner
import logging

# Set up logging to reduce noise
logging.basicConfig(level=logging.WARNING)
for logger_name in ["httpx", "langsmith", "neo4j", "openai", "src"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)


def parse_business_questions(file_path: str) -> List[str]:
    """Parse business questions from the markdown file"""
    questions = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('  -') or (line.startswith('-') and not line.startswith('--')):
            question = line.lstrip('- ').strip()
            if question:
                questions.append(question)
    
    return questions


def is_answer_grounded(answer: str) -> bool:
    """Check if an answer is grounded in data"""
    answer_lower = answer.lower()
    
    negative_indicators = [
        "no results", "not available", "no specific", "sorry",
        "unable to", "did not return", "no information",
        "does not contain", "not found", "did not yield",
        "cannot provide", "graph query did not"
    ]
    
    return not any(indicator in answer_lower for indicator in negative_indicators)


async def test_batch(agent: AgentRunner, questions: List[str], start_idx: int) -> List[Dict[str, Any]]:
    """Test a batch of questions"""
    results = []
    
    for i, question in enumerate(questions):
        idx = start_idx + i
        print(f"Q{idx}: {question[:60]}...", end=' ', flush=True)
        
        try:
            start_time = time.time()
            response = await agent.run(question)
            elapsed = time.time() - start_time
            
            answer = response.get('answer', 'No answer provided')
            is_grounded = is_answer_grounded(answer)
            
            results.append({
                'index': idx,
                'question': question,
                'answer': answer,
                'is_grounded': is_grounded,
                'elapsed': elapsed
            })
            
            print(f"{'✓' if is_grounded else '✗'} ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            results.append({
                'index': idx,
                'question': question,
                'answer': f"ERROR: {str(e)}",
                'is_grounded': False,
                'elapsed': 0
            })
        
        # Small delay between questions
        await asyncio.sleep(1)
    
    return results


async def test_all_in_batches():
    """Test all questions in batches"""
    print("=== TESTING ALL 60 QUESTIONS IN BATCHES ===")
    print("Batch size: 10 questions")
    print("Model: GPT-3.5-Turbo\n")
    
    # Parse questions
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    all_questions = parse_business_questions(questions_file)
    print(f"Found {len(all_questions)} questions\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent ready\n")
    
    # Process in batches of 10
    batch_size = 10
    all_results = []
    grounded_total = 0
    
    for batch_start in range(0, len(all_questions), batch_size):
        batch_end = min(batch_start + batch_size, len(all_questions))
        batch_questions = all_questions[batch_start:batch_end]
        
        print(f"\n--- BATCH {batch_start//batch_size + 1} (Questions {batch_start + 1}-{batch_end}) ---")
        
        batch_results = await test_batch(agent, batch_questions, batch_start + 1)
        all_results.extend(batch_results)
        
        # Count grounded in this batch
        batch_grounded = sum(1 for r in batch_results if r['is_grounded'])
        grounded_total += batch_grounded
        
        print(f"\nBatch summary: {batch_grounded}/{len(batch_questions)} grounded ({batch_grounded/len(batch_questions)*100:.0f}%)")
        print(f"Running total: {grounded_total}/{len(all_results)} grounded ({grounded_total/len(all_results)*100:.0f}%)")
        
        # Save intermediate results
        with open(f'batch_results_{batch_start//batch_size + 1}.json', 'w') as f:
            json.dump(batch_results, f, indent=2)
    
    # Final summary
    success_rate = grounded_total / len(all_questions) * 100
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Total Questions: {len(all_questions)}")
    print(f"Grounded Answers: {grounded_total} ({success_rate:.1f}%)")
    print(f"Ungrounded Answers: {len(all_questions) - grounded_total} ({100 - success_rate:.1f}%)")
    
    if success_rate > 83:
        print(f"\n✅ SUCCESS: Achieved {success_rate:.1f}% grounded answers!")
    else:
        print(f"\n❌ Below target: {success_rate:.1f}% (target: >83%)")
        print(f"   Need {int(0.83 * len(all_questions)) - grounded_total} more grounded answers")
    
    # Save all results
    final_results = {
        'total_questions': len(all_questions),
        'grounded': grounded_total,
        'ungrounded': len(all_questions) - grounded_total,
        'success_rate': success_rate,
        'results': all_results
    }
    
    with open('all_batch_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print("\nAll results saved to: all_batch_results.json")


if __name__ == "__main__":
    asyncio.run(test_all_in_batches())