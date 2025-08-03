#!/usr/bin/env python3
"""
Migrate property-centric entities to relationship-centric model
Phase 1: MARKETING_CHANNEL, PROJECTION, REVENUE
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from neo4j import GraphDatabase
from datetime import datetime

def create_new_node_types(session):
    """Create new node types for the relationship model"""
    
    print("\n1. Creating new node types...")
    
    queries = [
        # Performance metrics
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (p:PERFORMANCE_METRIC) REQUIRE p.id IS UNIQUE
        """,
        
        # Quarter periods
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (q:QUARTER) REQUIRE (q.name, q.year) IS UNIQUE
        """,
        
        # Revenue types
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (rt:REVENUE_TYPE) REQUIRE rt.name IS UNIQUE
        """,
        
        # Metric nodes
        """
        CREATE CONSTRAINT IF NOT EXISTS FOR (m:METRIC) REQUIRE m.id IS UNIQUE
        """
    ]
    
    for query in queries:
        try:
            session.run(query)
            print(f"  ✓ Created constraint")
        except Exception as e:
            print(f"  ⚠️  Constraint may already exist: {e}")

def migrate_marketing_channels(session):
    """Migrate MARKETING_CHANNEL from properties to relationships"""
    
    print("\n2. Migrating MARKETING_CHANNEL entities...")
    
    # First, check current state
    result = session.run("""
        MATCH (m:MARKETING_CHANNEL)
        RETURN count(m) as count
    """)
    count = result.single()['count']
    print(f"  Found {count} MARKETING_CHANNEL nodes to migrate")
    
    # Migrate each marketing channel
    migration_query = """
    MATCH (m:MARKETING_CHANNEL)
    WHERE m.roi IS NOT NULL AND m.total_cost IS NOT NULL
    
    // Create COST relationship
    MERGE (c:__Entity__:COST {
        amount: m.total_cost,
        type: 'marketing',
        period: coalesce(m.period, 'Unknown')
    })
    MERGE (m)-[:HAS_COST {period: coalesce(m.period, 'Unknown')}]->(c)
    
    // Create REVENUE relationship if attributed_revenue exists
    FOREACH (_ IN CASE WHEN m.attributed_revenue IS NOT NULL THEN [1] ELSE [] END |
        MERGE (r:__Entity__:REVENUE {
            amount: m.attributed_revenue,
            type: 'marketing_attributed',
            period: coalesce(m.period, 'Unknown')
        })
        MERGE (m)-[:GENERATES {period: coalesce(m.period, 'Unknown')}]->(r)
    )
    
    // Create PERFORMANCE_METRIC for ROI
    MERGE (p:__Entity__:PERFORMANCE_METRIC {
        type: 'ROI',
        value: m.roi,
        unit: 'percentage',
        entity_type: 'MARKETING_CHANNEL',
        entity_name: m.name
    })
    MERGE (m)-[:ACHIEVES]->(p)
    
    RETURN count(m) as migrated
    """
    
    result = session.run(migration_query)
    migrated = result.single()['migrated']
    print(f"  ✓ Migrated {migrated} MARKETING_CHANNEL nodes")
    
    # Don't remove properties yet - keep for validation
    print("  ℹ️  Original properties retained for validation")

def migrate_projections(session):
    """Migrate PROJECTION from properties to relationships"""
    
    print("\n3. Migrating PROJECTION entities...")
    
    # Check current state
    result = session.run("""
        MATCH (p:PROJECTION)
        RETURN count(p) as count
    """)
    count = result.single()['count']
    print(f"  Found {count} PROJECTION nodes to migrate")
    
    # Migrate projections
    migration_query = """
    MATCH (proj:PROJECTION)
    WHERE proj.quarter IS NOT NULL AND proj.projected_revenue IS NOT NULL
    
    // Parse quarter (e.g., "Q1 2025")
    WITH proj,
         substring(proj.quarter, 0, 2) as quarter_name,
         toInteger(substring(proj.quarter, 3)) as year
    
    // Create QUARTER node
    MERGE (q:__Entity__:QUARTER {
        name: quarter_name,
        year: year,
        full_name: proj.quarter
    })
    MERGE (proj)-[:FOR_PERIOD]->(q)
    
    // Create METRIC node for projected revenue
    MERGE (m:__Entity__:METRIC {
        type: 'projected_revenue',
        value: proj.projected_revenue,
        confidence: coalesce(proj.confidence, 1.0),
        unit: 'USD',
        entity_type: 'PROJECTION',
        entity_name: proj.name
    })
    MERGE (proj)-[:PROJECTS]->(m)
    
    RETURN count(proj) as migrated
    """
    
    result = session.run(migration_query)
    migrated = result.single()['migrated']
    print(f"  ✓ Migrated {migrated} PROJECTION nodes")

