#!/usr/bin/env python3
"""Test all 60 questions individually with timeout handling"""

import sys
import os

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import signal
from contextlib import contextmanager

from src.agents.main_agent import AgentRunner
import logging

# Set up logging to reduce noise
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("langsmith").setLevel(logging.ERROR)
logging.getLogger("neo4j").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("src").setLevel(logging.ERROR)

# Configuration
QUESTION_TIMEOUT = 15  # 15 seconds per question
DELAY_BETWEEN_QUESTIONS = 1  # 1 second delay


class TimeoutException(Exception):
    pass


@contextmanager
def timeout(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    
    # Set up signal handler
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Disable alarm


def parse_business_questions(file_path: str) -> List[Dict[str, str]]:
    """Parse business questions from the markdown file"""
    questions = []
    current_category = ""
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Category (no indentation)
        if line and not line.startswith(' ') and not line.startswith('-'):
            current_category = line
            
        # Question (starts with -)
        elif line.startswith('  -') or line.startswith('-'):
            question = line.lstrip('- ').strip()
            if question:
                questions.append({
                    'category': current_category,
                    'question': question
                })
    
    return questions


def is_answer_grounded(answer: str) -> bool:
    """Check if an answer is grounded in data"""
    answer_lower = answer.lower()
    
    negative_indicators = [
        "no results", "not available", "no specific", "sorry",
        "unable to", "did not return", "no information",
        "does not contain", "not found", "did not yield",
        "does not specify", "cannot provide", "graph query did not",
        "no data available", "not in the database"
    ]
    
    # Check for negative indicators
    for indicator in negative_indicators:
        if indicator in answer_lower:
            return False
    
    # Additional check - very short answers are usually not grounded
    if len(answer) < 50:
        return False
    
    return True


async def test_single_question_async(agent: AgentRunner, question: str) -> Dict[str, Any]:
    """Test a single question asynchronously"""
    start_time = time.time()
    
    try:
        response = await agent.run(question)
        elapsed = time.time() - start_time
        
        answer = response.get('answer', 'No answer provided')
        is_grounded = is_answer_grounded(answer)
        
        return {
            'answer': answer,
            'is_grounded': is_grounded,
            'elapsed': elapsed,
            'error': None
        }
        
    except Exception as e:
        return {
            'answer': f"ERROR: {str(e)}",
            'is_grounded': False,
            'elapsed': time.time() - start_time,
            'error': str(e)
        }


def test_single_question(agent: AgentRunner, question: str, index: int, total: int) -> Dict[str, Any]:
    """Test a single question with timeout"""
    print(f"\rTesting Q{index}/{total}: {question[:60]}...", end='', flush=True)
    
    try:
        with timeout(QUESTION_TIMEOUT):
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_single_question_async(agent, question))
            loop.close()
            
            # Print result indicator
            if result['is_grounded']:
                print(f" ✓ ({result['elapsed']:.1f}s)", flush=True)
            else:
                print(f" ✗ ({result['elapsed']:.1f}s)", flush=True)
            
            return result
            
    except TimeoutException:
        print(f" ⏱ TIMEOUT", flush=True)
        return {
            'answer': "TIMEOUT: Question took too long to process",
            'is_grounded': False,
            'elapsed': QUESTION_TIMEOUT,
            'error': 'Timeout'
        }
    except Exception as e:
        print(f" ❌ ERROR: {str(e)[:30]}...", flush=True)
        return {
            'answer': f"ERROR: {str(e)}",
            'is_grounded': False,
            'elapsed': 0,
            'error': str(e)
        }


def main():
    """Test all 60 questions individually"""
    print("=== TESTING ALL 60 BUSINESS QUESTIONS INDIVIDUALLY ===")
    print(f"Timeout: {QUESTION_TIMEOUT}s per question")
    print(f"Model: GPT-3.5-Turbo\n")
    
    # Parse questions
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    print(f"Found {len(questions)} questions to test\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent ready\n")
    
    # Test each question
    results = []
    grounded_count = 0
    timeout_count = 0
    error_count = 0
    start_time = time.time()
    
    for i, q_data in enumerate(questions, 1):
        question = q_data['question']
        category = q_data['category']
        
        # Test the question
        result = test_single_question(agent, question, i, len(questions))
        
        # Store result
        result['index'] = i
        result['question'] = question
        result['category'] = category
        results.append(result)
        
        # Update counters
        if result['is_grounded']:
            grounded_count += 1
        if result.get('error') == 'Timeout':
            timeout_count += 1
        elif result.get('error'):
            error_count += 1
        
        # Progress update every 10 questions
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = grounded_count / i * 100
            print(f"\n  Progress: {i}/{len(questions)} - Grounded: {grounded_count} ({rate:.1f}%) - Time: {elapsed/60:.1f}m\n")
        
        # Small delay between questions
        if i < len(questions):
            time.sleep(DELAY_BETWEEN_QUESTIONS)
    
    # Calculate final statistics
    total_time = time.time() - start_time
    success_rate = grounded_count / len(questions) * 100
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"Total Questions: {len(questions)}")
    print(f"Grounded Answers: {grounded_count} ({success_rate:.1f}%)")
    print(f"Ungrounded Answers: {len(questions) - grounded_count} ({100 - success_rate:.1f}%)")
    print(f"Timeouts: {timeout_count}")
    print(f"Errors: {error_count}")
    print(f"Total Time: {total_time/60:.1f} minutes")
    print(f"Average Time per Question: {total_time/len(questions):.1f} seconds")
    
    if success_rate > 83:
        print(f"\n✅ SUCCESS: Achieved {success_rate:.1f}% grounded answers (target: >83%)")
    else:
        print(f"\n❌ Below target: {success_rate:.1f}% grounded answers (target: >83%)")
        print(f"   Need {int(0.83 * len(questions)) - grounded_count} more grounded answers")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results_data = {
        'timestamp': timestamp,
        'summary': {
            'total_questions': len(questions),
            'grounded': grounded_count,
            'ungrounded': len(questions) - grounded_count,
            'timeouts': timeout_count,
            'errors': error_count,
            'success_rate': success_rate,
            'total_time_minutes': total_time/60
        },
        'results': results
    }
    
    with open('test_60_individual_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: test_60_individual_results.json")
    
    # Show categories performance
    print("\n" + "="*80)
    print("PERFORMANCE BY CATEGORY")
    print("="*80)
    
    category_stats = {}
    for result in results:
        cat = result['category']
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'grounded': 0}
        category_stats[cat]['total'] += 1
        if result['is_grounded']:
            category_stats[cat]['grounded'] += 1
    
    for cat, stats in sorted(category_stats.items()):
        rate = stats['grounded'] / stats['total'] * 100
        print(f"{cat[:40]:<40} {stats['grounded']:>3}/{stats['total']:<3} ({rate:>5.1f}%)")
    
    # Show failing questions
    print("\n" + "="*80)
    print("SAMPLE FAILING QUESTIONS")
    print("="*80)
    
    failing = [r for r in results if not r['is_grounded'] and r.get('error') != 'Timeout']
    for r in failing[:5]:  # Show first 5
        print(f"\nQ{r['index']}: {r['question'][:70]}...")
        print(f"Category: {r['category']}")
        print(f"Answer preview: {r['answer'][:150]}...")


if __name__ == "__main__":
    main()