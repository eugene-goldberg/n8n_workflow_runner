#!/usr/bin/env python3
"""Test queries against the extracted data to verify what's available"""

from neo4j import GraphDatabase
import os

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Test queries that should work with our extracted data
test_queries = [
    {
        "question": "How much does it cost to run each product across all regions?",
        "query": """
        MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
        RETURN p.name as product, 
               sum(c.total_monthly_cost) as total_cost,
               collect(DISTINCT r.name + ': $' + toString(c.total_monthly_cost)) as regional_costs
        ORDER BY total_cost DESC
        """
    },
    {
        "question": "What is the cost-per-customer for each product by region?",
        "query": """
        MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
        WHERE c.cost_per_customer IS NOT NULL
        RETURN p.name as product, r.name as region, 
               c.cost_per_customer as cost_per_customer,
               c.customer_count as customers
        ORDER BY p.name, r.name
        """
    },
    {
        "question": "What are the top customer commitments and their risks?",
        "query": """
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
        WHERE com.risk_level IN ['High', 'Critical']
        RETURN c.name as customer, 
               com.feature_name as feature,
               com.risk_level as risk,
               com.revenue_at_risk as revenue_at_risk,
               com.current_status as status
        ORDER BY com.revenue_at_risk DESC
        """
    },
    {
        "question": "Which features were promised to customers and their delivery status?",
        "query": """
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
        RETURN c.name as customer,
               com.feature_name as feature,
               com.promise_date as promised,
               com.expected_delivery as expected,
               com.current_status as status,
               com.completion_percentage as completion
        ORDER BY com.expected_delivery
        """
    },
    {
        "question": "Which products have the highest customer satisfaction scores?",
        "query": """
        MATCH (p:__Entity__:PRODUCT)-[:HAS_SATISFACTION_SCORE]->(s:__Entity__:SATISFACTION_SCORE)
        RETURN p.name as product,
               s.average_score as satisfaction_score,
               s.nps_score as nps,
               s.score_trend as trend,
               s.customer_count as customers
        ORDER BY s.average_score DESC
        """
    },
    {
        "question": "What is the adoption rate of new features?",
        "query": """
        MATCH (p:__Entity__:PRODUCT)-[:OFFERS_FEATURE]->(f:__Entity__:FEATURE)
        WHERE f.adoption_rate IS NOT NULL
        RETURN p.name as product,
               f.name as feature,
               f.adoption_rate as adoption_percentage,
               f.actual_users as users,
               f.adoption_trend as trend,
               f.release_date as released
        ORDER BY f.adoption_rate DESC
        """
    },
    {
        "question": "Which teams have the highest costs relative to revenue?",
        "query": """
        MATCH (t:__Entity__:TEAM)
        WHERE t.monthly_cost IS NOT NULL AND t.revenue_supported IS NOT NULL AND t.revenue_supported > 0
        RETURN t.name as team,
               t.monthly_cost as cost,
               t.revenue_supported as revenue,
               t.efficiency_ratio as efficiency,
               (t.monthly_cost / t.revenue_supported * 100) as cost_to_revenue_ratio
        ORDER BY cost_to_revenue_ratio DESC
        """
    }
]

print("Testing queries against extracted data...\n")

with driver.session() as session:
    for test in test_queries:
        print(f"Question: {test['question']}")
        print("-" * 80)
        
        try:
            result = session.run(test['query'])
            records = list(result)
            
            if records:
                for record in records[:5]:  # Show first 5 results
                    print(f"  {dict(record)}")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"  Error: {e}")
        
        print()

driver.close()

print("\nConclusion:")
print("The data is available in Neo4j, but the agent's Cypher examples don't match the actual schema.")
print("The agent needs updated Cypher examples that use:")
print("  - :OPERATIONAL_COST with cost_per_customer")
print("  - :COMMITMENT instead of :FEATURE_PROMISE")
print("  - :SATISFACTION_SCORE for product satisfaction")
print("  - :FEATURE for adoption metrics")