def migrate_revenue_types(session):
    """Migrate REVENUE source property to relationships"""
    
    print("\n4. Migrating REVENUE source types...")
    
    # Check current state
    result = session.run("""
        MATCH (r:REVENUE)
        WHERE r.source IS NOT NULL
        RETURN r.source as source, count(r) as count
        ORDER BY count DESC
    """)
    
    print("  Current revenue types:")
    for record in result:
        print(f"    - {record['source']}: {record['count']} nodes")
    
    # Create REVENUE_TYPE nodes
    session.run("""
        UNWIND ['recurring', 'one-time'] as type_name
        MERGE (rt:__Entity__:REVENUE_TYPE {name: type_name})
    """)
    print("  ✓ Created REVENUE_TYPE nodes")
    
    # Migrate revenue nodes
    migration_query = """
    MATCH (r:REVENUE)
    WHERE r.source IS NOT NULL
    MATCH (rt:REVENUE_TYPE {name: r.source})
    MERGE (r)-[:HAS_TYPE]->(rt)
    RETURN count(r) as migrated
    """
    
    result = session.run(migration_query)
    migrated = result.single()['migrated']
    print(f"  ✓ Migrated {migrated} REVENUE nodes")

def verify_migration(session):
    """Verify the migration was successful"""
    
    print("\n5. Verifying migration...")
    
    checks = [
        {
            "name": "MARKETING_CHANNEL relationships",
            "query": """
                MATCH (m:MARKETING_CHANNEL)-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """
        },
        {
            "name": "PROJECTION relationships",
            "query": """
                MATCH (p:PROJECTION)-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """
        },
        {
            "name": "REVENUE relationships",
            "query": """
                MATCH (r:REVENUE)-[:HAS_TYPE]->(rt:REVENUE_TYPE)
                RETURN rt.name as type, count(r) as count
            """
        }
    ]
    
    for check in checks:
        print(f"\n  {check['name']}:")
        result = session.run(check['query'])
        for record in result:
            if 'rel_type' in record:
                print(f"    - {record['rel_type']}: {record['count']}")
            elif 'type' in record:
                print(f"    - {record['type']}: {record['count']}")
            else:
                print(f"    - {dict(record)}")

def test_queries(session):
    """Test if queries work better with the new model"""
    
    print("\n6. Testing sample queries...")
    
    test_queries = [
        {
            "name": "Marketing ROI (Q53)",
            "old": "MATCH (m:MARKETING_CHANNEL) RETURN m.name, m.roi",
            "new": """
                MATCH (m:MARKETING_CHANNEL)-[:ACHIEVES]->(p:PERFORMANCE_METRIC {type: 'ROI'})
                RETURN m.name as channel, p.value as roi
                ORDER BY p.value DESC
            """
        },
        {
            "name": "Revenue Projections (Q7)",
            "old": "MATCH (p:PROJECTION) WHERE p.quarter STARTS WITH 'Q' RETURN p.quarter, p.projected_revenue",
            "new": """
                MATCH (p:PROJECTION)-[:FOR_PERIOD]->(q:QUARTER)
                MATCH (p)-[:PROJECTS]->(m:METRIC {type: 'projected_revenue'})
                RETURN q.full_name as quarter, m.value as revenue
                ORDER BY q.year, q.name
            """
        },
        {
            "name": "Revenue Types (Q52)",
            "old": "MATCH (r:REVENUE) RETURN r.source, sum(r.amount)",
            "new": """
                MATCH (r:REVENUE)-[:HAS_TYPE]->(rt:REVENUE_TYPE)
                RETURN rt.name as type, sum(r.amount) as total
            """
        }
    ]
    
    for test in test_queries:
        print(f"\n  Testing: {test['name']}")
        try:
            result = session.run(test['new'])
            records = list(result)
            if records:
                print(f"    ✓ Success - {len(records)} results")
                for record in records[:2]:
                    print(f"      {dict(record)}")
            else:
                print("    ⚠️  No results")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def main():
    config = Config.from_env()
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_username, config.neo4j_password)
    )
    
    with driver.session() as session:
        print("PHASE 1: RELATIONSHIP-CENTRIC MODEL MIGRATION")
        print("=" * 60)
        
        try:
            # Execute migration steps
            create_new_node_types(session)
            migrate_marketing_channels(session)
            migrate_projections(session)
            migrate_revenue_types(session)
            verify_migration(session)
            test_queries(session)
            
            print("\n✅ Migration completed successfully!")
            print("\nNOTE: Original properties have been retained for validation.")
            print("Once queries are verified, run cleanup script to remove them.")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            raise
    
    driver.close()

if __name__ == "__main__":
    main()