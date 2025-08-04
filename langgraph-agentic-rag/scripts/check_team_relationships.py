#!/usr/bin/env python3
"""Check team relationships in Neo4j"""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

with driver.session() as session:
    # Check team-project relationships
    result = session.run("""
        MATCH (t:TEAM)-[r]->(p:PROJECT)
        RETURN type(r) as rel_type, count(*) as count
    """)
    print("Team-Project relationships:")
    for record in result:
        print(f"  {record['rel_type']}: {record['count']}")
    
    # Check understaffed teams
    result = session.run("""
        MATCH (t:TEAM)
        WHERE t.is_understaffed = true
        RETURN t.name as team, t.staffing_gap as gap, t.active_projects as projects
    """)
    print("\nUnderstaffed teams:")
    for record in result:
        print(f"  {record['team']}: gap={record['gap']}, projects={record['projects']}")
    
    # Check operational risks
    result = session.run("""
        MATCH (r:OPERATIONAL_RISK)
        RETURN count(r) as count
    """)
    print(f"\nOperational risks: {result.single()['count']}")
    
    # Check projects
    result = session.run("""
        MATCH (p:PROJECT)
        RETURN count(p) as total,
               sum(CASE WHEN p.is_blocked THEN 1 ELSE 0 END) as blocked,
               sum(CASE WHEN p.status = 'at_risk' THEN 1 ELSE 0 END) as at_risk
    """)
    record = result.single()
    print(f"\nProjects: {record['total']} total, {record['blocked']} blocked, {record['at_risk']} at risk")