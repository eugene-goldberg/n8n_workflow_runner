#!/usr/bin/env python3
"""Test queries directly against Neo4j"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def test_query(name, query):
    """Test a single query"""
    print(f"\n{'-' * 60}")
    print(f"Testing: {name}")
    print(f"Query: {query[:100]}...")
    
    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            print(f"Records returned: {len(records)}")
            if records:
                for i, record in enumerate(records[:3]):
                    print(f"Record {i}: {dict(record)}")
            else:
                print("No records found")
                
    except Exception as e:
        print(f"ERROR: {str(e)}")

def main():
    print("Testing Direct Cypher Queries")
    print("=" * 80)
    
    # Test queries
    queries = [
        ("Commitments at high risk", """
        MATCH (cm) 
        WHERE ('Commitment' IN labels(cm) OR ('__Entity__' IN labels(cm) AND 'COMMITMENT' IN labels(cm)))
        AND (cm.risk_level = 'High' OR cm.status IN ['Not Met', 'At Risk'])
        RETURN cm.type as commitment_type,
               cm.description as description,
               cm.target as target,
               cm.current_performance as current,
               cm.status as status,
               cm.risk_level as risk_level
        ORDER BY 
            CASE cm.risk_level 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                ELSE 3 
            END,
            cm.status
        """),
        
        ("Product satisfaction scores", """
        MATCH (p) 
        WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
        AND (p.satisfaction_score IS NOT NULL OR p.nps_score IS NOT NULL)
        RETURN p.name as product,
               coalesce(p.satisfaction_score, 'N/A') as satisfaction_score,
               coalesce(p.nps_score, 'N/A') as nps_score
        ORDER BY p.satisfaction_score DESC
        """),
        
        ("Teams with high costs", """
        MATCH (t) 
        WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
        AND t.monthly_cost > 0 AND t.revenue_supported > 0
        WITH t.name as team,
             t.monthly_cost as team_cost,
             t.revenue_supported as supported_revenue,
             t.efficiency_ratio as efficiency_ratio
        ORDER BY efficiency_ratio ASC
        LIMIT 5
        RETURN team, team_cost, supported_revenue, 
               round(team_cost / supported_revenue * 100, 2) as cost_to_revenue_ratio
        """),
        
        ("Check teams data", """
        MATCH (t)
        WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
        RETURN t.name as name, 
               t.monthly_cost as monthly_cost,
               t.revenue_supported as revenue_supported,
               t.efficiency_ratio as efficiency_ratio
        LIMIT 10
        """),
        
        ("Check commitments data", """
        MATCH (cm)
        WHERE ('Commitment' IN labels(cm) OR ('__Entity__' IN labels(cm) AND 'COMMITMENT' IN labels(cm)))
        RETURN cm
        LIMIT 10
        """),
        
        ("Check products data", """
        MATCH (p)
        WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
        RETURN p.name as name,
               p.satisfaction_score as satisfaction_score,
               p.nps_score as nps_score
        LIMIT 10
        """)
    ]
    
    for name, query in queries:
        test_query(name, query)
    
    print(f"\n{'=' * 80}")
    print("Test completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()