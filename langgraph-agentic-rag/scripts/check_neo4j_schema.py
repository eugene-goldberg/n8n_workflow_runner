#!/usr/bin/env python3
"""Check Neo4j schema and data from spyro-agentic-rag"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings

def check_schema():
    """Check the current Neo4j schema"""
    
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    print("=== NEO4J SCHEMA STATUS ===\n")
    print(f"Connected to: {settings.neo4j.uri}")
    print(f"Username: {settings.neo4j.username}\n")
    
    with driver.session() as session:
        # Check for LlamaIndex format entities
        print("1. LLAMAINDEX FORMAT ENTITIES (:__Entity__:TYPE):")
        print("-" * 50)
        
        entity_types = [
            'CUSTOMER', 'PRODUCT', 'TEAM', 'PROJECT', 'RISK', 'SUBSCRIPTION', 
            'REVENUE', 'FEATURE', 'ROADMAP_ITEM', 'CUSTOMER_SUCCESS_SCORE', 
            'EVENT', 'COST', 'PROFITABILITY', 'OBJECTIVE', 'SLA', 'OPPORTUNITY',
            'INTEGRATION', 'PERFORMANCE_METRIC', 'BUSINESS_UNIT', 'HEALTH_SCORE',
            'PIPELINE_STAGE', 'DEAL_SIZE', 'PROJECT_MILESTONE', 'USER_STORY',
            'COMPETITOR', 'MARKET_SEGMENT', 'SALES_REP', 'CUSTOMER_SEGMENT',
            'CUSTOMER_EVENT', 'SUPPORT_TICKET', 'INTEGRATION_ISSUE', 
            'EXECUTIVE_SPONSOR', 'PRIORITY', 'EXTERNAL_DEPENDENCY', 'LIFECYCLE_STAGE'
        ]
        
        total_entities = 0
        for entity_type in entity_types:
            result = session.run(f"""
                MATCH (n:__Entity__:{entity_type})
                RETURN count(n) as count
            """)
            count = result.single()['count']
            if count > 0:
                print(f"  {entity_type}: {count} entities")
                total_entities += count
        
        print(f"\nTotal entities: {total_entities}")
        
        # Check relationships
        print("\n2. RELATIONSHIPS:")
        print("-" * 50)
        
        result = session.run("""
            MATCH ()-[r]->()
            WITH type(r) as rel_type, count(*) as count
            ORDER BY count DESC
            RETURN rel_type, count
            LIMIT 20
        """)
        
        for record in result:
            print(f"  {record['rel_type']}: {record['count']} relationships")
        
        # Check indexes
        print("\n3. INDEXES:")
        print("-" * 50)
        
        result = session.run("SHOW INDEXES")
        for record in result:
            print(f"  {record['name']} on {record['labelsOrTypes']} ({record['properties']})")
        
        # Sample data
        print("\n4. SAMPLE DATA:")
        print("-" * 50)
        
        # Sample customers
        print("\nSample Customers:")
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)
            RETURN c.name as name, c.arr as arr, c.success_score as score
            LIMIT 5
        """)
        for record in result:
            print(f"  - {record['name']}: ARR=${record['arr']}, Score={record['score']}")
        
        # Sample products
        print("\nSample Products:")
        result = session.run("""
            MATCH (p:__Entity__:PRODUCT)
            RETURN p.name as name, p.adoption_rate as adoption
            LIMIT 5
        """)
        for record in result:
            print(f"  - {record['name']}: Adoption={record['adoption']}%")
    
    driver.close()
    print("\n=== SCHEMA CHECK COMPLETE ===")

if __name__ == "__main__":
    check_schema()