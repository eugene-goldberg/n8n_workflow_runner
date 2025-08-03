"""Compatible Cypher query examples that work with both Spyro RAG and LlamaIndex schemas"""

# These examples use flexible patterns that match both label formats
COMPATIBLE_CYPHER_EXAMPLES = [
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
MATCH (c)-[:HAS_SUCCESS_SCORE]->(css) WHERE ('CustomerSuccessScore' IN labels(css) OR ('__Entity__' IN labels(css) AND 'CUSTOMER_SUCCESS_SCORE' IN labels(css)))
WHERE css.score < 70
MATCH (c)-[:SUBSCRIBES_TO]->(s) WHERE ('SaaSSubscription' IN labels(s) OR ('__Entity__' IN labels(s) AND 'SUBSCRIPTION' IN labels(s)))
MATCH (s)-[:GENERATES]->(arr) WHERE ('AnnualRecurringRevenue' IN labels(arr) OR ('__Entity__' IN labels(arr) AND 'REVENUE' IN labels(arr)))
WITH sum(arr.amount) as lowScoreARR
MATCH (arr2) WHERE ('AnnualRecurringRevenue' IN labels(arr2) OR ('__Entity__' IN labels(arr2) AND 'REVENUE' IN labels(arr2)))
WITH lowScoreARR, sum(arr2.amount) as totalARR
WHERE totalARR > 0
RETURN (lowScoreARR / totalARR * 100) as percentage"""
    },
    {
        "question": "Which customers have declining success scores?",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
MATCH (c)-[:HAS_SUCCESS_SCORE]->(css) WHERE ('CustomerSuccessScore' IN labels(css) OR ('__Entity__' IN labels(css) AND 'CUSTOMER_SUCCESS_SCORE' IN labels(css)))
WHERE css.trend = 'declining'
RETURN c.name as customer, css.score as score, css.trend as trend
ORDER BY css.score"""
    },
    {
        "question": "List all customers with their subscription values",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(s) WHERE ('SaaSSubscription' IN labels(s) OR ('__Entity__' IN labels(s) AND 'SUBSCRIPTION' IN labels(s)))
RETURN c.name as customer, s.value as subscription_value
ORDER BY c.name"""
    },
    {
        "question": "Which customers have subscriptions over $5M?",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
MATCH (c)-[:SUBSCRIBES_TO]->(s) WHERE ('SaaSSubscription' IN labels(s) OR ('__Entity__' IN labels(s) AND 'SUBSCRIPTION' IN labels(s)))
WHERE s.value CONTAINS '$' AND toInteger(replace(replace(s.value, '$', ''), 'M', '')) > 5
RETURN c.name as customer, s.value as subscription_value
ORDER BY c.name"""
    },
    {
        "question": "Show me all teams and their assigned products",
        "cypher": """
MATCH (t) WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
OPTIONAL MATCH (t)-[:SUPPORTS]->(p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
RETURN t.name as team, collect(p.name) as products
ORDER BY t.name"""
    },
    {
        "question": "What are the risks for each customer?",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:HAS_RISK]->(r) WHERE ('Risk' IN labels(r) OR ('__Entity__' IN labels(r) AND 'RISK' IN labels(r)))
RETURN c.name as customer, collect(r.type + ': ' + r.severity) as risks
ORDER BY c.name"""
    },
    {
        "question": "Count customers by type",
        "cypher": """
MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
RETURN CASE 
    WHEN 'Customer' IN labels(c) THEN 'Spyro RAG Format'
    WHEN '__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c) THEN 'LlamaIndex Format'
    ELSE 'Unknown Format'
END as format, count(c) as count"""
    },
    {
        "question": "Show all products and their features",
        "cypher": """
MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f) WHERE ('Feature' IN labels(f) OR ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f)))
RETURN p.name as product, collect(f.name) as features
ORDER BY p.name"""
    }
]

COMPATIBLE_CYPHER_INSTRUCTIONS = """
Important notes for generating Cypher queries:

1. LABEL MATCHING: Always use the LlamaIndex format:
   - LlamaIndex: (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
   - This is the only format in the database

2. ENTITY TYPES IN LLAMAINDEX FORMAT:
   - CUSTOMER
   - PRODUCT
   - TEAM
   - RISK
   - SUBSCRIPTION
   - REVENUE
   - CUSTOMER_SUCCESS_SCORE

3. RELATIONSHIPS: Same in both schemas (e.g., SUBSCRIBES_TO, HAS_RISK, SUPPORTS)

4. PROPERTIES: Generally the same between schemas, though some may vary

5. Always use OPTIONAL MATCH when relationships might not exist

6. Handle string monetary values (e.g., '$5M') with proper parsing when needed
"""