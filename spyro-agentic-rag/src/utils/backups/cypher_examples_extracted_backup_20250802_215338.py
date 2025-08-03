"""Cypher query examples for LlamaExtract schema entities"""

EXTRACTED_CYPHER_EXAMPLES = [
    # Cost Analysis Queries
    {
        "question": "How much does it cost to run each product across all regions?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
WITH p.name as product, sum(c.total_monthly_cost) as total_cost,
     collect(DISTINCT r.name + ': $' + toString(coalesce(c.total_monthly_cost, 0))) as regional_costs
RETURN product, total_cost, regional_costs
ORDER BY total_cost DESC"""
    },
    {
        "question": "What is the cost-per-customer for each product, and how does it vary by region?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
WHERE c.cost_per_customer IS NOT NULL
RETURN p.name as product, r.name as region, 
       c.cost_per_customer as cost_per_customer,
       c.customer_count as customers,
       c.infrastructure_cost as infra_cost,
       c.support_cost as support_cost
ORDER BY p.name, c.cost_per_customer DESC"""
    },
    {
        "question": "Which teams have the highest operational costs relative to the revenue they support?",
        "cypher": """
MATCH (t:__Entity__:TEAM)
WHERE t.monthly_cost IS NOT NULL AND t.revenue_supported IS NOT NULL AND t.revenue_supported > 0
WITH t.name as team, t.monthly_cost as cost, t.revenue_supported as revenue,
     t.efficiency_ratio as efficiency,
     (t.monthly_cost / t.revenue_supported * 100) as cost_to_revenue_ratio
RETURN team, cost, revenue, efficiency, cost_to_revenue_ratio
ORDER BY cost_to_revenue_ratio DESC"""
    },
    
    # Customer Commitment Queries
    {
        "question": "What are the top customer commitments, and what are the current risks to achieving them?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
WHERE com.risk_level IN ['High', 'Critical'] OR com.current_status = 'Delayed'
RETURN c.name as customer, com.feature_name as feature,
       com.risk_level as risk, com.revenue_at_risk as revenue_at_risk,
       com.current_status as status, com.expected_delivery as delivery_date,
       com.responsible_team as team
ORDER BY com.revenue_at_risk DESC, com.risk_level DESC"""
    },
    {
        "question": "Which features were promised to customers, and what is their delivery status?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
RETURN c.name as customer, com.feature_name as feature,
       com.promise_date as promised, com.expected_delivery as expected,
       com.current_status as status, com.completion_percentage as completion,
       com.responsible_team as team
ORDER BY com.expected_delivery, c.name"""
    },
    {
        "question": "How much revenue is at risk from customers with high-risk commitments?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
WHERE com.risk_level IN ['High', 'Critical'] AND com.revenue_at_risk IS NOT NULL
WITH c, sum(com.revenue_at_risk) as total_risk
MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
RETURN c.name as customer, s.value as subscription_value, 
       total_risk as revenue_at_risk
ORDER BY total_risk DESC"""
    },
    
    # SLA & Performance Queries
    {
        "question": "Which customers have unmet SLA commitments in the last quarter?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SLA]->(sla:__Entity__:SLA)
WHERE sla.status = 'Violated' OR sla.actual_performance < sla.target
RETURN c.name as customer, sla.product as product,
       sla.target as sla_target, sla.actual_performance as actual,
       sla.status as status
ORDER BY c.name"""
    },
    {
        "question": "How much revenue will be at risk if TechCorp misses their SLA next month?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER {name: 'TechCorp'})-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
OPTIONAL MATCH (c)-[:HAS_SLA]->(sla:__Entity__:SLA)
WITH c, s, collect(sla) as slas
RETURN c.name as customer, s.value as subscription_value,
       CASE WHEN '$' IN s.value 
            THEN toInteger(replace(replace(s.value, '$', ''), 'M', '')) * 1000000
            ELSE 0
       END as revenue_at_risk,
       size(slas) as sla_count"""
    },
    
    # Product Health & Satisfaction Queries
    {
        "question": "Which products have the highest customer satisfaction scores?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:HAS_SATISFACTION_SCORE]->(s:__Entity__:SATISFACTION_SCORE)
RETURN p.name as product, s.average_score as satisfaction_score,
       s.nps_score as nps, s.score_trend as trend,
       s.customer_count as customers
ORDER BY s.average_score DESC"""
    },
    {
        "question": "Which products have the most operational issues impacting customer success?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_ISSUE]->(i:__Entity__:OPERATIONAL_ISSUE)
WITH p.name as product, count(i) as issue_count,
     collect(DISTINCT i.severity) as severities,
     sum(CASE WHEN i.severity = 'Critical' THEN 1 ELSE 0 END) as critical_count,
     sum(CASE WHEN i.severity = 'High' THEN 1 ELSE 0 END) as high_count
RETURN product, issue_count, critical_count, high_count, severities
ORDER BY critical_count DESC, high_count DESC, issue_count DESC"""
    },
    
    # Feature Adoption Queries
    {
        "question": "What is the adoption rate of new features released in the last 6 months?",
        "cypher": """
MATCH (p:__Entity__:PRODUCT)-[:OFFERS_FEATURE]->(f:__Entity__:FEATURE)
WHERE f.days_since_release <= 180 AND f.adoption_rate IS NOT NULL
RETURN p.name as product, f.name as feature,
       f.adoption_rate as adoption_percentage,
       f.target_users as target, f.actual_users as actual,
       f.monthly_growth_rate as growth_rate
ORDER BY f.adoption_rate DESC"""
    },
    
    # Revenue Impact Queries
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WHERE css.score < 70
MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
WITH sum(CASE WHEN '$' IN s.value 
              THEN toInteger(replace(replace(s.value, '$', ''), 'M', '')) * 1000000
              ELSE 0 END) as lowScoreARR
MATCH (c2:__Entity__:CUSTOMER)-[:SUBSCRIBES_TO]->(s2:__Entity__:SUBSCRIPTION)
WITH lowScoreARR, sum(CASE WHEN '$' IN s2.value 
                            THEN toInteger(replace(replace(s2.value, '$', ''), 'M', '')) * 1000000
                            ELSE 0 END) as totalARR
WHERE totalARR > 0
RETURN round((lowScoreARR / totalARR * 100), 2) as percentage,
       lowScoreARR, totalARR"""
    },
    {
        "question": "Which customers generate 80% of our revenue?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
WITH c, s, CASE WHEN '$' IN s.value 
                THEN toInteger(replace(replace(s.value, '$', ''), 'M', '')) * 1000000
                ELSE 0 END as revenue
ORDER BY revenue DESC
WITH collect({customer: c.name, revenue: revenue}) as customers, sum(revenue) as total
WITH customers, total, total * 0.8 as target
UNWIND range(0, size(customers)-1) as idx
WITH customers[0..idx+1] as topCustomers, 
     reduce(s = 0, x IN customers[0..idx+1] | s + x.revenue) as runningTotal,
     target
WHERE runningTotal >= target
WITH topCustomers[0..size(topCustomers)] as finalList
UNWIND finalList as customer
MATCH (c:__Entity__:CUSTOMER {name: customer.customer})
OPTIONAL MATCH (c)-[:HAS_RISK]->(r:__Entity__:RISK)
RETURN customer.customer as name, customer.revenue as revenue,
       collect(DISTINCT r.severity) as risks"""
    }
]

EXTRACTED_CYPHER_INSTRUCTIONS = """
When generating Cypher queries for SpyroSolutions data, use these LlamaIndex schema patterns:

ENTITIES (all prefixed with :__Entity__:):
- CUSTOMER: Has name, may have success scores, subscriptions, commitments, SLAs
- PRODUCT: Has name, operational costs, satisfaction scores, features
- REGION: Geographic regions for cost analysis
- TEAM: Has name, monthly_cost, revenue_supported, efficiency_ratio
- OPERATIONAL_COST: Has total_monthly_cost, cost_per_customer, infrastructure_cost, support_cost
- COMMITMENT: Customer feature commitments with risk_level, revenue_at_risk, status
- SLA: Service level agreements with target, actual_performance, status
- SATISFACTION_SCORE: Product satisfaction with average_score, nps_score, trend
- FEATURE: Product features with adoption_rate, target_users, actual_users

RELATIONSHIPS:
- (CUSTOMER)-[:HAS_COMMITMENT]->(COMMITMENT)
- (CUSTOMER)-[:HAS_SLA]->(SLA)
- (CUSTOMER)-[:SUBSCRIBES_TO]->(SUBSCRIPTION)
- (PRODUCT)-[:HAS_OPERATIONAL_COST]->(OPERATIONAL_COST)
- (OPERATIONAL_COST)-[:INCURS_COST]->(REGION)
- (PRODUCT)-[:HAS_SATISFACTION_SCORE]->(SATISFACTION_SCORE)
- (PRODUCT)-[:OFFERS_FEATURE]->(FEATURE)
- (TEAM)-[:RESPONSIBLE_FOR]->(COMMITMENT)

KEY PROPERTIES:
- Costs: total_monthly_cost, cost_per_customer, infrastructure_cost, support_cost
- Commitments: feature_name, risk_level, revenue_at_risk, current_status, completion_percentage
- Teams: monthly_cost, revenue_supported, efficiency_ratio
- Satisfaction: average_score, nps_score, score_trend
- Features: adoption_rate, target_users, actual_users, monthly_growth_rate

When handling subscription values, they are stored as strings like "$8M", so convert them:
toInteger(replace(replace(s.value, '$', ''), 'M', '')) * 1000000
"""