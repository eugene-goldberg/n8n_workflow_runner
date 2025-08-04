#!/usr/bin/env python3
"""Capture all questions and answers after Neo4j data fixes"""

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
            
            # Write to output file
            output_file.write(f"\n{'='*80}\n")
            output_file.write(f"Question {index}: {question}\n")
            output_file.write(f"Category: {category}")
            if subcategory:
                output_file.write(f" > {subcategory}")
            output_file.write(f"\n{'='*80}\n\n")
            output_file.write(f"Answer:\n{answer}\n")
            output_file.flush()
            
            print(f" ✓ ({elapsed:.1f}s)")
            
            return {
                'index': index,
                'question': question,
                'answer': answer,
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
                    'success': False,
                    'elapsed': 0
                }


async def capture_all_qa():
    """Capture all questions and answers after data fixes"""
    
    print("=== CAPTURING ALL Q&A AFTER NEO4J DATA FIXES ===\n")
    print("Using GPT-3.5-Turbo for faster processing\n")
    
    # Parse questions from file
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    
    print(f"Found {len(questions)} questions to process")
    print(f"Output will be saved to: all_questions_and_answers_AFTER_FIX.txt\n")
    
    # Initialize agent
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent ready\n")
    
    # Open output file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('all_questions_and_answers_AFTER_FIX.txt', 'w') as output_file:
        # Write header
        output_file.write("LANGGRAPH AGENTIC RAG - ALL BUSINESS Q&A (AFTER DATA FIXES)\n")
        output_file.write(f"Generated: {timestamp}\n")
        output_file.write(f"Model: GPT-3.5-Turbo\n")
        output_file.write(f"Total Questions: {len(questions)}\n")
        output_file.write("\nData Improvements Applied:\n")
        output_file.write("- Added customer success scores for all customers\n")
        output_file.write("- Created customer events (negative events for low-score customers)\n")
        output_file.write("- Added customer commitments and SLAs\n")
        output_file.write("- Created product success metrics\n")
        output_file.write("- Established team-product relationships\n")
        output_file.write("- Added risk mitigation strategies\n")
        output_file.write("- Updated project statuses\n")
        output_file.write("- Created roadmap items\n")
        output_file.write("- Added customer concerns\n")
        output_file.write("="*80 + "\n")
        
        # Process all questions
        results = []
        start_time = time.time()
        successful = 0
        
        for i, question_data in enumerate(questions, 1):
            # Capture Q&A
            result = await capture_qa_with_retry(agent, question_data, i, output_file)
            results.append(result)
            
            if result['success']:
                successful += 1
            
            # Rate limiting delay
            if i < len(questions):
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Progress update every 10 questions
            if i % 10 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(questions) - i) * avg_time
                print(f"\nProgress: {i}/{len(questions)} ({i/len(questions)*100:.1f}%) - "
                      f"Success rate: {successful/i*100:.1f}% - "
                      f"ETA: {remaining/60:.1f}m\n")
        
        # Write summary
        total_time = time.time() - start_time
        output_file.write(f"\n\n{'='*80}\n")
        output_file.write("SUMMARY\n")
        output_file.write("="*80 + "\n")
        output_file.write(f"Total Questions: {len(questions)}\n")
        output_file.write(f"Successful: {successful}\n")
        output_file.write(f"Failed: {len(questions) - successful}\n")
        output_file.write(f"Success Rate: {successful/len(questions)*100:.1f}%\n")
        output_file.write(f"Total Time: {total_time/60:.1f} minutes\n")
        output_file.write(f"Average Time per Question: {total_time/len(questions):.1f} seconds\n")
    
    print(f"\n{'='*60}")
    print("COMPLETE!")
    print(f"{'='*60}")
    print(f"All questions and answers saved to: all_questions_and_answers_AFTER_FIX.txt")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Success rate: {successful/len(questions)*100:.1f}%")
    
    # Analyze improvement
    analyze_improvement(results)
    
    # Also save a JSON version for analysis
    json_data = {
        'timestamp': timestamp,
        'model': 'gpt-3.5-turbo',
        'total_questions': len(questions),
        'successful': successful,
        'failed': len(questions) - successful,
        'total_time_minutes': total_time/60,
        'results': results
    }
    
    with open('all_qa_results_after_fix.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"JSON results saved to: all_qa_results_after_fix.json")


def analyze_improvement(results):
    """Analyze how many questions now have grounded answers"""
    grounded_count = 0
    
    for result in results:
        if result['success']:
            answer = result['answer'].lower()
            # Check for indicators of grounded data
            if any(indicator in answer for indicator in [
                'based on', 'retrieved', 'found', 'shows', 'indicates',
                'customers', 'products', 'teams', 'revenue', '$',
                'score', 'percentage', '%', 'total', 'count'
            ]) and not any(negative in answer for negative in [
                'no results', 'not available', 'no specific', 'sorry',
                'unable to', 'did not return', 'no information'
            ]):
                grounded_count += 1
    
    print(f"\n📊 Data Grounding Analysis:")
    print(f"   Questions with grounded answers: {grounded_count}/{len(results)} ({grounded_count/len(results)*100:.1f}%)")
    print(f"   Improvement from previous run: +{grounded_count - 23} questions")


if __name__ == "__main__":
    asyncio.run(capture_all_qa())