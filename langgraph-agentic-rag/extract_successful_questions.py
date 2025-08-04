#!/usr/bin/env python3
"""Extract all successfully grounded questions from the latest test results"""

import json

# Load the test results
with open('agentic_test_results_20250803_204310.json', 'r') as f:
    data = json.load(f)

# Extract grounded questions organized by category
grounded_by_category = {}
grounded_questions = []

for result in data['detailed_results']:
    if result['is_grounded']:
        category = result['category']
        question = result['question']
        
        if category not in grounded_by_category:
            grounded_by_category[category] = []
        
        grounded_by_category[category].append(question)
        grounded_questions.append({
            'index': result['index'],
            'category': category,
            'question': question
        })

# Print summary
print(f"Total grounded questions: {len(grounded_questions)}/60 ({data['summary']['success_rate']:.1f}%)")
print(f"Categories with grounded questions: {len(grounded_by_category)}")

# Create TypeScript format for webapp
print("\n" + "="*80)
print("TYPESCRIPT FORMAT FOR WEBAPP")
print("="*80)

print("""
/**
 * Business questions that have been verified to return grounded answers
 * Based on improved agentic RAG test results from 2025-08-03
 * Success rate: 88.3% (53/60 questions)
 * 
 * Improvements applied:
 * - Multi-strategy retrieval (all 3 retrievers for every query)
 * - Enhanced synthesis with creative information combination
 * - True agentic behavior - never gives up easily
 */

export const groundedQuestionsByCategory = {""")

# Group categories for better organization
category_groups = {
    "Revenue & Customer Health": ["Customer Health", "Revenue Risk Analysis"],
    "Products & Operations": ["Product Performance", "Cost & Profitability", "Operational Risk"],
    "Strategy & Delivery": ["Strategic Risk Assessment", "Project Delivery", "Roadmap & Delivery Risk"],
    "Customer & Growth": ["Customer Commitments & Satisfaction", "Growth & Expansion", "Competitive Positioning"],
    "Organization": ["Team Performance"]
}

# Output grouped categories
for group_name, categories in category_groups.items():
    print(f'  "{group_name}": {{')
    
    for category in categories:
        if category in grounded_by_category:
            questions = grounded_by_category[category]
            print(f'    "{category}": [')
            for q in questions:
                print(f'      "{q}",')
            print('    ],')
    
    print('  },')

print("};")

# Save summary
output = {
    'total_grounded': len(grounded_questions),
    'success_rate': data['summary']['success_rate'],
    'categories': grounded_by_category,
    'detailed_list': grounded_questions
}

with open('grounded_questions_88percent.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n\nGrounded questions saved to: grounded_questions_88percent.json")