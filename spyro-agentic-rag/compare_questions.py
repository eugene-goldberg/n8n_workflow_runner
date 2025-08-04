"""Compare questions between API and direct test scripts"""

# From test_single_api_question.py (1-indexed)
API_QUESTIONS = {
    1: "What is our total ARR and how is it distributed across customer segments?",
    2: "Which customers have success scores below 50?",
    3: "What is the distribution of customer health scores?",
    4: "How many customers are at risk of churning?",
    5: "What percentage of our ARR comes from customers with low success scores?",
}

# From test_single_business_query.py (0-indexed list)
DIRECT_QUESTIONS = [
    "What percentage of our ARR is dependent on customers with success scores below 70?",  # 0 -> Q1
    "Which customers are at high risk due to low product adoption?",  # 1 -> Q2
    "What is the impact on revenue if we lose our top 3 enterprise customers?",  # 2 -> Q3
    "How many customers have success scores below 60, and what is their combined ARR?",  # 3 -> Q4
    "What percentage of customers experienced negative events in the last 90 days?",  # 4 -> Q5
]

print("Comparing first 5 questions:")
print("=" * 80)

for i in range(1, 6):
    api_q = API_QUESTIONS.get(i, "N/A")
    direct_q = DIRECT_QUESTIONS[i-1] if i-1 < len(DIRECT_QUESTIONS) else "N/A"
    match = "✅ MATCH" if api_q == direct_q else "❌ DIFFERENT"
    
    print(f"\nQ{i}:")
    print(f"API:    {api_q}")
    print(f"Direct: {direct_q}")
    print(f"Status: {match}")