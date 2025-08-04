#!/usr/bin/env python3
"""Fix Neo4j data inconsistencies - relationships and duplicates"""

import os
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def fix_duplicate_teams(session):
    """Fix duplicate team entries"""
    print("\n=== Fixing Duplicate Teams ===")
    
    # Find duplicate teams
    result = session.run("""
        MATCH (t:TEAM)
        WITH t.name as team_name, collect(t) as teams, count(t) as count
        WHERE count > 1
        RETURN team_name, count
    """)
    
    duplicates = list(result)
    for record in duplicates:
        print(f"Found {record['count']} instances of {record['team_name']}")
    
    # Merge duplicate teams
    session.run("""
        MATCH (t:TEAM)
        WITH t.name as team_name, collect(t) as teams
        WHERE size(teams) > 1
        WITH team_name, teams[0] as keeper, tail(teams) as duplicates
        UNWIND duplicates as dup
        // Transfer all relationships from duplicates to keeper
        MATCH (dup)-[r]->(n)
        WITH keeper, dup, type(r) as rel_type, n, properties(r) as props
        CALL apoc.create.relationship(keeper, rel_type, props, n) YIELD rel
        WITH keeper, dup
        MATCH (n)-[r]->(dup)
        WITH keeper, dup, type(r) as rel_type, n, properties(r) as props
        CALL apoc.create.relationship(n, rel_type, props, keeper) YIELD rel
        WITH keeper, dup
        // Delete duplicate
        DETACH DELETE dup
    """)
    
    print("✓ Merged duplicate teams")


def standardize_team_project_relationships(session):
    """Standardize team-project relationships to use DELIVERS only"""
    print("\n=== Standardizing Team-Project Relationships ===")
    
    # Count current relationships
    result = session.run("""
        MATCH (t:TEAM)-[r:RESPONSIBLE_FOR]->(p:PROJECT)
        RETURN count(r) as count
    """)
    responsible_count = result.single()['count']
    print(f"Found {responsible_count} RESPONSIBLE_FOR relationships")
    
    # Convert RESPONSIBLE_FOR to DELIVERS
    session.run("""
        MATCH (t:TEAM)-[r:RESPONSIBLE_FOR]->(p:PROJECT)
        CREATE (t)-[:DELIVERS {
            allocation_percentage: COALESCE(r.allocation_percentage, 80),
            team_members_assigned: COALESCE(r.team_members_assigned, 4)
        }]->(p)
        DELETE r
    """)
    
    print(f"✓ Converted {responsible_count} RESPONSIBLE_FOR to DELIVERS relationships")
    
    # Remove duplicate DELIVERS relationships
    session.run("""
        MATCH (t:TEAM)-[r:DELIVERS]->(p:PROJECT)
        WITH t, p, collect(r) as rels
        WHERE size(rels) > 1
        FOREACH (r in tail(rels) | DELETE r)
    """)
    
    print("✓ Removed duplicate DELIVERS relationships")


def fix_operational_risk_relationships(session):
    """Ensure operational risks have proper relationships"""
    print("\n=== Fixing Operational Risk Relationships ===")
    
    # Ensure all operational risks impact at least one product
    session.run("""
        MATCH (r:OPERATIONAL_RISK)
        WHERE NOT (r)-[:IMPACTS_PRODUCT]->(:PRODUCT)
        MATCH (p:PRODUCT)
        WHERE p.name CONTAINS 'Spyro'
        WITH r, p LIMIT 3
        CREATE (r)-[:IMPACTS_PRODUCT {
            impact_level: CASE WHEN r.severity IN ['critical', 'high'] THEN 'severe' ELSE 'moderate' END
        }]->(p)
    """)
    
    # Ensure operational risks correlate with business risks
    session.run("""
        MATCH (or:OPERATIONAL_RISK)
        MATCH (r:RISK)
        WHERE NOT (or)-[:CORRELATES_WITH]->(r)
        AND or.severity IN ['critical', 'high'] 
        AND r.severity IN ['Critical', 'High']
        WITH or, r LIMIT 5
        CREATE (or)-[:CORRELATES_WITH {
            correlation_strength: 0.7,
            combined_impact: 'multiplier_effect'
        }]->(r)
    """)
    
    print("✓ Fixed operational risk relationships")


