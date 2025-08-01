#!/usr/bin/env python3
"""
Clean up duplicate relationships in the graph
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def cleanup_duplicates():
    """Remove duplicate relationships while keeping one of each type"""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # First, let's see what we have
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        logger.info("Current relationship counts:")
        for record in result:
            logger.info(f"  {record['rel_type']}: {record['count']}")
        
        # Keep only one of each duplicate relationship
        # This query finds duplicate relationships and deletes all but one
        result = session.run("""
            MATCH (a)-[r]->(b)
            WITH a, b, type(r) AS rel_type, collect(r) AS rels
            WHERE size(rels) > 1
            FOREACH (r IN tail(rels) | DELETE r)
            RETURN count(*) as deleted_count
        """)
        
        deleted = result.single()['deleted_count']
        logger.info(f"\nDeleted {deleted} duplicate relationships")
        
        # Verify the cleanup
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        logger.info("\nRelationship counts after cleanup:")
        for record in result:
            logger.info(f"  {record['rel_type']}: {record['count']}")
        
        # Check specific customer relationships
        result = session.run("""
            MATCH (c:Customer)-[:HAS_RISK]->(r:Risk), 
                  (c)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)
            RETURN DISTINCT c.name as customer, r.level as risk_level, s.ARR as revenue
            ORDER BY c.name
        """)
        
        logger.info("\nCustomer risk and revenue data:")
        for record in result:
            logger.info(f"  {record['customer']}: Risk={record['risk_level']}, Revenue={record['revenue']}")
    
    driver.close()

if __name__ == "__main__":
    cleanup_duplicates()