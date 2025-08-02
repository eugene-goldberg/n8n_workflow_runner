#!/usr/bin/env python3
"""Test actual success rate of the enhanced agent"""
import requests
import time

# Test questions and expected data points
tests = [
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "expected": ["%", "ARR"],
        "category": "Revenue"
    },
    {
        "question": "How much revenue will be at risk if TechCorp misses their SLA next month?",
        "expected": ["$", "800"],
        "category": "Revenue"
    },
    {
        "question": "Which customers generate 80% of our revenue, and what are their current risk profiles?",
        "expected": ["TechCorp", "HealthNet", "$"],
        "category": "Revenue"
    },
    {
        "question": "What are the top 5 customers by revenue?",
        "expected": ["$", "TechCorp", "GlobalRetail"],
        "category": "Revenue"
    },
    {
        "question": "Which teams have the highest operational costs relative to revenue?",
        "expected": ["Security Team", "$"],
        "category": "Cost"
    },
    {
        "question": "How much does it cost to run each product across all regions?",
        "expected": ["SpyroSecure", "$"],
        "category": "Cost"
    },
    {
        "question": "Which customer commitments are at high risk?",
        "expected": ["TechCorp", "risk"],
        "category": "Risk"
    },
    {
        "question": "What are the satisfaction scores for each product?",
        "expected": ["product", "score"],
        "category": "Product"
    },
    {
        "question": "Which products have the highest customer satisfaction scores?",
        "expected": ["product", "satisfaction"],
        "category": "Product"
    },
    {
        "question": "Which features were promised to customers, and what is their delivery status?",
        "expected": ["feature", "status"],
        "category": "Product"
    }
]

def is_data_grounded(answer, expected_terms):
    """Check if answer contains expected data points"""
    answer_lower = answer.lower()
    
    # Generic response indicators
    generic_phrases = [
        "i couldn't find",
        "not directly available",
        "unable to retrieve",
        "no specific data",
        "might want to check",
        "internal project management"
    ]
    
    # Check for generic responses
    if any(phrase in answer_lower for phrase in generic_phrases):
        return False
    
    # Check for expected data points
    found_terms = sum(1 for term in expected_terms if term.lower() in answer_lower)
    return found_terms >= len(expected_terms) // 2  # At least half the expected terms

def test_query(question):
    """Test a single query"""
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": question},
            headers={"x-api-key": "spyro-secret-key-123"},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("answer", "")
        return f"Error: HTTP {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

# Run tests
print("Testing Enhanced Agent Success Rate")
print("=" * 80)

results = {"success": 0, "total": 0, "by_category": {}}

for test in tests:
    category = test["category"]
    if category not in results["by_category"]:
        results["by_category"][category] = {"success": 0, "total": 0}
    
    print(f"\n{test['question']}")
    answer = test_query(test["question"])
    
    is_success = is_data_grounded(answer, test["expected"])
    status = "✓ SUCCESS" if is_success else "✗ FAILED"
    
    print(f"Status: {status}")
    print(f"Answer: {answer[:150]}...")
    
    results["total"] += 1
    results["by_category"][category]["total"] += 1
    
    if is_success:
        results["success"] += 1
        results["by_category"][category]["success"] += 1
    
    time.sleep(1)

# Print summary
print("\n" + "=" * 80)
print("RESULTS BY CATEGORY:")
for category, stats in results["by_category"].items():
    rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
    print(f"{category}: {stats['success']}/{stats['total']} ({rate:.0f}%)")

overall_rate = (results["success"] / results["total"]) * 100
print(f"\nOVERALL SUCCESS RATE: {results['success']}/{results['total']} ({overall_rate:.0f}%)")

if overall_rate >= 83:
    print("✓ ACHIEVED TARGET OF >83%!")
else:
    print(f"✗ Need {83 - overall_rate:.0f}% improvement to reach target")