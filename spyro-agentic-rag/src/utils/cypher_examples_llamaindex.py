"""Cypher query examples for LlamaIndex schema only"""

LLAMAINDEX_CYPHER_EXAMPLES = [
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WHERE css.score < 70
MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)-[:GENERATES]->(arr:__Entity__:REVENUE)
WITH sum(arr.amount) as lowScoreARR
MATCH (arr2:__Entity__:REVENUE)
WITH lowScoreARR, sum(arr2.amount) as totalARR
WHERE totalARR > 0
RETURN (lowScoreARR / totalARR * 100) as percentage"""
    },
    {
        "question": "Which customers have declining success scores?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WHERE css.trend = 'declining'
RETURN c.name as customer, css.score as score, css.trend as trend
ORDER BY css.score"""
    },
    {
        "question": "List all customers with their subscription values",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
RETURN c.name as customer, s.value as subscription_value
ORDER BY c.name"""
    },
    {
        "question": "Which customers have subscriptions over $5M?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
WHERE s.value CONTAINS '$' AND toInteger(replace(replace(s.value, '$', ''), 'M', '')) > 5
RETURN c.name as customer, s.value as subscription_value
ORDER BY c.name"""
    },
    {
        "question": "Show me all teams and their assigned products",
        "cypher": """
MATCH (t:__Entity__:TEAM)
OPTIONAL MATCH (t)-[:SUPPORTS]->(p:__Entity__:PRODUCT)
RETURN t.name as team, collect(p.name) as products
ORDER BY t.name"""
    },
    {
        "question": "What are the risks for each customer?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)
OPTIONAL MATCH (c)-[:HAS_RISK]->(r:__Entity__:RISK)
RETURN c.name as customer, collect(r.type + ': ' + r.severity) as risks
ORDER BY c.name"""
    },
    {
        "question": "What percentage of roadmap items are currently behind schedule?",
        "cypher": """
MATCH (ri:__Entity__:ROADMAP_ITEM)
WITH count(ri) as total
MATCH (ri:__Entity__:ROADMAP_ITEM {status: 'behind_schedule'})
WITH count(ri) as behind, total
WHERE total > 0
RETURN (behind * 100.0 / total) as percentage, behind, total"""
    },
    {
        "question": "Which teams are responsible for delayed roadmap items?",
        "cypher": """
MATCH (t:__Entity__:TEAM)-[:RESPONSIBLE_FOR]->(ri:__Entity__:ROADMAP_ITEM {status: 'behind_schedule'})
RETURN t.name as team, collect(ri.title) as delayed_items"""
    },
    {
        "question": "What are the top risks for customers with low success scores?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WHERE css.score < 70
MATCH (c)-[:HAS_RISK]->(r:__Entity__:RISK)
RETURN r.type as risk_type, r.severity as severity, count(r) as count
ORDER BY count DESC"""
    },
    {
        "question": "How much revenue is at risk from customers with SLA commitments?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SLA]->(sla:__Entity__:SLA)
MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)-[:GENERATES]->(arr:__Entity__:REVENUE)
RETURN sum(arr.amount) as revenue_at_risk"""
    },
    {
        "question": "Which features were promised to customers and what is their delivery status?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_FEATURE_PROMISE]->(fp:__Entity__:FEATURE_PROMISE)
RETURN c.name as customer, fp.name as feature, fp.status as status,
       fp.expected_date as expected_date, fp.delivery_date as delivery_date
ORDER BY c.name, fp.expected_date"""
    },
    {
        "question": "What are the top customer concerns?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_CONCERN]->(cc:__Entity__:CONCERN)
RETURN cc.type as concern_type, cc.priority as priority, 
       count(cc) as count, collect(c.name)[0..3] as sample_customers
ORDER BY count DESC"""
    },
    {
        "question": "Which teams have the highest impact on customer success scores?",
        "cypher": """
MATCH (t:__Entity__:TEAM)-[:IMPROVES_SUCCESS]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WITH t, count(css) as customers_impacted, avg(css.score) as avg_score
MATCH (t)-[:SUPPORTS]->(p:__Entity__:PRODUCT)
RETURN t.name as team, customers_impacted, avg_score, 
       t.revenue_supported as revenue_supported, collect(p.name) as products
ORDER BY customers_impacted DESC"""
    },
    {
        "question": "What is the cost-per-customer for each product by region?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:HAS_REGIONAL_COST]->(rc:__Entity__:REGIONAL_COST)-[:IN_REGION]->(r:__Entity__:REGION)
MATCH (c:__Entity__:CUSTOMER)-[:LOCATED_IN]->(r)
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
MATCH (c:__Entity__:CUSTOMER)-[:VALUES_FEATURE]->(f:__Entity__:FEATURE)<-[:HAS_FEATURE]-(p:__Entity__:PRODUCT)
WHERE c.size = 'Enterprise' OR c.name IN ['TechCorp', 'FinanceHub', 'CloudFirst', 'InnovateTech Solutions']
MATCH (f)-[:HAS_USAGE]->(fu:__Entity__:FEATURE_USAGE)
RETURN f.name as feature, p.name as product, 
       avg(fu.value_score) as avg_value_score,
       fu.adoption_rate as adoption_rate,
       count(c) as enterprise_customers_using
ORDER BY avg_value_score DESC"""
    }
]

LLAMAINDEX_CYPHER_INSTRUCTIONS = """
Important notes for generating Cypher queries with LlamaIndex schema:
1. All entities use the pattern :__Entity__:TYPE (e.g., :__Entity__:CUSTOMER)
2. Always check for division by zero using WHERE clauses
3. Use OPTIONAL MATCH when relationships might not exist
4. Remember that REVENUE.amount is stored as FLOAT (numeric value in dollars)
5. For aggregations, ensure proper grouping with WITH clauses
6. The relationship chain for ARR is: CUSTOMER -> SUBSCRIPTION -> REVENUE
7. CUSTOMER_SUCCESS_SCORE has 'score' (FLOAT) and 'trend' (STRING: 'improving', 'stable', 'declining')
8. ROADMAP_ITEM status values: 'completed', 'in_progress', 'behind_schedule', 'planned'
9. When counting or summing, always handle the case where no results might be found
10. Subscription values may be stored as strings (e.g., '$5M') and need parsing
"""