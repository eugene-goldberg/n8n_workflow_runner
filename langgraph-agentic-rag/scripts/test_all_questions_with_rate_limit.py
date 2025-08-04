#!/usr/bin/env python3
"""Test all business questions with rate limiting and retry logic"""

import sys
import os
import asyncio
import time
import json
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Suppress verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langsmith").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Rate limiting configuration
RATE_LIMIT_TPM = 30000  # Tokens per minute limit
ESTIMATED_TOKENS_PER_REQUEST = 500  # Conservative estimate
REQUESTS_PER_MINUTE = RATE_LIMIT_TPM // ESTIMATED_TOKENS_PER_REQUEST
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # Seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 5  # Base delay for retries


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


async def test_question_with_retry(
    agent: AgentRunner, 
    question_data: Dict[str, str], 
    index: int
) -> Dict[str, Any]:
    """Test a single question with retry logic"""
    
    question = question_data['question']
    category = question_data['category']
    subcategory = question_data['subcategory']
    
    result = {
        'index': index,
        'category': category,
        'subcategory': subcategory,
        'question': question,
        'success': False,
        'answer': None,
        'route': None,
        'tools_used': [],
        'error': None,
        'retries': 0
    }
    
    for retry in range(MAX_RETRIES):
        try:
            print(f"\n{'='*80}")
            print(f"Question {index}: {question}")
            print(f"Category: {category} > {subcategory}")
            if retry > 0:
                print(f"Retry attempt: {retry}/{MAX_RETRIES}")
            print(f"{'='*80}")
            
            # Run the agent
            start_time = time.time()
            response = await agent.run(question)
            elapsed = time.time() - start_time
            
            # Extract results
            result['success'] = True
            result['answer'] = response.get('answer', 'No answer provided')
            result['route'] = response.get('metadata', {}).get('route')
            result['tools_used'] = response.get('metadata', {}).get('tools_used', [])
            result['elapsed_time'] = elapsed
            result['retries'] = retry
            
            print(f"\n✅ Success in {elapsed:.2f}s")
            print(f"Route: {result['route']}")
            print(f"Tools: {result['tools_used']}")
            
            # Success - no need to retry
            break
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            result['retries'] = retry + 1
            
            print(f"\n❌ Error: {error_msg}")
            
            # Check if it's a rate limit error
            if "rate_limit_exceeded" in error_msg or "429" in str(e):
                if retry < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** retry)  # Exponential backoff
                    print(f"Rate limit hit. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
            
            # For other errors, don't retry
            break
    
    return result


async def test_all_business_questions():
    """Test all business questions with rate limiting"""
    
    print("=== TESTING ALL BUSINESS QUESTIONS WITH RATE LIMITING ===\n")
    
    # Parse questions from file
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    
    print(f"Found {len(questions)} questions to test")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} requests per minute")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS:.2f}s\n")
    
    # Initialize agent once
    print("Initializing agent...")
    agent = AgentRunner()
    print("Agent initialized successfully\n")
    
    # Test all questions
    results = []
    start_time = time.time()
    
    for i, question_data in enumerate(questions, 1):
        # Test the question
        result = await test_question_with_retry(agent, question_data, i)
        results.append(result)
        
        # Save intermediate results
        with open('test_results_intermediate.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Rate limiting delay (except for last question)
        if i < len(questions):
            print(f"\n⏱️  Waiting {DELAY_BETWEEN_REQUESTS:.1f}s for rate limiting...")
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Progress update
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = (len(questions) - i) * avg_time
        print(f"\n📊 Progress: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
        print(f"⏱️  Elapsed: {elapsed/60:.1f}m, Remaining: {remaining/60:.1f}m")
    
    # Generate summary report
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Total questions: {len(results)}")
    print(f"Successful: {successful} ({successful/len(results)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(results)*100:.1f}%)")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average time per question: {total_time/len(results):.2f}s")
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    final_report = {
        'metadata': {
            'total_questions': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful/len(results)*100,
            'total_time_minutes': total_time/60,
            'timestamp': timestamp
        },
        'results': results
    }
    
    with open(results_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Generate markdown report
    generate_markdown_report(final_report, f"test_report_{timestamp}.md")
    
    return final_report


def generate_markdown_report(report: Dict[str, Any], filename: str):
    """Generate a markdown report from test results"""
    
    with open(filename, 'w') as f:
        f.write("# Business Questions Test Report\n\n")
        f.write(f"Generated: {report['metadata']['timestamp']}\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- Total Questions: {report['metadata']['total_questions']}\n")
        f.write(f"- Successful: {report['metadata']['successful']} ({report['metadata']['success_rate']:.1f}%)\n")
        f.write(f"- Failed: {report['metadata']['failed']}\n")
        f.write(f"- Total Time: {report['metadata']['total_time_minutes']:.1f} minutes\n\n")
        
        # Results by category
        f.write("## Results by Category\n\n")
        
        categories = {}
        for result in report['results']:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, cat_results in categories.items():
            f.write(f"### {category}\n\n")
            
            success_count = sum(1 for r in cat_results if r['success'])
            f.write(f"Success Rate: {success_count}/{len(cat_results)} ({success_count/len(cat_results)*100:.1f}%)\n\n")
            
            for result in cat_results:
                status = "✅" if result['success'] else "❌"
                f.write(f"{status} **Q{result['index']}**: {result['question']}\n")
                
                if result['success']:
                    f.write(f"   - Route: {result['route']}\n")
                    f.write(f"   - Tools: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}\n")
                else:
                    f.write(f"   - Error: {result['error']}\n")
                f.write("\n")
        
        # Failed questions detail
        f.write("\n## Failed Questions Detail\n\n")
        
        failed_questions = [r for r in report['results'] if not r['success']]
        if failed_questions:
            for result in failed_questions:
                f.write(f"### Q{result['index']}: {result['question']}\n\n")
                f.write(f"- Category: {result['category']} > {result['subcategory']}\n")
                f.write(f"- Error: {result['error']}\n")
                f.write(f"- Retries: {result['retries']}\n\n")
        else:
            f.write("No failed questions! 🎉\n")
    
    print(f"📄 Markdown report saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(test_all_business_questions())