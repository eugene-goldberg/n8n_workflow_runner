"""Enhanced Cypher examples for better Text2Cypher results"""

ENHANCED_CYPHER_EXAMPLES = [
    # Revenue and ARR queries
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
WITH c, coalesce(s.score, s.value, 100) as score,
CASE 
    WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'M' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(sub.value, '$', ''))
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue
WITH sum(revenue) as total_arr,
     sum(CASE WHEN score < 70 THEN revenue ELSE 0 END) as low_score_arr
RETURN round((low_score_arr / total_arr) * 100, 1) as percentage, low_score_arr, total_arr"""
    },
    
    # Customer risk queries
    {
        "question": "How much revenue will be at risk if TechCorp misses their SLA next month?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
AND toLower(c.name) = 'techcorp'
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
OPTIONAL MATCH (c)-[:HAS_SLA]->(sla)
WITH c, sub,
CASE 
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue,
coalesce(sla.penalty_percentage, 10) as penalty
RETURN c.name as customer, sub.value as subscription, revenue * (penalty / 100) as revenue_at_risk"""
    },
    
    # Top customers query
    {
        "question": "Who are the top 5 customers by revenue?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
WITH c, sub, coalesce(s.score, s.value, 'N/A') as success_score,
CASE 
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue_value
ORDER BY revenue_value DESC
LIMIT 5
RETURN c.name as customer, sub.value as revenue, success_score"""
    },
    
    # Risk profile queries
    {
        "question": "Which customers have high-severity risks?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
MATCH (c)-[:HAS_RISK]->(r)
WHERE r.severity IN ['High', 'Critical', 'high', 'critical']
RETURN c.name as customer, collect({type: r.type, severity: r.severity, description: r.description}) as risks"""
    },
    
    # Team cost queries
    {
        "question": "Which teams have the highest operational costs?",
        "cypher": """MATCH (t) WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
WHERE t.monthly_cost > 0 OR t.operational_cost > 0
RETURN t.name as team, 
       coalesce(t.monthly_cost, t.operational_cost, 0) as cost,
       t.revenue_supported as revenue,
       t.efficiency_ratio as efficiency
ORDER BY cost DESC
LIMIT 5"""
    },
    
    # Product satisfaction queries
    {
        "question": "What are the satisfaction scores for each product?",
        "cypher": """MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
WHERE p.satisfaction_score IS NOT NULL OR p.nps_score IS NOT NULL
RETURN p.name as product, p.satisfaction_score as satisfaction, p.nps_score as nps
ORDER BY p.satisfaction_score DESC"""
    },
    
    # Commitment queries
    {
        "question": "Which customer commitments are at risk?",
        "cypher": """MATCH (cm) WHERE ('Commitment' IN labels(cm) OR ('__Entity__' IN labels(cm) AND 'COMMITMENT' IN labels(cm)))
WHERE cm.status IN ['at_risk', 'At Risk', 'Not Met'] OR cm.risk_level = 'High'
RETURN cm.description as commitment, cm.status as status, 
       coalesce(cm.risk_level, 'High') as risk_level,
       cm.due_date as due_date"""
    },
    
    # Feature queries
    {
        "question": "What features were promised to customers?",
        "cypher": """MATCH (f) WHERE ('Feature' IN labels(f) OR ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f)))
WHERE f.promised = true OR exists(f.commitment_date)
OPTIONAL MATCH (c)-[:WAITING_FOR]->(f)
WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
RETURN f.name as feature, f.status as status, f.expected_date as expected_date,
       collect(c.name) as waiting_customers"""
    }
]

# Instructions for the LLM
ENHANCED_CYPHER_INSTRUCTIONS = """
When generating Cypher queries, follow these patterns:

1. ALWAYS use the LlamaIndex label format:
   - LlamaIndex: (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
   - This is the only format in the database

2. Handle monetary values stored as strings:
   - Values might be stored as '$8M', '$500K', etc.
   - Convert using: toFloat(replace(replace(value, '$', ''), 'M', '')) * 1000000

3. Common entity types in LlamaIndex format:
   - CUSTOMER
   - PRODUCT
   - TEAM
   - RISK
   - COMMITMENT
   - FEATURE

4. Handle optional relationships with OPTIONAL MATCH

5. Use coalesce() for fields that might be null

6. Common properties:
   - Success scores: score or value property
   - Subscriptions: value property (string format like '$8M')
   - Teams: monthly_cost, operational_cost, revenue_supported
   - Risks: severity, type, description

Return only the Cypher query without any explanation.
"""