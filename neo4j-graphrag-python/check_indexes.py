#!/usr/bin/env python3
"""
Check existing indexes in Neo4j
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def check_indexes():
    """Check all indexes in Neo4j"""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # List all indexes
        result = session.run("SHOW INDEXES")
        
        logger.info("=== All Indexes ===")
        for record in result:
            logger.info(f"Name: {record['name']}")
            logger.info(f"Type: {record['type']}")
            logger.info(f"Labels: {record['labelsOrTypes']}")
            logger.info(f"Properties: {record['properties']}")
            logger.info(f"State: {record['state']}")
            logger.info("-" * 40)
        
        # Check nodes with embeddings
        result = session.run("""
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            RETURN DISTINCT labels(n) as labels, count(*) as count
        """)
        
        logger.info("\n=== Nodes with Embeddings ===")
        for record in result:
            logger.info(f"Labels: {record['labels']}, Count: {record['count']}")
        
        # Check nodes with text
        result = session.run("""
            MATCH (n)
            WHERE n.text IS NOT NULL
            RETURN DISTINCT labels(n) as labels, count(*) as count
            LIMIT 10
        """)
        
        logger.info("\n=== Nodes with Text ===")
        for record in result:
            logger.info(f"Labels: {record['labels']}, Count: {record['count']}")
    
    driver.close()

if __name__ == "__main__":
    check_indexes()