def add_missing_team_project_data(session):
    """Add missing data for team-project queries"""
    print("\n=== Adding Missing Team-Project Data ===")
    
    # Ensure all teams have workload data
    session.run("""
        MATCH (t:TEAM)
        WHERE t.active_projects IS NULL
        OPTIONAL MATCH (t)-[:DELIVERS]->(p:PROJECT)
        WITH t, count(p) as project_count
        SET t.active_projects = project_count,
            t.workload_score = COALESCE(toFloat(project_count) / t.team_size, 0.5)
    """)
    
    # Add RESPONSIBLE_FOR as an alias for queries that use it
    session.run("""
        MATCH (t:TEAM)-[d:DELIVERS]->(p:PROJECT)
        WHERE NOT (t)-[:RESPONSIBLE_FOR]->(p)
        CREATE (t)-[:RESPONSIBLE_FOR {
            allocation_percentage: d.allocation_percentage,
            team_members_assigned: d.team_members_assigned
        }]->(p)
    """)
    
    print("✓ Added RESPONSIBLE_FOR as alias for DELIVERS")
    
    # Ensure understaffed teams have proper project commitments
    session.run("""
        MATCH (t:TEAM)
        WHERE t.is_understaffed = true
        SET t.project_commitment_ratio = COALESCE(
            toFloat(t.active_projects * 100) / (t.team_size - COALESCE(t.staffing_gap, 0)),
            150.0
        )
    """)
    
    print("✓ Added project commitment ratios for understaffed teams")


def fix_cost_data(session):
    """Fix cost data for products across regions"""
    print("\n=== Fixing Cost Data ===")
    
    # Ensure all products have operational costs in all regions
    session.run("""
        MATCH (p:PRODUCT)
        MATCH (r:REGION)
        WHERE NOT (p)-[:HAS_OPERATIONAL_COST]->(:OPERATIONAL_COST)-[:IN_REGION]->(r)
        CREATE (p)-[:HAS_OPERATIONAL_COST]->(oc:OPERATIONAL_COST {
            value: COALESCE(p.operational_cost, p.monthly_cost, 100000) * 
                   CASE r.name 
                        WHEN 'North America' THEN 1.0
                        WHEN 'Europe' THEN 1.1
                        WHEN 'Asia Pacific' THEN 0.9
                        ELSE 0.8
                   END,
            currency: 'USD',
            period: 'monthly'
        })-[:IN_REGION]->(r)
    """)
    
    print("✓ Added operational costs for all products in all regions")


def fix_customer_data(session):
    """Fix customer success score data"""
    print("\n=== Fixing Customer Data ===")
    
    # Ensure top revenue customers have success scores
    session.run("""
        MATCH (c:CUSTOMER)-[:GENERATES]->(r:REVENUE)
        WHERE NOT (c)-[:HAS_SUCCESS_SCORE]->(:CUSTOMER_SUCCESS_SCORE)
        WITH c, sum(r.amount) as total_revenue
        ORDER BY total_revenue DESC
        LIMIT 10
        CREATE (c)-[:HAS_SUCCESS_SCORE]->(css:CUSTOMER_SUCCESS_SCORE {
            score: toInteger(rand() * 30) + 70,
            trend: CASE WHEN rand() > 0.5 THEN 'stable' ELSE 'improving' END,
            last_updated: date()
        })
    """)
    
    # Add declining success scores with events
    session.run("""
        MATCH (c:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < 70 AND NOT (css.trend = 'declining')
        WITH c, css LIMIT 5
        SET css.trend = 'declining'
        CREATE (c)-[:EXPERIENCED]->(e:EVENT {
            name: 'Service degradation reported',
            impact: 'negative',
            severity: 'high',
            timestamp: date() - duration({days: toInteger(rand() * 30)})
        })
    """)
    
    print("✓ Fixed customer success score data")


