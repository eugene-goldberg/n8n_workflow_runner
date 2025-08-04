#!/usr/bin/env python3
"""Analyze improvement in data grounding after Neo4j fixes"""

import json
import re
from typing import Dict, List, Tuple


def is_answer_grounded(answer: str) -> Tuple[bool, str]:
    """Determine if an answer is grounded in Neo4j data"""
    answer_lower = answer.lower()
    
    # Negative indicators - answer is NOT grounded
    negative_indicators = [
        "no results", "not available", "no specific", "sorry",
        "unable to", "did not return", "no information",
        "does not contain", "not found", "did not yield",
        "does not specify", "cannot provide", "graph query did not"
    ]
    
    # Positive indicators - answer IS grounded
    positive_indicators = [
        "based on", "retrieved", "found", "shows", "indicates",
        "the result", "according to", "from the graph",
        "graph results", "query result"
    ]
    
    # Data-specific indicators
    data_indicators = [
        r"\$[0-9,]+",  # Dollar amounts
        r"\d+\s*customers?",  # Customer counts
        r"\d+\s*products?",  # Product counts
        r"\d+\s*teams?",  # Team counts
        r"\d+%",  # Percentages
        r"score[s]?\s*(?:of\s*)?\d+",  # Scores
        r"\d+\.\d+",  # Decimal numbers
        "spyro",  # Product names
        "global", "retail", "tech", "finance",  # Customer names
        "revenue", "arr", "cost", "profitability"
    ]
    
    # Check for negative indicators first
    for indicator in negative_indicators:
        if indicator in answer_lower:
            return False, "not_grounded"
    
    # Check for positive indicators
    has_positive = any(indicator in answer_lower for indicator in positive_indicators)
    
    # Check for data indicators
    has_data = any(
        re.search(pattern, answer_lower) if isinstance(pattern, str) and pattern.startswith(r"\\")
        else pattern in answer_lower
        for pattern in data_indicators
    )
    
    # Special case: If answer provides specific data points
    if has_data and (has_positive or len(answer) > 100):
        return True, "grounded_with_data"
    
    # If it has positive indicators but no data
    if has_positive and not has_data:
        return False, "partial_grounding"
    
    # Long answers with structure often contain data
    if len(answer) > 200 and ("1." in answer or "- " in answer):
        return True, "grounded_structured"
    
    return False, "not_grounded"


def analyze_results(before_file: str, after_file: str):
    """Compare results before and after data fixes"""
    
    # Load before results
    with open(before_file, 'r') as f:
        before_data = json.load(f)
    
    # Load after results
    with open(after_file, 'r') as f:
        after_data = json.load(f)
    
    # Analyze each question
    improvements = []
    category_stats = {}
    
    for i in range(len(before_data['results'])):
        before_result = before_data['results'][i]
        after_result = after_data['results'][i]
        
        before_grounded, before_type = is_answer_grounded(before_result['answer'])
        after_grounded, after_type = is_answer_grounded(after_result['answer'])
        
        # Track improvements
        improved = not before_grounded and after_grounded
        
        # Extract category from question (assuming format)
        question = before_result['question']
        category = "Unknown"
        
        # Map questions to categories based on index
        if i < 5:
            category = "Revenue Risk Analysis"
        elif i < 10:
            category = "Cost & Profitability"
        elif i < 15:
            category = "Customer Health"
        elif i < 20:
            category = "Customer Commitments"
        elif i < 25:
            category = "Product Performance"
        elif i < 30:
            category = "Roadmap & Delivery Risk"
        elif i < 35:
            category = "Strategic Risk Assessment"
        elif i < 40:
            category = "Operational Risk"
        elif i < 45:
            category = "Team Performance"
        elif i < 50:
            category = "Project Delivery"
        elif i < 55:
            category = "Growth & Expansion"
        else:
            category = "Competitive Positioning"
        
        if category not in category_stats:
            category_stats[category] = {
                'total': 0,
                'before_grounded': 0,
                'after_grounded': 0,
                'improved': 0
            }
        
        category_stats[category]['total'] += 1
        if before_grounded:
            category_stats[category]['before_grounded'] += 1
        if after_grounded:
            category_stats[category]['after_grounded'] += 1
        if improved:
            category_stats[category]['improved'] += 1
        
        improvements.append({
            'index': i + 1,
            'question': question[:80] + '...' if len(question) > 80 else question,
            'before_grounded': before_grounded,
            'after_grounded': after_grounded,
            'improved': improved,
            'before_type': before_type,
            'after_type': after_type
        })
    
    return improvements, category_stats


