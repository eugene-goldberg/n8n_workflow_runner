#!/usr/bin/env python3
"""Extract all questions that have grounded answers from the latest API test"""

import json

# Load the latest API test results
with open('api_test_results_20250803_200853.json', 'r') as f:
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
print(f"Total grounded questions: {len(grounded_questions)}/60")
print(f"Categories with grounded questions: {len(grounded_by_category)}")
print("\n" + "="*80)
print("GROUNDED QUESTIONS BY CATEGORY")
print("="*80)

for category in sorted(grounded_by_category.keys()):
    questions = grounded_by_category[category]
    print(f"\n{category} ({len(questions)} questions):")
    for i, q in enumerate(questions, 1):
        print(f"  {i}. {q}")

# Create TypeScript format for webapp
print("\n" + "="*80)
print("TYPESCRIPT FORMAT FOR WEBAPP")
print("="*80)

print("\nexport const groundedQuestions = {")
for category in sorted(grounded_by_category.keys()):
    questions = grounded_by_category[category]
    print(f'  "{category}": [')
    for q in questions:
        print(f'    "{q}",')
    print('  ],')
print("};")

# Save to file
output = {
    'total_grounded': len(grounded_questions),
    'categories': grounded_by_category,
    'detailed_list': grounded_questions
}

with open('grounded_questions.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nGrounded questions saved to: grounded_questions.json")