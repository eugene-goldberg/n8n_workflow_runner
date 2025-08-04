#!/usr/bin/env python3
"""Final capture of all questions and answers with improvements"""

import sys
import os

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict, Any

from src.agents.main_agent import AgentRunner
import logging

# Set up logging to reduce noise
logging.basicConfig(level=logging.WARNING)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("langsmith").setLevel(logging.ERROR)
logging.getLogger("neo4j").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("src").setLevel(logging.ERROR)

# Rate limiting configuration
DELAY_BETWEEN_REQUESTS = 2  # 2 seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 3


def parse_business_questions(file_path: str) -> List[Dict[str, str]]:
    """Parse business questions from the markdown file"""
    questions = []
    current_category = ""
    current_subcategory = ""
    
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
            
        # Subcategory (2 spaces)
        elif line.startswith('  ') and not line.startswith('  -'):
            current_subcategory = line.strip()
            
        # Question (starts with -)
        elif line.startswith('  -') or line.startswith('-'):
            question = line.lstrip('- ').strip()
            if question:
                questions.append({
                    'category': current_category,
                    'subcategory': current_subcategory,
                    'question': question
                })
    
    return questions


async def capture_qa_with_retry(
    agent: AgentRunner, 
    question_data: Dict[str, str], 
    index: int,
    output_file: Any
) -> Dict[str, Any]:
    """Capture a single Q&A with retry logic"""
    
    question = question_data['question']
    category = question_data['category']
    subcategory = question_data['subcategory']
    
    for retry in range(MAX_RETRIES):
        try:
            # Progress indicator
            print(f"Processing Q{index}/60: {question[:60]}...", end='', flush=True)
            
            # Run the agent
            start_time = time.time()
            response = await agent.run(question)
            elapsed = time.time() - start_time
            
            # Extract answer
            answer = response.get('answer', 'No answer provided')
            
            # Check if answer is grounded
            answer_lower = answer.lower()
            is_grounded = not any(phrase in answer_lower for phrase in [
                "no results", "not available", "no specific", "sorry",
                "unable to", "did not return", "no information",
                "does not contain", "not found", "did not yield",
                "does not specify", "cannot provide", "graph query did not"
            ])
            
            # Write to output file
            output_file.write(f"\n{'='*80}\n")
            output_file.write(f"Question {index}: {question}\n")
            output_file.write(f"Category: {category}")
            if subcategory:
                output_file.write(f" > {subcategory}")
            output_file.write(f"\n{'='*80}\n\n")
            output_file.write(f"Answer:\n{answer}\n")
            output_file.write(f"\nGrounded: {'✅ YES' if is_grounded else '❌ NO'}\n")
            output_file.flush()
            
            print(f" {'✓' if is_grounded else '✗'} ({elapsed:.1f}s)")
            
            return {
                'index': index,
                'question': question,
                'answer': answer,
                'is_grounded': is_grounded,
                'success': True,
                'elapsed': elapsed
            }
            
        except Exception as e:
            print(f" ✗ Error: {str(e)[:50]}...")
            
            # Retry with backoff
            if retry < MAX_RETRIES - 1:
                wait_time = RETRY_DELAY * (2 ** retry)
                print(f"  Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                # Write error to file
                output_file.write(f"\n{'='*80}\n")
                output_file.write(f"Question {index}: {question}\n")
                output_file.write(f"Category: {category}")
                if subcategory:
                    output_file.write(f" > {subcategory}")
                output_file.write(f"\n{'='*80}\n\n")
                output_file.write(f"ERROR: {str(e)}\n")
                output_file.flush()
                
                return {
                    'index': index,
                    'question': question,
                    'answer': f"ERROR: {str(e)}",
                    'is_grounded': False,
                    'success': False,
                    'elapsed': 0
                }


async def capture_all_qa():
    """Capture all questions and answers with final improvements"""
    
    print("=== FINAL CAPTURE OF ALL Q&A WITH IMPROVEMENTS ===\n")
    print("Using GPT-3.5-Turbo for faster processing\n")
    
    # Parse questions from file
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    
    print(f"Found {len(questions)} questions to process")
    print(f"Output will be saved to: all_questions_and_answers_FINAL.txt\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent ready\n")
    
    # Open output file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('all_questions_and_answers_FINAL.txt', 'w') as output_file:
        # Write header
        output_file.write("LANGGRAPH AGENTIC RAG - FINAL RESULTS WITH ALL IMPROVEMENTS\n")
        output_file.write(f"Generated: {timestamp}\n")
        output_file.write(f"Model: GPT-3.5-Turbo\n")
        output_file.write(f"Total Questions: {len(questions)}\n")
        output_file.write("\nImprovements Applied:\n")
        output_file.write("1. Enhanced Cypher query templates for complex aggregations\n")
        output_file.write("2. Added comprehensive financial relationships\n")
        output_file.write("3. Created customer subscriptions and revenue tracking\n")
        output_file.write("4. Added team operational costs and member counts\n")
        output_file.write("5. Linked customers to products they use\n")
        output_file.write("6. Added historical revenue for growth calculations\n")
        output_file.write("7. Added customer segments and regions\n")
        output_file.write("8. Added SLA data and performance metrics\n")
        output_file.write("9. Created objective-risk relationships\n")
        output_file.write("10. Improved query routing and keyword matching\n")
        output_file.write("="*80 + "\n")
        
        # Process all questions
        results = []
        start_time = time.time()
        grounded_count = 0
        
        for i, question_data in enumerate(questions, 1):
            # Capture Q&A
            result = await capture_qa_with_retry(agent, question_data, i, output_file)
            results.append(result)
            
            if result['is_grounded']:
                grounded_count += 1
            
            # Rate limiting delay
            if i < len(questions):
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Progress update every 10 questions
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(questions) - i) * avg_time
                print(f"\nProgress: {i}/{len(questions)} ({i/len(questions)*100:.1f}%) - "
                      f"Grounded: {grounded_count}/{i} ({grounded_count/i*100:.1f}%) - "
                      f"ETA: {remaining/60:.1f}m\n")
        
        # Write summary
        total_time = time.time() - start_time
        output_file.write(f"\n\n{'='*80}\n")
        output_file.write("SUMMARY\n")
        output_file.write("="*80 + "\n")
        output_file.write(f"Total Questions: {len(questions)}\n")
        output_file.write(f"Grounded Answers: {grounded_count}\n")
        output_file.write(f"Ungrounded Answers: {len(questions) - grounded_count}\n")
        output_file.write(f"Success Rate: {grounded_count/len(questions)*100:.1f}%\n")
        output_file.write(f"Total Time: {total_time/60:.1f} minutes\n")
        output_file.write(f"Average Time per Question: {total_time/len(questions):.1f} seconds\n")
        
        if grounded_count/len(questions) > 0.83:
            output_file.write(f"\n✅ SUCCESS: Achieved target of >83% grounded answers!\n")
        else:
            output_file.write(f"\n❌ Current grounding rate: {grounded_count/len(questions)*100:.1f}%\n")
            output_file.write(f"   Need {int(0.83 * len(questions)) - grounded_count} more grounded answers to reach 83% target\n")
    
    print(f"\n{'='*60}")
    print("COMPLETE!")
    print(f"{'='*60}")
    print(f"All questions and answers saved to: all_questions_and_answers_FINAL.txt")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Grounded answers: {grounded_count}/{len(questions)} ({grounded_count/len(questions)*100:.1f}%)")
    
    if grounded_count/len(questions) > 0.83:
        print("\n✅ SUCCESS: Achieved target of >83% grounded answers!")
    else:
        print(f"\n❌ Need {int(0.83 * len(questions)) - grounded_count} more grounded answers to reach 83% target")
    
    # Also save a JSON version for analysis
    json_data = {
        'timestamp': timestamp,
        'model': 'gpt-3.5-turbo',
        'total_questions': len(questions),
        'grounded': grounded_count,
        'ungrounded': len(questions) - grounded_count,
        'success_rate': grounded_count/len(questions)*100,
        'total_time_minutes': total_time/60,
        'results': results
    }
    
    with open('all_qa_results_final.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"JSON results saved to: all_qa_results_final.json")


if __name__ == "__main__":
    asyncio.run(capture_all_qa())