#!/usr/bin/env python3
"""
Clean all data from Neo4j database
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def clean_database():
    """Remove all data from Neo4j"""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # Delete all nodes and relationships
        logger.info("Deleting all nodes and relationships...")
        result = session.run("MATCH (n) DETACH DELETE n")
        logger.info("✅ All nodes and relationships deleted")
        
        # Drop all indexes except system indexes
        logger.info("\nDropping all custom indexes...")
        indexes = session.run("SHOW INDEXES").data()
        
        for index in indexes:
            index_name = index['name']
            # Skip system indexes
            if index_name.startswith('index_'):
                continue
                
            try:
                session.run(f"DROP INDEX {index_name}")
                logger.info(f"Dropped index: {index_name}")
            except Exception as e:
                logger.warning(f"Could not drop index {index_name}: {e}")
        
        # Verify cleanup
        node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
        logger.info(f"\n✅ Database cleaned. Node count: {node_count}")
    
    driver.close()

if __name__ == "__main__":
    clean_database()