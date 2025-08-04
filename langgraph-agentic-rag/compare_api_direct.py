#!/usr/bin/env python3
"""Compare API and direct test results to find differences"""

import json

# Load both test results
with open('api_test_results_20250803_195300.json', 'r') as f:
    api_results = json.load(f)

with open('final_verification_20250803_192533.json', 'r') as f:
    direct_results = json.load(f)

# Create lookup for direct results
direct_grounded = {}
for result in direct_results['detailed_results']:
    direct_grounded[result['index']] = result['is_grounded']

# Find differences
differences = []
for api_result in api_results['detailed_results']:
    idx = api_result['index']
    api_grounded = api_result['is_grounded']
    direct_ground = direct_grounded.get(idx, False)
    
    if api_grounded != direct_ground:
        differences.append({
            'index': idx,
            'question': api_result['question'],
            'category': api_result['category'],
            'api_grounded': api_grounded,
            'direct_grounded': direct_ground,
            'api_reason': api_result['grounding_reason'],
            'answer_preview': api_result['answer'][:200]
        })

print(f"Total API grounded: {api_results['summary']['grounded']}/60 ({api_results['summary']['success_rate']:.1f}%)")
print(f"Total Direct grounded: {direct_results['summary']['grounded']}/60 ({direct_results['summary']['success_rate']:.1f}%)")
print(f"\nFound {len(differences)} questions with different grounding results")

print("\n" + "="*80)
print("Questions where API wrongly classified as grounded (False Positives):")
print("="*80)
false_positives = 0
for diff in differences:
    if diff['api_grounded'] and not diff['direct_grounded']:
        false_positives += 1
        print(f"\nQ{diff['index']}: {diff['question']}")
        print(f"Category: {diff['category']}")
        print(f"API reason: {diff['api_reason']}")
        print(f"Answer: {diff['answer_preview']}...")

print(f"\nTotal false positives: {false_positives}")

print("\n" + "="*80)
print("Questions where API wrongly classified as NOT grounded (False Negatives):")
print("="*80)
false_negatives = 0
for diff in differences:
    if not diff['api_grounded'] and diff['direct_grounded']:
        false_negatives += 1
        print(f"\nQ{diff['index']}: {diff['question']}")
        print(f"Category: {diff['category']}")
        print(f"API reason: {diff['api_reason']}")
        print(f"Answer: {diff['answer_preview']}...")

print(f"\nTotal false negatives: {false_negatives}")

# Analyze the answers to find patterns
print("\n" + "="*80)
print("Analysis of False Positives:")
print("="*80)

# Check which negative indicators are missing from API
api_negative_indicators = [
    "no results", "not available", "no specific", "sorry",
    "unable to", "did not return", "no information",
    "couldn't find", "no relevant", "doesn't have"
]

direct_negative_indicators = [
    "no results", "not available", "no specific", "sorry",
    "unable to", "did not return", "no information",
    "does not contain", "not found", "did not yield",
    "does not specify", "cannot provide", "graph query did not",
    "no data available", "not in the database", "couldn't find",
    "no relevant", "doesn't have", "no direct"
]

missing_indicators = set(direct_negative_indicators) - set(api_negative_indicators)
print(f"\nNegative indicators missing from API: {missing_indicators}")

# Check which false positives would be caught by missing indicators
for diff in differences:
    if diff['api_grounded'] and not diff['direct_grounded']:
        answer_lower = diff['answer_preview'].lower()
        for indicator in missing_indicators:
            if indicator in answer_lower:
                print(f"\nQ{diff['index']} would be caught by '{indicator}'")
                break