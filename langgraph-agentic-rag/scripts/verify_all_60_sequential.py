#!/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3
"""Run verification for all 60 questions sequentially to avoid timeouts"""

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
    print("=== FINAL VERIFICATION OF ALL 60 QUESTIONS (SEQUENTIAL) ===")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Running questions one at a time to avoid timeouts...\n")
    
    # Parse questions
    questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
    questions = parse_business_questions(questions_file)
    print(f"Found {len(questions)} questions to verify\n")
    
    # Results storage
    results = []
    grounded_count = 0
    category_stats = {}
    start_time = time.time()
    
    # Process each question individually
    for i, q_data in enumerate(questions, 1):
        question = q_data['question']
        category = q_data['category']
        
        # Initialize category stats
        if category not in category_stats:
            category_stats[category] = {'total': 0, 'grounded': 0}
        category_stats[category]['total'] += 1
        
        print(f"[{i:2d}/{len(questions)}] Testing...", end='', flush=True)
        
        # Run single question verification
        q_start = time.time()
        try:
            # Use the single question verification script
            result = subprocess.run(
                ['/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3', 
                 '/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/scripts/verify_single_question.py', 
                 str(i)],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout per question
            )
            q_elapsed = time.time() - q_start
            
            # Check if grounded (exit code 0 means grounded)
            is_grounded = (result.returncode == 0)
            
            if is_grounded:
                grounded_count += 1
                category_stats[category]['grounded'] += 1
                print(f"\r[{i:2d}/{len(questions)}] ✅ {category[:20]:<20} Q: {question[:40]:<40}... ({q_elapsed:.1f}s)")
            else:
                print(f"\r[{i:2d}/{len(questions)}] ❌ {category[:20]:<20} Q: {question[:40]:<40}... ({q_elapsed:.1f}s)")
            
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'is_grounded': is_grounded,
                'elapsed': q_elapsed
            })
            
            # Clean up any verification files
            verification_file = f"verification_q{i}.json"
            if os.path.exists(verification_file):
                os.remove(verification_file)
            
        except subprocess.TimeoutExpired:
            print(f"\r[{i:2d}/{len(questions)}] ⏱️  {category[:20]:<20} Q: {question[:40]:<40}... TIMEOUT")
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'is_grounded': False,
                'elapsed': 30
            })
        except Exception as e:
            print(f"\r[{i:2d}/{len(questions)}] ❌ {category[:20]:<20} ERROR: {str(e)[:30]}")
            results.append({
                'index': i,
                'category': category,
                'question': question,
                'is_grounded': False,
                'elapsed': 0
            })
        
        # Progress update every 10 questions
        if i % 10 == 0:
            current_rate = grounded_count / i * 100
            elapsed_total = time.time() - start_time
            print(f"\n  Progress: {grounded_count}/{i} grounded ({current_rate:.1f}%) - Time: {elapsed_total/60:.1f}m\n")
        
        # Small delay between questions to avoid rate limits
        if i < len(questions):
            time.sleep(2)
    
    # Calculate final results
    total_time = time.time() - start_time
    success_rate = grounded_count / len(questions) * 100
    
    # Print summary
    print("\n" + "="*80)
    print("FINAL VERIFICATION RESULTS")
    print("="*80)
    print(f"Total Questions: {len(questions)}")
    print(f"Grounded Answers: {grounded_count} ({success_rate:.1f}%)")
    print(f"Ungrounded Answers: {len(questions) - grounded_count} ({100 - success_rate:.1f}%)")
    print(f"Total Time: {total_time/60:.1f} minutes")
    print(f"Average Time per Question: {total_time/len(questions):.1f} seconds")
    
    if success_rate >= 83:
        print(f"\n✅ SUCCESS: Achieved {success_rate:.1f}% grounded answers (target: >83%)")
        print(f"   Exceeded target by: {success_rate - 83:.1f} percentage points")
    else:
        print(f"\n❌ Below target: {success_rate:.1f}% (target: >83%)")
        print(f"   Need {int(0.83 * len(questions)) - grounded_count} more grounded answers")
    
    # Improvement from baseline
    baseline = 21.7
    print(f"\nImprovement from baseline:")
    print(f"   Baseline: {baseline}%")
    print(f"   Current: {success_rate:.1f}%")
    print(f"   Improvement: {success_rate/baseline:.1f}x ({success_rate - baseline:.1f} percentage points)")
    
    # Category breakdown
    print("\n" + "="*80)
    print("PERFORMANCE BY CATEGORY")
    print("="*80)
    print(f"{'Category':<40} {'Grounded':>8} {'Total':>6} {'Rate':>8}")
    print("-" * 80)
    
    for category, stats in sorted(category_stats.items()):
        rate = stats['grounded'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"{category[:40]:<40} {stats['grounded']:>8} {stats['total']:>6} {rate:>7.1f}%")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_data = {
        'timestamp': timestamp,
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
    
    output_file = f'final_verification_{timestamp}.json'
    with open(output_file, 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Show top failing questions if any
    if grounded_count < len(questions):
        print("\n" + "="*80)
        print("SAMPLE FAILING QUESTIONS")
        print("="*80)
        
        failing = [r for r in results if not r['is_grounded']]
        for r in failing[:5]:
            print(f"Q{r['index']}: {r['question'][:70]}...")
            print(f"   Category: {r['category']}")


if __name__ == "__main__":
    main()