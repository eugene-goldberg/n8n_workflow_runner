"""Cypher query examples for Text2Cypher retriever"""

CYPHER_EXAMPLES = [
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """
MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
WHERE css.score < 70
MATCH (c)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
WITH sum(arr.amount) as lowScoreARR
MATCH (arr2:AnnualRecurringRevenue)
WITH lowScoreARR, sum(arr2.amount) as totalARR
WHERE totalARR > 0
RETURN (lowScoreARR / totalARR * 100) as percentage"""
    },
    {
        "question": "Which customers have declining success scores?",
        "cypher": """
MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
WHERE css.trend = 'declining'
RETURN c.name as customer, css.score as score, css.trend as trend
ORDER BY css.score"""
    },
    {
        "question": "What percentage of roadmap items are currently behind schedule?",
        "cypher": """
MATCH (ri:RoadmapItem)
WITH count(ri) as total
MATCH (ri:RoadmapItem {status: 'behind_schedule'})
WITH count(ri) as behind, total
WHERE total > 0
RETURN (behind * 100.0 / total) as percentage, behind, total"""
    },
    {
        "question": "Which teams are responsible for delayed roadmap items?",
        "cypher": """
MATCH (t:Team)-[:RESPONSIBLE_FOR]->(ri:RoadmapItem {status: 'behind_schedule'})
RETURN t.name as team, collect(ri.title) as delayed_items"""
    },
    {
        "question": "What are the top risks for customers with low success scores?",
        "cypher": """
MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
WHERE css.score < 70
MATCH (c)-[:HAS_RISK]->(r:Risk)
RETURN r.type as risk_type, r.severity as severity, count(r) as count
ORDER BY count DESC"""
    },
    {
        "question": "How much revenue is at risk from customers with SLA commitments?",
        "cypher": """
MATCH (c:Customer)-[:HAS_SLA]->(sla:SLA)
MATCH (c)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
RETURN sum(arr.amount) as revenue_at_risk"""
    },
    {
        "question": "Which features were promised to customers and what is their delivery status?",
        "cypher": """
MATCH (c:Customer)-[:HAS_FEATURE_PROMISE]->(fp:FeaturePromise)
RETURN c.name as customer, fp.name as feature, fp.status as status,
       fp.expected_date as expected_date, fp.delivery_date as delivery_date
ORDER BY c.name, fp.expected_date"""
    },
    {
        "question": "What are the top customer concerns?",
        "cypher": """
MATCH (c:Customer)-[:HAS_CONCERN]->(cc:CustomerConcern)
RETURN cc.type as concern_type, cc.priority as priority, 
       count(cc) as count, collect(c.name)[0..3] as sample_customers
ORDER BY count DESC"""
    },
    {
        "question": "Which teams have the highest impact on customer success scores?",
        "cypher": """
MATCH (t:Team)-[:IMPROVES_SUCCESS]->(css:CustomerSuccessScore)
WITH t, count(css) as customers_impacted, avg(css.score) as avg_score
MATCH (t)-[:SUPPORTS]->(p:Product)
RETURN t.name as team, customers_impacted, avg_score, 
       t.revenue_supported as revenue_supported, collect(p.name) as products
ORDER BY customers_impacted DESC"""
    },
    {
        "question": "What is the cost-per-customer for each product by region?",
        "cypher": """
MATCH (p:Product)-[:HAS_REGIONAL_COST]->(rc:RegionalCost)-[:IN_REGION]->(r:Region)
MATCH (c:Customer)-[:LOCATED_IN]->(r)
MATCH (c)-[:USES]->(p)
WITH p, r, rc, count(c) as customer_count
RETURN p.name as product, r.name as region, 
       rc.base_cost_per_customer * rc.cost_multiplier as cost_per_customer,
       customer_count
ORDER BY p.name, r.name"""
    },
    {
        "question": "Which features drive the most value for enterprise customers?",
        "cypher": """
MATCH (c:Customer)-[:VALUES_FEATURE]->(f:Feature)<-[:HAS_FEATURE]-(p:Product)
WHERE c.size = 'Enterprise' OR c.name IN ['TechCorp', 'FinanceHub', 'CloudFirst']
MATCH (f)-[:HAS_USAGE]->(fu:FeatureUsage)
RETURN f.name as feature, p.name as product, 
       avg(fu.value_score) as avg_value_score,
       fu.adoption_rate as adoption_rate,
       count(c) as enterprise_customers_using
ORDER BY avg_value_score DESC"""
    },
    {
        "question": "Which customers have unmet SLA commitments in the last quarter?",
        "cypher": """
MATCH (c:Customer)-[:HAS_SLA]->(sla:SLA)-[:HAS_PERFORMANCE]->(sp:SLAPerformance)
WHERE sp.month >= date() - duration({months: 3}) AND sp.met = false
RETURN c.name as customer, count(sp) as violations, 
       sum(sp.penalty_applied) as total_penalty_percentage,
       collect(sp.month) as violation_months
ORDER BY violations DESC"""
    }
]

CYPHER_INSTRUCTIONS = """
Important notes for generating Cypher queries:
1. Always check for division by zero using WHERE clauses
2. Use OPTIONAL MATCH when relationships might not exist
3. Remember that ARR.amount is stored as FLOAT (numeric value in dollars)
4. For aggregations, ensure proper grouping with WITH clauses
5. The relationship chain for ARR is: Customer -> SaaSSubscription -> AnnualRecurringRevenue
6. CustomerSuccessScore has 'score' (FLOAT) and 'trend' (STRING: 'improving', 'stable', 'declining')
7. RoadmapItem status values: 'completed', 'in_progress', 'behind_schedule', 'planned'
8. When counting or summing, always handle the case where no results might be found
"""