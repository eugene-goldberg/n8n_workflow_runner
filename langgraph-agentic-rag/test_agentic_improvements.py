#!/usr/bin/env python3
"""Test all 60 business questions through the improved agentic API"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

API_URL = "http://localhost:8000"
API_KEY = "test-key-123"


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


def test_question_via_api(question: str) -> Dict[str, Any]:
    """Test a single question through the API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    payload = {
        "question": question
    }
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned status {response.status_code}: {response.text}",
                "answer": f"ERROR: {response.status_code}",
                "metadata": {"grounded": False}
            }
            
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out",
            "answer": "ERROR: Timeout",
            "metadata": {"grounded": False}
        }
    except Exception as e:
        return {
            "error": str(e),
            "answer": f"ERROR: {str(e)}",
            "metadata": {"grounded": False}
        }


def main():
    print("=== TESTING ALL 60 QUESTIONS WITH IMPROVED AGENTIC RAG ===")
    print(f"API URL: {API_URL}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Multi-strategy retrieval enabled: YES")
    print("Improved synthesis prompting: YES\n")
    
    # Parse questions
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    print(f"Found {len(questions)} questions to test\n")
    
    # Results storage
    results = []
    grounded_count = 0
    category_stats = {}
    start_time = time.time()
    
    # Test each question
    for i, q_data in enumerate(questions, 1):
        question = q_data['question']
        category = q_data['category']
        
        # Initialize category stats
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'grounded': 0}
        category_stats[category]['total'] += 1
        
        print(f"\n[{i:2d}/{len(questions)}] {category}")
        print(f"Q: {question}")
        print("Testing...", end='', flush=True)
        
        # Test via API
        q_start = time.time()
        api_response = test_question_via_api(question)
        q_elapsed = time.time() - q_start
        print(f" ({q_elapsed:.1f}s)")
        
        # Extract answer and metadata
        answer = api_response.get('answer', 'No answer provided')
        metadata = api_response.get('metadata', {})
        is_grounded = metadata.get('grounded', False)
        
        if is_grounded:
            grounded_count += 1
            category_stats[category]['grounded'] += 1
            print(f"✅ GROUNDED")
        else:
            print(f"❌ NOT GROUNDED")
        
        # Show answer preview
        print(f"Answer preview: {answer[:150]}...")
        
        # Check if multi-strategy was used
        tools_used = metadata.get('tools_used', [])
        if len(tools_used) > 1:
            print(f"🔄 Multi-strategy: {', '.join(tools_used)}")
        
        # Store result
        results.append({
            'index': i,
            'category': category,
            'question': question,
            'answer': answer,
            'is_grounded': is_grounded,
            'tools_used': tools_used,
            'elapsed': q_elapsed
        })
        
        # Progress update every 10 questions
        if i % 10 == 0:
            current_rate = grounded_count / i * 100
            elapsed_total = time.time() - start_time
            print(f"\n{'='*60}")
            print(f"Progress: {i}/{len(questions)} tested")
            print(f"Current success rate: {grounded_count}/{i} ({current_rate:.1f}%)")
            print(f"Time elapsed: {elapsed_total/60:.1f} minutes")
            print(f"{'='*60}\n")
        
        # Small delay between questions
        time.sleep(1)
    
    # Calculate final results
    total_time = time.time() - start_time
    success_rate = grounded_count / len(questions) * 100
    
    # Print final summary
    print("\n" + "="*80)
    print("FINAL RESULTS - IMPROVED AGENTIC RAG")
    print("="*80)
    print(f"Total Questions: {len(questions)}")
    print(f"Grounded Answers: {grounded_count} ({success_rate:.1f}%)")
    print(f"Ungrounded Answers: {len(questions) - grounded_count} ({100 - success_rate:.1f}%)")
    print(f"Total Time: {total_time/60:.1f} minutes")
    print(f"Average Time per Question: {total_time/len(questions):.1f} seconds")
    
    # Category breakdown
    print("\n" + "="*80)
    print("PERFORMANCE BY CATEGORY")
    print("="*80)
    print(f"{'Category':<40} {'Grounded':>8} {'Total':>6} {'Rate':>8}")
    print("-" * 80)
    
    for category, stats in sorted(category_stats.items()):
        rate = stats['grounded'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{category[:40]:<40} {stats['grounded']:>8} {stats['total']:>6} {rate:>7.1f}%")
    
    # Comparison with previous results
    print("\n" + "="*80)
    print("COMPARISON WITH PREVIOUS RESULTS")
    print("="*80)
    
    previous_rate = 66.7  # Previous best result
    improvement = success_rate - previous_rate
    
    print(f"Previous best: {previous_rate:.1f}%")
    print(f"Current: {success_rate:.1f}%")
    
    if improvement > 0:
        print(f"✅ IMPROVEMENT: +{improvement:.1f} percentage points")
    elif improvement < 0:
        print(f"❌ REGRESSION: {improvement:.1f} percentage points")
    else:
        print(f"➖ NO CHANGE")
    
    # Target comparison
    print("\n" + "="*80)
    print("TARGET COMPARISON")
    print("="*80)
    
    if success_rate >= 83:
        print(f"✅ SUCCESS: Achieved {success_rate:.1f}% grounded answers (target: >83%)")
        print(f"   Exceeded target by: {success_rate - 83:.1f} percentage points")
    else:
        print(f"❌ Below target: {success_rate:.1f}% (target: >83%)")
        print(f"   Gap: {83 - success_rate:.1f} percentage points")
        print(f"   Need {int(0.83 * len(questions)) - grounded_count} more grounded answers")
    
    # Multi-strategy usage analysis
    multi_strategy_count = sum(1 for r in results if len(r['tools_used']) > 1)
    print(f"\nMulti-strategy usage: {multi_strategy_count}/{len(questions)} questions ({multi_strategy_count/len(questions)*100:.1f}%)")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_data = {
        'timestamp': timestamp,
        'api_url': API_URL,
        'improvements': {
            'multi_strategy_retrieval': True,
            'improved_synthesis': True,
            'agentic_behavior': True
        },
        'summary': {
            'total_questions': len(questions),
            'grounded': grounded_count,
            'ungrounded': len(questions) - grounded_count,
            'success_rate': success_rate,
            'total_time_minutes': total_time/60,
            'improvement_from_previous': improvement
        },
        'category_stats': category_stats,
        'detailed_results': results
    }
    
    output_file = f'agentic_test_results_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Show sample of newly grounded questions
    print("\n" + "="*80)
    print("SAMPLE OF IMPROVED QUESTIONS")
    print("="*80)
    
    # Find questions that are now grounded but weren't before
    # These would be questions like Q1, Q2 from Customer Health that were failing
    improved_questions = [
        (1, "What are the top 5 customers by revenue, and what are their current success scores?"),
        (2, "Which customers have declining success scores, and what events are driving the decline?"),
        (21, "Which products have the highest customer satisfaction scores?"),
        (26, "How much future revenue will be at risk if [Feature X] misses its deadline by 3 months?")
    ]
    
    for idx, question in improved_questions[:3]:
        result = next((r for r in results if r['index'] == idx), None)
        if result and result['is_grounded']:
            print(f"\nQ{idx}: {question[:70]}...")
            print(f"Status: {'✅ Now grounded' if result['is_grounded'] else '❌ Still failing'}")
            print(f"Answer: {result['answer'][:200]}...")


if __name__ == "__main__":
    main()