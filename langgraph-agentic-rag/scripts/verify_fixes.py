#!/usr/bin/env python3
"""Verify Neo4j fixes were applied"""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

with driver.session() as session:
    print("=== Verification Results ===\n")
    
    # Check teams
    result = session.run("""
        MATCH (t:TEAM)
        RETURN count(DISTINCT t.name) as unique_count, count(t) as total_count
    """).single()
    print(f"Teams: {result['unique_count']} unique teams, {result['total_count']} total nodes")
    
    # Check relationships
    result = session.run("""
        MATCH (t:TEAM)-[:DELIVERS]->(p:PROJECT)
        RETURN count(*) as delivers_count
    """).single()
    print(f"DELIVERS relationships: {result['delivers_count']}")
    
    result = session.run("""
        MATCH (t:TEAM)-[:RESPONSIBLE_FOR]->(p:PROJECT)
        RETURN count(*) as responsible_count
    """).single()
    print(f"RESPONSIBLE_FOR relationships: {result['responsible_count']}")
    
    # Check understaffed teams
    result = session.run("""
        MATCH (t:TEAM)
        WHERE t.is_understaffed = true
        RETURN t.name as name, t.staffing_gap as gap, t.active_projects as projects
        ORDER BY t.name
    """)
    print("\nUnderstaffed teams:")
    for record in result:
        print(f"  - {record['name']}: gap={record['gap']}, projects={record['projects']}")
    
    # Check operational costs
    result = session.run("""
        MATCH (p:PRODUCT)-[:HAS_OPERATIONAL_COST]->(oc:OPERATIONAL_COST)-[:IN_REGION]->(r:REGION)
        RETURN p.name as product, count(DISTINCT r.name) as regions
        ORDER BY product
        LIMIT 5
    """)
    print("\nProduct operational costs by region (sample):")
    for record in result:
        print(f"  - {record['product']}: {record['regions']} regions")
    
    # Check feature promises
    result = session.run("""
        MATCH (c:CUSTOMER)-[:PROMISED_FEATURE]->(f:FEATURE)
        RETURN count(*) as promise_count
    """).single()
    print(f"\nFeature promises: {result['promise_count']}")
    
    print("\n✅ Verification complete!")