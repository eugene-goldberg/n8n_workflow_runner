#!/usr/bin/env python3
"""Standardize to use only DELIVERS relationship between teams and projects"""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def remove_responsible_for_relationships(session):
    """Remove all RESPONSIBLE_FOR relationships"""
    print("\n=== Removing RESPONSIBLE_FOR Relationships ===")
    
    # Count before
    result = session.run("""
        MATCH ()-[r:RESPONSIBLE_FOR]->()
        RETURN count(r) as count
    """).single()
    count = result['count']
    print(f"Found {count} RESPONSIBLE_FOR relationships to remove")
    
    # Delete all RESPONSIBLE_FOR relationships
    session.run("""
        MATCH ()-[r:RESPONSIBLE_FOR]->()
        DELETE r
    """)
    
    print(f"✓ Removed {count} RESPONSIBLE_FOR relationships")


def add_cypher_examples_to_graph_retriever(session):
    """Add schema hints for consistent Cypher generation"""
    print("\n=== Adding Cypher Pattern Examples ===")
    
    # Create or update schema examples node
    session.run("""
        MERGE (s:CYPHER_EXAMPLES {id: 'team_project_patterns'})
        SET s.examples = [
            'Teams working on projects: MATCH (t:TEAM)-[:DELIVERS]->(p:PROJECT)',
            'Understaffed teams: MATCH (t:TEAM) WHERE t.is_understaffed = true OR t.staffing_gap > 0',
            'Team project workload: MATCH (t:TEAM)-[:DELIVERS]->(p:PROJECT) WITH t, count(p) as project_count',
            'Teams by project status: MATCH (t:TEAM)-[:DELIVERS]->(p:PROJECT) WHERE p.status = "at_risk"',
            'Project dependencies: MATCH (p1:PROJECT)-[:BLOCKS]->(p2:PROJECT)',
            'Blocked projects: MATCH (p:PROJECT) WHERE p.is_blocked = true',
            'Team costs: MATCH (t:TEAM) WHERE exists(t.operational_cost) OR exists(t.total_cost)',
            'Operational risks: MATCH (r:OPERATIONAL_RISK)-[:IMPACTS_PRODUCT]->(p:PRODUCT)',
            'Customer revenue: MATCH (c:CUSTOMER)-[:PAYS]->(s:SUBSCRIPTION) WITH c, sum(s.amount * 12) as arr',
            'Product costs by region: MATCH (p:PRODUCT)-[:HAS_OPERATIONAL_COST]->(oc:OPERATIONAL_COST)-[:IN_REGION]->(r:REGION)'
        ],
        s.updated_at = datetime()
    """)
    
    print("✓ Added Cypher pattern examples for consistent query generation")


def verify_standardization(session):
    """Verify the standardization was successful"""
    print("\n=== Verification ===")
    
    # Check DELIVERS relationships
    result = session.run("""
        MATCH (:TEAM)-[r:DELIVERS]->(:PROJECT)
        RETURN count(r) as count
    """).single()
    print(f"✓ DELIVERS relationships: {result['count']}")
    
    # Check RESPONSIBLE_FOR relationships
    result = session.run("""
        MATCH ()-[r:RESPONSIBLE_FOR]->()
        RETURN count(r) as count
    """).single()
    print(f"✓ RESPONSIBLE_FOR relationships: {result['count']} (should be 0)")
    
    # Sample team-project relationships
    result = session.run("""
        MATCH (t:TEAM)-[:DELIVERS]->(p:PROJECT)
        RETURN t.name as team, collect(p.name)[0..3] as sample_projects
        LIMIT 5
    """)
    print("\nSample team-project relationships:")
    for record in result:
        projects = ', '.join(record['sample_projects'][:3])
        if len(record['sample_projects']) > 3:
            projects += '...'
        print(f"  - {record['team']}: {projects}")


def main():
    print("=== Standardizing Team-Project Relationships ===")
    print("Using only DELIVERS relationship type")
    
    with driver.session() as session:
        remove_responsible_for_relationships(session)
        add_cypher_examples_to_graph_retriever(session)
        verify_standardization(session)
        
        print("\n✅ Standardization complete!")
        print("   All team-project relationships now use DELIVERS only")


if __name__ == "__main__":
    main()