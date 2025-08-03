"""
Cypher examples for properly scoped risk and filtering queries
"""

RISK_FILTERING_EXAMPLES = [
    {
        "question": "How many customers are at risk of churning?",
        "cypher": """
// Customers are at risk if they have low scores OR active risks OR declining trends
MATCH (c:__Entity__:CUSTOMER)
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
OPTIONAL MATCH (c)-[:HAS_RISK]->(r:__Entity__:RISK)
WHERE r.status = 'active'
WITH c, css.score AS score, css.trend AS trend, COUNT(r) AS risk_count
WHERE score < 60 OR trend = 'declining' OR risk_count > 0
RETURN COUNT(DISTINCT c) AS at_risk_customers
"""
    },
    {
        "question": "How many high-value customers are at risk?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
WITH c, SUM(CASE 
    WHEN s.value CONTAINS 'M' THEN toFloat(replace(s.value, '$', '')) * 1000000
    WHEN s.value CONTAINS 'K' THEN toFloat(replace(s.value, '$', '')) * 1000
    ELSE toFloat(replace(replace(s.value, '$', ''), ',', ''))
END) AS total_value
WHERE total_value > 1000000  // High-value = >$1M ARR
MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
WHERE css.score < 60 OR css.trend = 'declining'
RETURN COUNT(DISTINCT c) AS high_value_at_risk
"""
    },
    {
        "question": "How many customers are using deprecated features?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT)-[:OFFERS_FEATURE]->(f:__Entity__:FEATURE)
WHERE f.status = 'deprecated' OR f.deprecated = true
RETURN COUNT(DISTINCT c) AS customers_using_deprecated
"""
    },
    {
        "question": "How many features are blocked by technical debt?",
        "cypher": """
MATCH (f:__Entity__:FEATURE)
WHERE f.status = 'blocked' AND (f.blocked_reason = 'technical_debt' OR f.blocked_reason CONTAINS 'debt')
RETURN COUNT(f) AS blocked_features
"""
    },
    {
        "question": "What percentage of customers are on the latest product version?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT)
WITH COUNT(DISTINCT c) AS total_customers
MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT)
WHERE p.version = 'latest' OR p.is_latest = true
WITH COUNT(DISTINCT c) AS latest_customers, total_customers
RETURN (latest_customers * 100.0 / total_customers) AS percentage_on_latest
"""
    }
]