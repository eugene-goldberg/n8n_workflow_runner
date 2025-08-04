#!/usr/bin/env python3
"""Test all business questions using GPT-3.5 to avoid rate limits"""

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

# Set up logging
logging.basicConfig(level=logging.INFO)
# Suppress verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langsmith").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Rate limiting configuration for GPT-3.5
DELAY_BETWEEN_REQUESTS = 2  # 2 seconds between requests for GPT-3.5
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
        'retries': 0,
        'cypher_query': None,
        'result_count': 0
    }
    
    for retry in range(MAX_RETRIES):
        try:
            print(f"\n{'='*80}")
            print(f"Question {index}/60: {question[:100]}...")
            print(f"Category: {category} > {subcategory}")
            
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
            
            # Try to extract Cypher query from answer if it's a graph query
            if result['route'] == 'relational_query' and 'cypher' in result['answer'].lower():
                result['cypher_query'] = 'Generated'
            
            print(f"✅ Success in {elapsed:.2f}s - Route: {result['route']}")
            
            # Success - no need to retry
            break
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            result['retries'] = retry + 1
            
            print(f"❌ Error: {error_msg[:100]}...")
            
            # Check if it's a rate limit error
            if "rate_limit_exceeded" in error_msg or "429" in str(e):
                if retry < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** retry)
                    print(f"Rate limit hit. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    continue
            
            # For other errors, wait a bit and retry
            if retry < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
    
    return result


async def test_all_business_questions():
    """Test all business questions with GPT-3.5"""
    
    print("=== TESTING ALL BUSINESS QUESTIONS WITH GPT-3.5-TURBO ===\n")
    print("Using GPT-3.5 to avoid rate limits and reduce costs\n")
    
    # Parse questions from file
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    
    print(f"Found {len(questions)} questions to test")
    print(f"Delay between requests: {DELAY_BETWEEN_REQUESTS}s\n")
    
    # Initialize agent
    print("Initializing agent with GPT-3.5...")
    agent = AgentRunner()
    print("Agent initialized successfully\n")
    
    # Test all questions
    results = []
    start_time = time.time()
    
    # Summary stats
    stats = {
        'by_route': {},
        'by_category': {},
        'errors': []
    }
    
    for i, question_data in enumerate(questions, 1):
        # Test the question
        result = await test_question_with_retry(agent, question_data, i)
        results.append(result)
        
        # Update stats
        route = result.get('route', 'no_route')
        stats['by_route'][route] = stats['by_route'].get(route, 0) + 1
        
        category = result['category']
        if category not in stats['by_category']:
            stats['by_category'][category] = {'total': 0, 'success': 0}
        stats['by_category'][category]['total'] += 1
        if result['success']:
            stats['by_category'][category]['success'] += 1
        
        if not result['success']:
            stats['errors'].append({
                'question': result['question'],
                'error': result['error']
            })
        
        # Save intermediate results every 10 questions
        if i % 10 == 0:
            with open('test_results_gpt35_intermediate.json', 'w') as f:
                json.dump({
                    'completed': i,
                    'total': len(questions),
                    'results': results,
                    'stats': stats
                }, f, indent=2)
        
        # Rate limiting delay
        if i < len(questions):
            await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Progress update every 10 questions
        if i % 10 == 0 or i == len(questions):
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(questions) - i) * avg_time
            print(f"\n📊 Progress: {i}/{len(questions)} ({i/len(questions)*100:.1f}%)")
            print(f"⏱️  Elapsed: {elapsed/60:.1f}m, Remaining: {remaining/60:.1f}m")
            print(f"📈 Routes used: {dict(stats['by_route'])}")
    
    # Generate final report
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
    
    print(f"\nRoutes distribution:")
    for route, count in stats['by_route'].items():
        print(f"  {route}: {count} ({count/len(results)*100:.1f}%)")
    
    print(f"\nSuccess by category:")
    for category, cat_stats in stats['by_category'].items():
        success_rate = cat_stats['success'] / cat_stats['total'] * 100
        print(f"  {category}: {cat_stats['success']}/{cat_stats['total']} ({success_rate:.1f}%)")
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_gpt35_{timestamp}.json"
    
    final_report = {
        'metadata': {
            'model': 'gpt-3.5-turbo',
            'total_questions': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful/len(results)*100,
            'total_time_minutes': total_time/60,
            'timestamp': timestamp,
            'stats': stats
        },
        'results': results
    }
    
    with open(results_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Generate markdown report
    generate_markdown_report(final_report, f"test_report_gpt35_{timestamp}.md")
    
    return final_report


def generate_markdown_report(report: Dict[str, Any], filename: str):
    """Generate a markdown report from test results"""
    
    with open(filename, 'w') as f:
        f.write("# Business Questions Test Report (GPT-3.5-Turbo)\n\n")
        f.write(f"Generated: {report['metadata']['timestamp']}\n")
        f.write(f"Model: {report['metadata']['model']}\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write(f"- Total Questions: {report['metadata']['total_questions']}\n")
        f.write(f"- Successful: {report['metadata']['successful']} ({report['metadata']['success_rate']:.1f}%)\n")
        f.write(f"- Failed: {report['metadata']['failed']}\n")
        f.write(f"- Total Time: {report['metadata']['total_time_minutes']:.1f} minutes\n\n")
        
        # Route distribution
        f.write("## Route Distribution\n\n")
        for route, count in report['metadata']['stats']['by_route'].items():
            percentage = count / report['metadata']['total_questions'] * 100
            f.write(f"- {route}: {count} ({percentage:.1f}%)\n")
        f.write("\n")
        
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
            
            # Group by subcategory
            subcategories = {}
            for result in cat_results:
                subcat = result['subcategory']
                if subcat not in subcategories:
                    subcategories[subcat] = []
                subcategories[subcat].append(result)
            
            for subcategory, subcat_results in subcategories.items():
                if subcategory:
                    f.write(f"#### {subcategory}\n\n")
                
                for result in subcat_results:
                    status = "✅" if result['success'] else "❌"
                    f.write(f"{status} **Q{result['index']}**: {result['question']}\n")
                    
                    if result['success']:
                        f.write(f"   - Route: `{result['route']}`\n")
                        if result.get('cypher_query'):
                            f.write(f"   - Generated Cypher: Yes\n")
                    else:
                        error_msg = result['error'][:100] + '...' if len(result['error']) > 100 else result['error']
                        f.write(f"   - Error: {error_msg}\n")
                    f.write("\n")
        
        # Failed questions summary
        f.write("\n## Failed Questions Summary\n\n")
        
        failed_questions = [r for r in report['results'] if not r['success']]
        if failed_questions:
            f.write(f"Total failed: {len(failed_questions)}\n\n")
            
            # Group by error type
            error_types = {}
            for result in failed_questions:
                error_type = "rate_limit" if "rate_limit" in result['error'] else "other"
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(result)
            
            for error_type, errors in error_types.items():
                f.write(f"### {error_type.replace('_', ' ').title()} Errors ({len(errors)})\n\n")
                for result in errors[:5]:  # Show first 5
                    f.write(f"- Q{result['index']}: {result['question'][:50]}...\n")
                if len(errors) > 5:
                    f.write(f"- ... and {len(errors) - 5} more\n")
                f.write("\n")
        else:
            f.write("No failed questions! 🎉\n")
    
    print(f"📄 Markdown report saved to: {filename}")


if __name__ == "__main__":
    # Set the model environment variable
    os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'
    asyncio.run(test_all_business_questions())