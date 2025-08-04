#!/usr/bin/env python3
"""Analyze test results from the business questions test"""

import json
import sys
from typing import Dict, List, Any
from collections import defaultdict
import glob

def load_latest_results():
    """Load the latest test results file"""
    result_files = glob.glob("test_results_gpt35_*.json")
    # Filter out intermediate files
    result_files = [f for f in result_files if 'intermediate' not in f]
    
    if not result_files:
        print("No test results found!")
        return None
    
    latest_file = sorted(result_files)[-1]
    print(f"Loading results from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def analyze_results(results: Dict[str, Any]):
    """Analyze the test results"""
    metadata = results['metadata']
    questions = results['results']
    
    print("\n" + "="*80)
    print("TEST RESULTS ANALYSIS")
    print("="*80)
    
    # Overall summary
    print(f"\nModel: {metadata['model']}")
    print(f"Total Questions: {metadata['total_questions']}")
    print(f"Success Rate: {metadata['success_rate']:.1f}%")
    print(f"Total Time: {metadata['total_time_minutes']:.1f} minutes")
    print(f"Average Time per Question: {metadata['total_time_minutes']*60/metadata['total_questions']:.1f} seconds")
    
    # Route distribution
    print("\n## Route Distribution")
    route_stats = metadata['stats']['by_route']
    for route, count in sorted(route_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = count / metadata['total_questions'] * 100
        route_name = 'No route' if route == 'null' or route is None else route
        print(f"  {route_name}: {count} ({percentage:.1f}%)")
    
    # Category performance
    print("\n## Performance by Category")
    category_stats = metadata['stats']['by_category']
    for category, stats in category_stats.items():
        success_rate = (stats['success'] / stats['total']) * 100 if stats['total'] > 0 else 0
        print(f"  {category}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    # Cypher query generation stats
    cypher_count = sum(1 for q in questions if q.get('cypher_query'))
    print(f"\n## Cypher Query Generation")
    print(f"  Questions that generated Cypher: {cypher_count}/{len(questions)} ({cypher_count/len(questions)*100:.1f}%)")
    
    # Error analysis
    errors = metadata['stats'].get('errors', [])
    print(f"\n## Error Analysis")
    print(f"  Total errors: {len(errors)}")
    
    if errors:
        error_types = defaultdict(int)
        for error in errors:
            if 'rate_limit' in error['error']:
                error_types['Rate Limit'] += 1
            elif 'timeout' in error['error'].lower():
                error_types['Timeout'] += 1
            elif 'syntax' in error['error'].lower():
                error_types['Syntax Error'] += 1
            else:
                error_types['Other'] += 1
        
        print("  Error types:")
        for error_type, count in error_types.items():
            print(f"    {error_type}: {count}")
    
    # Find patterns in failed questions
    failed_questions = [q for q in questions if not q['success']]
    if failed_questions:
        print(f"\n## Failed Questions Analysis ({len(failed_questions)} questions)")
        
        # Group by subcategory
        failed_by_subcategory = defaultdict(list)
        for q in failed_questions:
            failed_by_subcategory[q['subcategory']].append(q)
        
        for subcategory, questions_list in sorted(failed_by_subcategory.items()):
            print(f"\n  {subcategory or 'No subcategory'}: {len(questions_list)} failures")
            for q in questions_list[:3]:  # Show first 3
                print(f"    - Q{q['index']}: {q['question'][:60]}...")
    
    # Success patterns
    successful_questions = [q for q in questions if q['success']]
    print(f"\n## Success Patterns")
    
    # Questions that were routed correctly
    routed_questions = [q for q in successful_questions if q.get('route')]
    print(f"  Successfully routed: {len(routed_questions)}/{len(successful_questions)}")
    
    # Average response time by route
    print("\n  Average response time by route:")
    route_times = defaultdict(list)
    for q in successful_questions:
        if 'elapsed_time' in q:
            route = q.get('route', 'no_route')
            route_times[route].append(q['elapsed_time'])
    
    for route, times in sorted(route_times.items()):
        avg_time = sum(times) / len(times)
        print(f"    {route}: {avg_time:.2f}s")
    
    # Key insights
    print("\n## Key Insights")
    
    # Check if routing is working
    no_route_count = route_stats.get(None, 0) + route_stats.get('null', 0)
    if no_route_count == metadata['total_questions']:
        print("  ⚠️  No questions were properly routed - router may not be working")
    elif route_stats.get('relational_query', 0) > metadata['total_questions'] * 0.7:
        print("  ✅ Most questions correctly routed to relational_query for graph traversal")
    
    # Check Cypher generation
    if cypher_count > metadata['total_questions'] * 0.5:
        print("  ✅ Good Cypher query generation rate")
    else:
        print("  ⚠️  Low Cypher query generation - may need to improve prompt or schema context")
    
    # Performance
    avg_time = metadata['total_time_minutes'] * 60 / metadata['total_questions']
    if avg_time < 5:
        print("  ✅ Good performance - average response under 5 seconds")
    else:
        print(f"  ⚠️  Slow responses - average {avg_time:.1f}s per question")
    
    return results

def generate_improvement_suggestions(results: Dict[str, Any]):
    """Generate suggestions for improvement based on results"""
    print("\n## Improvement Suggestions")
    
    metadata = results['metadata']
    questions = results['results']
    
    # If success rate is low
    if metadata['success_rate'] < 80:
        print("\n### To improve success rate:")
        print("  1. Review failed questions for common patterns")
        print("  2. Enhance Cypher generation prompts with more examples")
        print("  3. Add more comprehensive schema context")
    
    # If routing isn't working
    route_stats = metadata['stats']['by_route']
    if route_stats.get(None, 0) > metadata['total_questions'] * 0.5:
        print("\n### To improve routing:")
        print("  1. Check if router is being called properly")
        print("  2. Review router prompt and examples")
        print("  3. Ensure all question types are covered in router logic")
    
    # If Cypher generation is low
    cypher_count = sum(1 for q in questions if q.get('cypher_query'))
    if cypher_count < metadata['total_questions'] * 0.5:
        print("\n### To improve Cypher generation:")
        print("  1. Add more Cypher examples to the prompt")
        print("  2. Include specific patterns for common question types")
        print("  3. Ensure schema relationships are clearly documented")

if __name__ == "__main__":
    results = load_latest_results()
    if results:
        analyze_results(results)
        generate_improvement_suggestions(results)