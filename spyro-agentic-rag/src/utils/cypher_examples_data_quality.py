"""
Cypher examples that handle data quality issues
"""

DATA_QUALITY_EXAMPLES = [
    {
        "question": "How many customers have multiple products deployed?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT)
WITH c, COUNT(DISTINCT p) AS product_count
WHERE product_count > 1
RETURN COUNT(c) AS customers_with_multiple_products
"""
    },
    {
        "question": "Which teams have the most skill gaps?",
        "cypher": """
// Teams with skill gaps have fewer members or missing skills
MATCH (t:__Entity__:TEAM)
OPTIONAL MATCH (t)-[:HAS_MEMBER]->(m:__Entity__:TEAM_MEMBER)
OPTIONAL MATCH (t)-[:REQUIRES_SKILL]->(rs:__Entity__:SKILL)
OPTIONAL MATCH (t)-[:HAS_SKILL]->(hs:__Entity__:SKILL)
WITH t, COUNT(DISTINCT m) AS member_count, 
     COUNT(DISTINCT rs) AS required_skills,
     COUNT(DISTINCT hs) AS available_skills
WHERE member_count < 5 OR (required_skills - available_skills) > 0
RETURN t.name AS team, 
       member_count,
       (required_skills - available_skills) AS skill_gap
ORDER BY skill_gap DESC
"""
    },
    {
        "question": "How many customers are in each lifecycle stage?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)
// Use lifecycle_stage if available, otherwise derive from other properties
WITH c,
CASE 
    WHEN c.lifecycle_stage IS NOT NULL THEN c.lifecycle_stage
    WHEN c.stage IS NOT NULL THEN c.stage
    WHEN c.created_date > date() - duration('P90D') THEN 'New'
    WHEN c.segment = 'SMB' THEN 'Growth'
    WHEN c.segment = 'Enterprise' THEN 'Mature'
    ELSE 'Unknown'
END AS lifecycle_stage
RETURN lifecycle_stage, COUNT(c) AS customer_count
ORDER BY customer_count DESC
"""
    },
    {
        "question": "Which teams are involved in the most projects?",
        "cypher": """
MATCH (t:__Entity__:TEAM)-[:OWNS|DELIVERS|SUPPORTS]->(p:__Entity__:PROJECT)
WITH t, COUNT(DISTINCT p) AS project_count
RETURN t.name AS team, project_count
ORDER BY project_count DESC
LIMIT 10
"""
    },
    {
        "question": "What percentage of customers have executive sponsors?",
        "cypher": """
MATCH (c:__Entity__:CUSTOMER)
WITH COUNT(c) AS total_customers
OPTIONAL MATCH (c:__Entity__:CUSTOMER)-[:HAS_EXECUTIVE_SPONSOR]->(es)
WITH total_customers, COUNT(DISTINCT c) AS customers_with_sponsors
RETURN CASE 
    WHEN customers_with_sponsors = 0 THEN 0.0
    ELSE (customers_with_sponsors * 100.0 / total_customers)
END AS percentage_with_sponsors
"""
    }
]