#!/usr/bin/env python3
"""Verify the Neo4j data fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings

def verify_data_fixes():
    """Check that key relationships and data now exist"""
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    with driver.session() as session:
        print("=== VERIFYING NEO4J DATA FIXES ===\n")
        
        # 1. Check customer success scores
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)
            OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
            RETURN 
                count(DISTINCT c) as total_customers,
                count(DISTINCT css) as customers_with_scores,
                count(CASE WHEN css.score < 60 THEN 1 END) as low_score_customers
        """)
        record = result.single()
        print(f"1. Customer Success Scores:")
        print(f"   Total customers: {record['total_customers']}")
        print(f"   Customers with scores: {record['customers_with_scores']}")
        print(f"   Customers with scores < 60: {record['low_score_customers']}")
        
        # 2. Check customer events
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:EXPERIENCED]->(e:__Entity__:EVENT)
            WHERE e.impact = 'negative'
            RETURN count(DISTINCT c) as customers_with_negative_events,
                   count(e) as total_negative_events
        """)
        record = result.single()
        print(f"\n2. Customer Events:")
        print(f"   Customers with negative events: {record['customers_with_negative_events']}")
        print(f"   Total negative events: {record['total_negative_events']}")
        
        # 3. Check commitments
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
            RETURN count(DISTINCT c) as customers_with_commitments,
                   count(com) as total_commitments
        """)
        record = result.single()
        print(f"\n3. Customer Commitments:")
        print(f"   Customers with commitments: {record['customers_with_commitments']}")
        print(f"   Total commitments: {record['total_commitments']}")
        
        # 4. Check product success scores
        result = session.run("""
            MATCH (p:__Entity__:PRODUCT)
            OPTIONAL MATCH (p)-[:HAS_SUCCESS_SCORE]->(pss)
            RETURN count(DISTINCT p) as total_products,
                   count(DISTINCT pss) as products_with_scores
        """)
        record = result.single()
        print(f"\n4. Product Success Scores:")
        print(f"   Total products: {record['total_products']}")
        print(f"   Products with success scores: {record['products_with_scores']}")
        
        # 5. Check team-product relationships
        result = session.run("""
            MATCH (t:__Entity__:TEAM)-[:SUPPORTS]->(p:__Entity__:PRODUCT)
            RETURN count(DISTINCT t) as teams_supporting_products,
                   count(DISTINCT p) as products_with_support
        """)
        record = result.single()
        print(f"\n5. Team-Product Relationships:")
        print(f"   Teams supporting products: {record['teams_supporting_products']}")
        print(f"   Products with team support: {record['products_with_support']}")
        
        # 6. Check risk mitigation
        result = session.run("""
            MATCH (r:__Entity__:RISK)
            WHERE r.severity IN ['high', 'critical']
            OPTIONAL MATCH (r)-[:MITIGATED_BY]->(m)
            RETURN count(DISTINCT r) as high_severity_risks,
                   count(DISTINCT m) as mitigations
        """)
        record = result.single()
        print(f"\n6. Risk Mitigation:")
        print(f"   High severity risks: {record['high_severity_risks']}")
        print(f"   Risks with mitigation: {record['mitigations']}")
        
        # 7. Check roadmap items
        result = session.run("""
            MATCH (ri:__Entity__:ROADMAP_ITEM)
            RETURN count(ri) as total_roadmap_items,
                   count(CASE WHEN ri.status = 'behind_schedule' THEN 1 END) as behind_schedule
        """)
        record = result.single()
        print(f"\n7. Roadmap Items:")
        print(f"   Total roadmap items: {record['total_roadmap_items']}")
        print(f"   Behind schedule: {record['behind_schedule']}")
        
        # 8. Check customer concerns
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:HAS_CONCERN]->(con:__Entity__:CONCERN)
            RETURN count(DISTINCT c) as customers_with_concerns,
                   count(con) as total_concerns
        """)
        record = result.single()
        print(f"\n8. Customer Concerns:")
        print(f"   Customers with concerns: {record['customers_with_concerns']}")
        print(f"   Total concerns: {record['total_concerns']}")
        
        print("\n✅ Data verification complete!")
    
    driver.close()

if __name__ == "__main__":
    verify_data_fixes()