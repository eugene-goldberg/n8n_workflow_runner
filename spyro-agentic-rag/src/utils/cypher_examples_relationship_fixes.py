"""
Additional Cypher examples for relationship-centric queries
These examples show how to query the migrated entities
"""

RELATIONSHIP_MODEL_EXAMPLES = [
    {
        "question": "What are the projected quarterly revenue trends for the next fiscal year?",
        "cypher": """
MATCH (p:__Entity__:PROJECTION)-[:FOR_PERIOD]->(q:__Entity__:QUARTER)
WHERE q.year = 2025
MATCH (p)-[:PROJECTS]->(m:__Entity__:METRIC)
WHERE m.type = 'revenue'
RETURN q.name AS quarter, q.year AS year, m.value AS projected_revenue, m.confidence AS confidence
ORDER BY q.name
"""
    },
    {
        "question": "What percentage of revenue is recurring vs one-time?",
        "cypher": """
MATCH (r:__Entity__:REVENUE)-[:HAS_TYPE]->(rt:__Entity__:REVENUE_TYPE)
WITH rt.name AS revenue_type, SUM(r.amount) AS total
WITH COLLECT({type: revenue_type, amount: total}) AS revenues, SUM(total) AS grand_total
UNWIND revenues AS rev
RETURN rev.type AS revenue_type, 
       rev.amount AS amount,
       (rev.amount * 100.0 / grand_total) AS percentage
"""
    },
    {
        "question": "Which marketing channels have the highest ROI?",
        "cypher": """
MATCH (mc:__Entity__:MARKETING_CHANNEL)-[:ACHIEVES]->(pm:__Entity__:PERFORMANCE_METRIC)
WHERE pm.type = 'ROI'
RETURN mc.name AS channel, pm.value AS roi, pm.unit AS unit
ORDER BY pm.value DESC
"""
    }
]