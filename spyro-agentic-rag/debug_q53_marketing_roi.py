#!/usr/bin/env python3
"""Debug Q53: Marketing Channels ROI Query Failure"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from neo4j import GraphDatabase

def test_cypher_queries(driver):
    """Test different Cypher queries to find what works"""
    
    queries = [
        # 1. Agent's first attempt - looking for relationships
        {
            "name": "Agent Query 1 - Relationships",
            "cypher": """
                MATCH (m:__Entity__)-[:GENERATES_REVENUE]->(r:REVENUE), 
                      (m)-[:INCURS_COST]->(c:COST)
                WHERE 'MARKETING_CHANNEL' IN labels(m)
                RETURN m.name AS marketing_channel, count(*) as matches
            """
        },
        
        # 2. Simple direct query
        {
            "name": "Direct Property Query",
            "cypher": """
                MATCH (m:MARKETING_CHANNEL)
                WHERE m.roi IS NOT NULL
                RETURN m.name AS channel, m.roi AS roi
                ORDER BY m.roi DESC
                LIMIT 5
            """
        },
        
        # 3. With __Entity__ label
        {
            "name": "With Entity Label",
            "cypher": """
                MATCH (m)
                WHERE '__Entity__' IN labels(m) AND 'MARKETING_CHANNEL' IN labels(m)
                AND m.roi IS NOT NULL
                RETURN m.name AS channel, m.roi AS roi
                ORDER BY m.roi DESC
                LIMIT 5
            """
        },
        
        # 4. All properties approach
        {
            "name": "All Properties",
            "cypher": """
                MATCH (m:MARKETING_CHANNEL)
                RETURN m.name AS channel, 
                       m.roi AS roi,
                       m.total_cost AS cost,
                       m.attributed_revenue AS revenue
                ORDER BY m.roi DESC
            """
        },
        
        # 5. Check for any relationships
        {
            "name": "Check Relationships",
            "cypher": """
                MATCH (m:MARKETING_CHANNEL)
                OPTIONAL MATCH (m)-[r]-()
                RETURN m.name, type(r) as rel_type, count(r) as rel_count
                LIMIT 5
            """
        }
    ]
    
    with driver.session() as session:
        for query_info in queries:
            print(f"\n{'='*60}")
            print(f"Testing: {query_info['name']}")
            print(f"Cypher: {query_info['cypher'].strip()}")
            print("-"*60)
            
            try:
                result = session.run(query_info['cypher'])
                records = list(result)
                
                if records:
                    print(f"✅ SUCCESS - {len(records)} results")
                    for i, record in enumerate(records[:3]):
                        print(f"   Row {i+1}: {dict(record)}")
                    if len(records) > 3:
                        print(f"   ... and {len(records) - 3} more")
                else:
                    print("❌ NO RESULTS")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")

def analyze_problem(driver):
    """Analyze why the agent's queries fail"""
    
    print("\n" + "="*60)
    print("PROBLEM ANALYSIS")
    print("="*60)
    
    with driver.session() as session:
        # Check if MARKETING_CHANNEL nodes have any relationships
        result = session.run("""
            MATCH (m:MARKETING_CHANNEL)
            OPTIONAL MATCH (m)-[r]-()
            RETURN count(DISTINCT m) as node_count, count(r) as rel_count
        """)
        record = result.single()
        print(f"\n1. Relationship Analysis:")
        print(f"   - MARKETING_CHANNEL nodes: {record['node_count']}")
        print(f"   - Relationships: {record['rel_count']}")
        
        # Check label combinations
        result = session.run("""
            MATCH (m:MARKETING_CHANNEL)
            RETURN DISTINCT labels(m) as label_combo, count(*) as count
        """)
        print(f"\n2. Label Combinations:")
        for record in result:
            print(f"   - {record['label_combo']}: {record['count']} nodes")
        
        # Show actual vs expected structure
        print("\n3. Agent's Expectation vs Reality:")
        print("   Agent expects:")
        print("     - MARKETING_CHANNEL -[:GENERATES_REVENUE]-> REVENUE")
        print("     - MARKETING_CHANNEL -[:INCURS_COST]-> COST")
        print("   Reality:")
        print("     - MARKETING_CHANNEL nodes have roi, total_cost, attributed_revenue as properties")
        print("     - No relationships to REVENUE or COST nodes")

def suggest_solution():
    """Suggest how to fix the issue"""
    
    print("\n" + "="*60)
    print("SOLUTION")
    print("="*60)
    
    print("\n1. Add this example to cypher_examples_enhanced_v3.py:")
    print("""
    {
        "question": "Which marketing channels have the highest ROI?",
        "cypher": \"\"\"// Marketing channels store ROI as a property
MATCH (m) 
WHERE '__Entity__' IN labels(m) AND 'MARKETING_CHANNEL' IN labels(m)
AND m.roi IS NOT NULL
RETURN m.name AS channel, 
       m.roi AS roi_percentage,
       m.total_cost AS cost,
       m.attributed_revenue AS revenue
ORDER BY m.roi DESC\"\"\"
    }
    """)
    
    print("\n2. The agent needs to learn that:")
    print("   - Some entities store calculated metrics as properties")
    print("   - Not all financial data requires relationship traversal")
    print("   - MARKETING_CHANNEL has self-contained ROI data")

def main():
    config = Config.from_env()
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_username, config.neo4j_password)
    )
    
    try:
        print("DEBUGGING Q53: Marketing Channels ROI Query\n")
        
        test_cypher_queries(driver)
        analyze_problem(driver)
        suggest_solution()
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()