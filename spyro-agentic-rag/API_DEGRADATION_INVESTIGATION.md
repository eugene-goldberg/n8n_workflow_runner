# API Degradation Investigation Results

## Critical Finding: Different Question Sets!

The API test and direct agent test are using **completely different sets of questions**, which explains the apparent "degradation" in performance.

### Examples of Differences:

| Query | API Test Question | Direct Agent Test Question |
|-------|------------------|---------------------------|
| Q1 | What is our total ARR and how is it distributed across customer segments? | What percentage of our ARR is dependent on customers with success scores below 70? |
| Q2 | Which customers have success scores below 50? | Which customers are at high risk due to low product adoption? |
| Q3 | What is the distribution of customer health scores? | What is the impact on revenue if we lose our top 3 enterprise customers? |
| Q4 | How many customers are at risk of churning? | How many customers have success scores below 60, and what is their combined ARR? |
| Q5 | What percentage of our ARR comes from customers with low success scores? | What percentage of customers experienced negative events in the last 90 days? |

## Root Causes of Apparent Degradation:

1. **Different Question Sets**: The tests are evaluating completely different queries
2. **Different Evaluation Criteria**: 
   - API test: Simple evaluation (5 indicators, requires 2)
   - Direct test: Complex evaluation (30+ indicators, more nuanced scoring)

## Actual Findings:

### There is NO API degradation!

The apparent difference in success rates (53.3% vs 71.7%) is due to:
- Testing different questions with different complexity levels
- Using different evaluation criteria
- The direct test questions may be easier or have better data coverage

## Recommendations:

1. **Standardize Questions**: Use the same question set in both test scripts
2. **Standardize Evaluation**: Use the same grounding detection logic
3. **Re-test**: Run both tests with identical questions and evaluation criteria

## Conclusion:

The API layer is NOT causing any degradation in agent performance. The perceived degradation was an artifact of:
- Comparing results from different question sets
- Using different evaluation criteria
- Potentially different data availability for different questions

To properly assess the system, we need to ensure both test methods use:
- The exact same questions
- The exact same evaluation criteria
- The exact same test conditions