def print_analysis(improvements: List[Dict], category_stats: Dict[str, Dict]):
    """Print detailed analysis of improvements"""
    
    # Overall statistics
    total_questions = len(improvements)
    before_grounded = sum(1 for imp in improvements if imp['before_grounded'])
    after_grounded = sum(1 for imp in improvements if imp['after_grounded'])
    improved_count = sum(1 for imp in improvements if imp['improved'])
    
    print("\n" + "="*80)
    print("LANGGRAPH AGENTIC RAG - DATA GROUNDING IMPROVEMENT ANALYSIS")
    print("="*80)
    
    print("\n📊 OVERALL STATISTICS:")
    print(f"   Total Questions: {total_questions}")
    print(f"   \nBEFORE Data Fixes:")
    print(f"   - Grounded Answers: {before_grounded} ({before_grounded/total_questions*100:.1f}%)")
    print(f"   - Ungrounded Answers: {total_questions - before_grounded} ({(total_questions - before_grounded)/total_questions*100:.1f}%)")
    print(f"   \nAFTER Data Fixes:")
    print(f"   - Grounded Answers: {after_grounded} ({after_grounded/total_questions*100:.1f}%)")
    print(f"   - Ungrounded Answers: {total_questions - after_grounded} ({(total_questions - after_grounded)/total_questions*100:.1f}%)")
    print(f"   \n✅ IMPROVEMENT:")
    print(f"   - Questions Improved: {improved_count}")
    print(f"   - Improvement Rate: {improved_count/total_questions*100:.1f}%")
    print(f"   - Net Gain: +{after_grounded - before_grounded} grounded answers")
    
    # Category breakdown
    print("\n📈 IMPROVEMENT BY CATEGORY:")
    print("\n{:<30} {:>10} {:>10} {:>10} {:>12}".format(
        "Category", "Before", "After", "Improved", "Success %"
    ))
    print("-" * 75)
    
    for category, stats in sorted(category_stats.items()):
        print("{:<30} {:>10} {:>10} {:>10} {:>11.1f}%".format(
            category[:30],
            f"{stats['before_grounded']}/{stats['total']}",
            f"{stats['after_grounded']}/{stats['total']}",
            f"+{stats['improved']}",
            stats['after_grounded']/stats['total']*100
        ))
    
    # Most improved questions
    print("\n🎯 MOST NOTABLE IMPROVEMENTS:")
    improved_questions = [imp for imp in improvements if imp['improved']]
    for imp in improved_questions[:10]:  # Show top 10
        print(f"\n   Q{imp['index']}: {imp['question']}")
        print(f"   Before: {imp['before_type']} → After: {imp['after_type']}")
    
    # Still ungrounded questions
    still_ungrounded = [imp for imp in improvements if not imp['after_grounded']]
    print(f"\n⚠️  STILL UNGROUNDED: {len(still_ungrounded)} questions")
    
    if still_ungrounded:
        print("\nQuestions that still need data:")
        for imp in still_ungrounded[:5]:  # Show first 5
            print(f"   - Q{imp['index']}: {imp['question']}")
    
    # Data fixes applied
    print("\n🔧 DATA FIXES APPLIED:")
    print("   1. Added customer success scores for all customers")
    print("   2. Created 148 negative events for low-score customers")
    print("   3. Added 88 customer commitments and SLAs")
    print("   4. Created product success metrics")
    print("   5. Established team-product relationships")
    print("   6. Added risk mitigation strategies")
    print("   7. Updated project statuses")
    print("   8. Created roadmap items")
    print("   9. Added customer concerns")
    print("   10. Created revenue tracking for products")
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    
    if improved_count > 0:
        print(f"\n✅ The data fixes successfully improved {improved_count} questions ({improved_count/total_questions*100:.1f}%)!")
        print(f"   The system now provides grounded answers for {after_grounded} out of {total_questions} questions.")
    else:
        print("\n❌ No improvement detected. Further investigation needed.")
    
    print("\n💡 RECOMMENDATIONS:")
    if len(still_ungrounded) > 0:
        print("   1. Focus on adding data for the remaining ungrounded questions")
        print("   2. Consider enhancing the retrieval strategies for complex queries")
        print("   3. Add more detailed relationships between entities")
        print("   4. Implement query optimization for aggregation questions")
    else:
        print("   1. All questions are now grounded! 🎉")
        print("   2. Consider adding more detailed metrics for richer answers")
        print("   3. Implement caching for frequently asked questions")


def main():
    """Run the improvement analysis"""
    
    before_file = 'all_qa_results.json'
    after_file = 'all_qa_results_after_fix.json'
    
    print("\nAnalyzing improvement in data grounding...")
    
    improvements, category_stats = analyze_results(before_file, after_file)
    print_analysis(improvements, category_stats)
    
    # Save detailed analysis
    analysis_data = {
        'improvements': improvements,
        'category_stats': category_stats,
        'summary': {
            'total_questions': len(improvements),
            'before_grounded': sum(1 for imp in improvements if imp['before_grounded']),
            'after_grounded': sum(1 for imp in improvements if imp['after_grounded']),
            'improved': sum(1 for imp in improvements if imp['improved'])
        }
    }
    
    with open('grounding_improvement_analysis.json', 'w') as f:
        json.dump(analysis_data, f, indent=2)
    
    print("\n📄 Detailed analysis saved to: grounding_improvement_analysis.json")


if __name__ == "__main__":
    main()