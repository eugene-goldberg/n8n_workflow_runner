#!/usr/bin/env python3
"""Test all 60 business questions through the API and evaluate grounding"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple

API_URL = "http://localhost:8000"
API_KEY = "test-key-123"  # Optional API key


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


def evaluate_grounding(answer: str, metadata: dict) -> Tuple[bool, str]:
    """
    Evaluate if an answer is grounded in Neo4j data.
    Returns (is_grounded, reason)
    """
    answer_lower = answer.lower()
    
    # Strong indicators of grounding
    positive_indicators = [
        "based on the",
        "according to",
        "shows that",
        "indicates that",
        "the data shows",
        "results show",
        "found that",
        "there are",
        "we have",
        "total of",
        "percentage",
        "revenue",
        "customers",
        "teams",
        "projects"
    ]
    
    # Clear indicators of no grounding
    negative_indicators = [
        "no results",
        "not available",
        "no specific",
        "sorry",
        "unable to",
        "did not return",
        "no information",
        "couldn't find",
        "no relevant",
        "doesn't have",
        "no direct",
        "cannot provide",
        "don't have",
        "no data"
    ]
    
    # Check metadata first
    if metadata.get('grounded', False):
        # API thinks it's grounded, but let's verify
        pass
    
    # Check for negative indicators first
    for indicator in negative_indicators:
        if indicator in answer_lower:
            return False, f"Contains '{indicator}'"
    
    # Check answer length
    if len(answer) < 50:
        return False, "Answer too short"
    
    # Check for positive indicators
    positive_count = sum(1 for ind in positive_indicators if ind in answer_lower)
    
    # Check for specific data mentions
    has_numbers = any(char.isdigit() for char in answer)
    has_specifics = any(word in answer_lower for word in ["customer", "team", "product", "revenue", "risk", "project"])
    
    if positive_count >= 2 and (has_numbers or has_specifics):
        return True, "Contains specific data references"
    elif positive_count >= 1 and has_specifics:
        return True, "References specific entities"
    else:
        return False, "Lacks specific data references"


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
    print("=== TESTING ALL 60 BUSINESS QUESTIONS VIA API ===")
    print(f"API URL: {API_URL}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
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
        
        # Evaluate grounding
        is_grounded, reason = evaluate_grounding(answer, metadata)
        
        if is_grounded:
            grounded_count += 1
            category_stats[category]['grounded'] += 1
            print(f"✅ GROUNDED: {reason}")
        else:
            print(f"❌ NOT GROUNDED: {reason}")
        
        print(f"Answer preview: {answer[:150]}...")
        
        # Store result
        results.append({
            'index': i,
            'category': category,
            'question': question,
            'answer': answer,
            'is_grounded': is_grounded,
            'grounding_reason': reason,
            'api_metadata': metadata,
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
    print("FINAL API TEST RESULTS")
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
    
    # Improvement from baseline
    baseline = 21.7
    print(f"\nImprovement from baseline:")
    print(f"   Baseline: {baseline}%")
    print(f"   Current: {success_rate:.1f}%")
    print(f"   Improvement: {success_rate/baseline:.1f}x ({success_rate - baseline:.1f} percentage points)")
    
    # Sample failing questions
    if grounded_count < len(questions):
        print("\n" + "="*80)
        print("SAMPLE FAILING QUESTIONS")
        print("="*80)
        
        failing = [r for r in results if not r['is_grounded']]
        for r in failing[:5]:
            print(f"\nQ{r['index']}: {r['question']}")
            print(f"Category: {r['category']}")
            print(f"Reason: {r['grounding_reason']}")
            print(f"Answer: {r['answer'][:200]}...")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_data = {
        'timestamp': timestamp,
        'api_url': API_URL,
        'summary': {
            'total_questions': len(questions),
            'grounded': grounded_count,
            'ungrounded': len(questions) - grounded_count,
            'success_rate': success_rate,
            'total_time_minutes': total_time/60
        },
        'category_stats': category_stats,
        'detailed_results': results
    }
    
    output_file = f'api_test_results_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()