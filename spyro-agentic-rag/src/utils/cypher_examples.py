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