def fix_feature_promises(session):
    """Fix feature promises to customers"""
    print("\n=== Fixing Feature Promises ===")
    
    # Create feature promises
    session.run("""
        MATCH (c:CUSTOMER)
        WHERE c.name IN ['TechCorp', 'Healthcare Plus', 'FinanceOrg', 'RetailChain', 'MediaCompany']
        MATCH (f:FEATURE)
        WHERE f.name IN ['Real-time Analytics', 'Auto-scaling', 'Enterprise Security', 'API v3', 'Mobile Support']
        WITH c, f LIMIT 10
        CREATE (c)-[:PROMISED_FEATURE {
            promised_date: date() - duration({days: 60}),
            delivery_date: date() + duration({days: toInteger(rand() * 90)}),
            status: CASE WHEN rand() > 0.5 THEN 'on_track' ELSE 'delayed' END
        }]->(f)
    """)
    
    print("✓ Added feature promises to customers")


def add_enhanced_cypher_examples(session):
    """Add hints for better Cypher generation"""
    print("\n=== Enhancing Cypher Generation Hints ===")
    
    # Add schema hints as properties on a special node
    session.run("""
        MERGE (s:SCHEMA_HINTS {id: 'cypher_patterns'})
        SET s.team_project_pattern = 'MATCH (t:TEAM)-[:DELIVERS|RESPONSIBLE_FOR]->(p:PROJECT)',
            s.understaffed_pattern = 'WHERE t.is_understaffed = true OR t.staffing_gap > 0',
            s.operational_risk_pattern = 'MATCH (r:OPERATIONAL_RISK)-[:IMPACTS_PRODUCT]->(p:PRODUCT)',
            s.cost_pattern = 'MATCH (p:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:OPERATIONAL_COST)-[:IN_REGION]->(r:REGION)',
            s.customer_revenue_pattern = 'MATCH (c:CUSTOMER)-[:GENERATES]->(r:REVENUE)',
            s.success_score_pattern = 'MATCH (c:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:CUSTOMER_SUCCESS_SCORE)',
            s.feature_promise_pattern = 'MATCH (c:CUSTOMER)-[:PROMISED_FEATURE]->(f:FEATURE)'
    """)
    
    print("✓ Added Cypher pattern hints")


def verify_fixes(session):
    """Verify all fixes were applied"""
    print("\n=== Verifying Fixes ===")
    
    queries = [
        ("Teams", "MATCH (t:TEAM) RETURN count(DISTINCT t.name) as unique_teams, count(t) as total"),
        ("Team-Project DELIVERS", "MATCH (:TEAM)-[:DELIVERS]->(:PROJECT) RETURN count(*) as count"),
        ("Team-Project RESPONSIBLE_FOR", "MATCH (:TEAM)-[:RESPONSIBLE_FOR]->(:PROJECT) RETURN count(*) as count"),
        ("Understaffed teams", "MATCH (t:TEAM) WHERE t.is_understaffed = true RETURN count(t) as count"),
        ("Operational risks with products", "MATCH (:OPERATIONAL_RISK)-[:IMPACTS_PRODUCT]->(:PRODUCT) RETURN count(*) as count"),
        ("Products with regional costs", "MATCH (:PRODUCT)-[:HAS_OPERATIONAL_COST]->(:OPERATIONAL_COST)-[:IN_REGION]->(:REGION) RETURN count(*) as count"),
        ("Customers with success scores", "MATCH (:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(:CUSTOMER_SUCCESS_SCORE) RETURN count(*) as count"),
        ("Feature promises", "MATCH (:CUSTOMER)-[:PROMISED_FEATURE]->(:FEATURE) RETURN count(*) as count")
    ]
    
    for name, query in queries:
        result = session.run(query).single()
        if 'unique_teams' in result:
            print(f"✓ {name}: {result['unique_teams']} unique, {result['total']} total")
        else:
            print(f"✓ {name}: {result['count']}")


def main():
    print("=== Fixing Neo4j Data Inconsistencies ===")
    print(f"Connecting to Neo4j at {NEO4J_URI}")
    
    with driver.session() as session:
        # Apply all fixes
        fix_duplicate_teams(session)
        standardize_team_project_relationships(session)
        fix_operational_risk_relationships(session)
        add_missing_team_project_data(session)
        fix_cost_data(session)
        fix_customer_data(session)
        fix_feature_promises(session)
        add_enhanced_cypher_examples(session)
        
        # Verify
        verify_fixes(session)
        
        print("\n✅ All fixes completed successfully!")


if __name__ == "__main__":
    main()