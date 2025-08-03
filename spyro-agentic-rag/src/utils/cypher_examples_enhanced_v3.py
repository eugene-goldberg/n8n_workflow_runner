"""
Enhanced Cypher Examples v3 - Based on Actual Neo4j Schema
These examples demonstrate real patterns from the data model to guide autonomous query generation
"""

ENHANCED_CYPHER_EXAMPLES = [
    # Customer Success and Risk Queries
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """// Success scores are in separate nodes, subscriptions have string values
MATCH (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(score_node)
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
WITH c, 
     coalesce(score_node.score, 100) as success_score,
     CASE 
         WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'M' THEN 
              toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
         WHEN sub.value CONTAINS '$' THEN 
              toFloat(replace(sub.value, '$', ''))
         ELSE 0
     END as subscription_value
WITH sum(subscription_value) as total_arr,
     sum(CASE WHEN success_score < 70 THEN subscription_value ELSE 0 END) as at_risk_arr
WHERE total_arr > 0
RETURN round((at_risk_arr / total_arr) * 100, 1) as percentage_at_risk,
       at_risk_arr as arr_below_70,
       total_arr as total_arr"""
    },
    
    {
        "question": "How many active risks are unmitigated and what is their financial impact?",
        "cypher": """// Risks use 'active' status and 'impact_amount' property
MATCH (r) WHERE ('__Entity__' IN labels(r) AND 'RISK' IN labels(r))
AND r.status = 'active'  // Not 'Unmitigated' - use actual status values
RETURN count(r) as active_risk_count,
       sum(r.impact_amount) as total_financial_impact,
       collect(r.description)[..5] as sample_risks"""
    },
    
    # Product and Feature Queries
    {
        "question": "Which features have high adoption but low satisfaction?",
        "cypher": """// Features have adoption_rate, but satisfaction is in separate nodes
MATCH (f) WHERE ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
AND f.adoption_rate IS NOT NULL
// Note: Satisfaction scores are in SATISFACTION_SCORE nodes
// This example shows features by adoption when satisfaction link doesn't exist
WITH f
ORDER BY f.adoption_rate DESC
RETURN f.name as feature,
       f.adoption_rate as adoption_percentage,
       f.active_users as active_users
LIMIT 10"""
    },
    
    {
        "question": "What is the retention rate by product?",
        "cypher": """// Calculate retention from subscription data and renewal probability
MATCH (c)-[:USES]->(p)
WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
AND ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p))
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(s)
WHERE ('__Entity__' IN labels(s) AND 'SUBSCRIPTION' IN labels(s))
WITH p.name as product,
     count(distinct c) as total_customers,
     count(distinct CASE WHEN s.status = 'Active' THEN c END) as active_customers,
     avg(s.renewal_probability) as avg_renewal_probability
RETURN product,
       total_customers,
       active_customers,
       CASE WHEN total_customers > 0 
            THEN round((active_customers * 100.0) / total_customers, 1)
            ELSE 0 END as retention_rate_percent,
       round(avg_renewal_probability * 100, 1) as avg_renewal_probability_percent
ORDER BY retention_rate_percent DESC"""
    },
    
    # Team and Cost Queries
    {
        "question": "Which teams have the highest operational costs relative to efficiency?",
        "cypher": """// Most teams use monthly_cost; efficiency_ratio measures productivity
MATCH (t) WHERE ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t))
// Use COALESCE to handle teams with operational_cost or monthly_cost
WITH t,
     coalesce(t.operational_cost, t.monthly_cost * 12, 0) as annual_cost,
     t.efficiency_ratio as efficiency,
     t.revenue_supported as revenue_supported
WHERE annual_cost > 0 AND efficiency IS NOT NULL
RETURN t.name as team,
       annual_cost,
       efficiency as efficiency_ratio,
       revenue_supported,
       round(annual_cost / efficiency, 0) as cost_per_efficiency_point
ORDER BY cost_per_efficiency_point DESC
LIMIT 10"""
    },
    
    # Financial Projections
    {
        "question": "What are the quarterly revenue projections?",
        "cypher": """// Calculate projections from current subscriptions and renewal probabilities
MATCH (s) WHERE ('__Entity__' IN labels(s) AND 'SUBSCRIPTION' IN labels(s))
AND s.status = 'Active'
WITH s,
     CASE 
         WHEN s.value CONTAINS '$' AND s.value CONTAINS 'M' THEN 
              toFloat(replace(replace(s.value, '$', ''), 'M', '')) * 1000000
         ELSE 0
     END as annual_value,
     s.renewal_probability as renewal_prob,
     s.end_date as end_date
// Calculate quarterly projections based on renewal probability
WITH sum(annual_value / 4) as current_quarter,
     sum((annual_value / 4) * renewal_prob) as next_quarter,
     sum((annual_value / 4) * renewal_prob * renewal_prob) as quarter_plus_2
RETURN round(current_quarter) as q1_revenue,
       round(next_quarter) as q2_revenue_projected,
       round(quarter_plus_2) as q3_revenue_projected"""
    },
    
    # Customer Issue Resolution
    {
        "question": "What is the average time to resolve customer issues?",
        "cypher": """// Events track issues but often lack resolution dates
MATCH (e) WHERE ('__Entity__' IN labels(e) AND 'EVENT' IN labels(e))
AND e.type IN ['support_escalation', 'performance_issue', 'security_incident']
// Note: Most events lack resolution dates, so we check what data exists
RETURN e.type as issue_type,
       count(e) as issue_count,
       count(e.date) as issues_with_dates,
       collect(e.description)[..3] as sample_issues"""
    },
    
    # Comprehensive Customer Analysis
    {
        "question": "Which customers are at risk of churn?",
        "cypher": """// Combine multiple risk factors: low scores, declining trends, active risks
MATCH (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(score)
OPTIONAL MATCH (c)-[:HAS_RISK]->(risk) WHERE risk.status = 'active'
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
WITH c,
     score.score as success_score,
     score.trend as score_trend,
     count(risk) as active_risks,
     sub.renewal_probability as renewal_prob
WHERE success_score < 60 
   OR score_trend = 'declining' 
   OR active_risks > 0
   OR renewal_prob < 0.7
RETURN c.name as customer,
       success_score,
       score_trend,
       active_risks,
       renewal_prob,
       CASE 
           WHEN success_score < 40 OR active_risks > 2 THEN 'High Risk'
           WHEN success_score < 60 OR score_trend = 'declining' THEN 'Medium Risk'
           ELSE 'Low Risk'
       END as churn_risk_level
ORDER BY success_score ASC NULLS LAST"""
    },
    
    # Modern Syntax Examples
    {
        "question": "Which products have the most customers?",
        "cypher": """// Use IS NOT NULL instead of EXISTS
MATCH (c)-[:USES]->(p)
WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
AND ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p))
AND c.name IS NOT NULL  // Modern syntax - not EXISTS(c.name)
RETURN p.name as product,
       count(distinct c) as customer_count,
       collect(distinct c.name)[..5] as sample_customers
ORDER BY customer_count DESC"""
    },
    
    # Handling Sparse Data
    {
        "question": "What data do we have about customer events?",
        "cypher": """// Many relationships might not exist - use OPTIONAL MATCH
MATCH (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
OPTIONAL MATCH (c)-[:EXPERIENCED]->(e:EVENT)
OPTIONAL MATCH (c)-[:HAS_CONCERN]->(concern:CONCERN)
WITH c.name as customer,
     count(distinct e) as event_count,
     count(distinct concern) as concern_count,
     collect(distinct e.type)[..3] as event_types
WHERE event_count > 0 OR concern_count > 0
RETURN customer, event_count, concern_count, event_types
ORDER BY event_count DESC
LIMIT 10"""
    }
]

# System instructions for using these examples
CYPHER_GENERATION_INSTRUCTIONS = """
When generating Cypher queries:
1. Always use the LlamaIndex label format: ('__Entity__' IN labels(n) AND 'TYPE' IN labels(n))
2. Financial values are often strings - parse them with CASE statements
3. Use OPTIONAL MATCH for relationships that might not exist
4. Check actual property names: impact_amount not potential_impact, active not Unmitigated
5. Modern syntax: use IS NOT NULL instead of EXISTS()
6. Many metrics require calculation rather than simple retrieval
7. Entity labels are UPPERCASE (CUSTOMER, PRODUCT, RISK, etc.)
8. Always verify relationships exist before traversing them
"""