#!/usr/bin/env python3
"""Run single-question verification for all 60 questions"""

import subprocess
import json
import time
import os
from datetime import datetime


def parse_business_questions(file_path: str) -> list:
    """Parse business questions from the markdown file"""
    questions = []
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    current_category = ""
    for line in lines:
        line = line.strip()
        
        # Category (no indentation)
        if line and not line.startswith(' ') and not line.startswith('-'):
            current_category = line
            
        # Question (starts with -)
        elif line.startswith('  -') or (line.startswith('-') and not line.startswith('--')):
            question = line.lstrip('- ').strip()
            if question:
                questions.append({
                    'category': current_category,
                    'question': question
                })
    
    return questions


def main():
    print("=== VERIFYING ALL 60 QUESTIONS INDIVIDUALLY ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Parse questions
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    print(f"Found {len(questions)} questions to verify\n")
    
    # Results storage
    results = []
    grounded_count = 0
    category_stats = {}
    
    # Process each question
    for i, q_data in enumerate(questions, 1):
        question = q_data['question']
        category = q_data['category']
        
        print(f"[{i:2d}/{len(questions)}] {category[:20]:<20} ", end='', flush=True)
        print(f"{question[:50]:<50}... ", end='', flush=True)
        
        # Run verification script
        start_time = time.time()
        try:
            result = subprocess.run(
                ['/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3', '/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/scripts/verify_single_question.py', str(i)],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            elapsed = time.time() - start_time
            
            # Parse result
            verification_file = f"verification_q{i}.json"
            if os.path.exists(verification_file):
                with open(verification_file, 'r') as f:
                    verification_data = json.load(f)
                
                is_grounded = verification_data['is_grounded']
                answer = verification_data['answer']
                
                # Clean up verification file
                os.remove(verification_file)
            else:
                is_grounded = False
                answer = "Failed to get verification result"
            
            # Store result
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'answer': answer,
                'is_grounded': is_grounded,
                'elapsed': elapsed
            })
            
            # Update stats
            if is_grounded:
                grounded_count += 1
                print(f"✅ ({elapsed:4.1f}s)")
            else:
                print(f"❌ ({elapsed:4.1f}s)")
            
            # Update category stats
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'grounded': 0}
            category_stats[category]['total'] += 1
            if is_grounded:
                category_stats[category]['grounded'] += 1
            
        except subprocess.TimeoutExpired:
            print(f"⏱️  TIMEOUT")
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'answer': "TIMEOUT",
                'is_grounded': False,
                'elapsed': 30
            })
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:20]}")
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'answer': f"ERROR: {str(e)}",
                'is_grounded': False,
                'elapsed': 0
            })
        
        # Progress update every 10 questions
        if i % 10 == 0:
            success_rate = grounded_count / i * 100
            print(f"\n  Progress: {grounded_count}/{i} grounded ({success_rate:.1f}%)\n")
        
        # Small delay between questions
        time.sleep(1)
    
    # Calculate final results
    success_rate = grounded_count / len(questions) * 100
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL VERIFICATION RESULTS")
    print("="*80)
    print(f"Total Questions: {len(questions)}")
    print(f"Grounded Answers: {grounded_count} ({success_rate:.1f}%)")
    print(f"Ungrounded Answers: {len(questions) - grounded_count} ({100 - success_rate:.1f}%)")
    
    if success_rate > 83:
        print(f"\n✅ SUCCESS: Achieved {success_rate:.1f}% grounded answers (target: >83%)")
    else:
        print(f"\n❌ Below target: {success_rate:.1f}% (target: >83%)")
        print(f"   Need {int(0.83 * len(questions)) - grounded_count} more grounded answers")
    
    # Category breakdown
    print("\n" + "="*80)
    print("PERFORMANCE BY CATEGORY")
    print("="*80)
    print(f"{'Category':<40} {'Grounded':>8} {'Total':>6} {'Rate':>8}")
    print("-" * 80)
    
    for category, stats in sorted(category_stats.items()):
        rate = stats['grounded'] / stats['total'] * 100
        print(f"{category[:40]:<40} {stats['grounded']:>8} {stats['total']:>6} {rate:>7.1f}%")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_data = {
        'timestamp': timestamp,
        'summary': {
            'total_questions': len(questions),
            'grounded': grounded_count,
            'ungrounded': len(questions) - grounded_count,
            'success_rate': success_rate
        },
        'category_stats': category_stats,
        'detailed_results': results
    }
    
    output_file = f'verification_results_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Show sample failing questions
    print("\n" + "="*80)
    print("SAMPLE FAILING QUESTIONS")
    print("="*80)
    
    failing = [r for r in results if not r['is_grounded']]
    for r in failing[:5]:
        print(f"\nQ{r['index']}: {r['question'][:70]}...")
        print(f"Category: {r['category']}")
        print(f"Answer: {r['answer'][:150]}...")


if __name__ == "__main__":
    main()