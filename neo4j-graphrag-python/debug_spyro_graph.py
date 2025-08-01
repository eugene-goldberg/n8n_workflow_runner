#!/usr/bin/env python3
"""
Debug what's in the SpyroSolutions graph
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def debug_graph():
    """Check what's in the graph"""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # Count all nodes by label
        logger.info("=== Node Counts by Label ===")
        result = session.run("""
            MATCH (n)
            RETURN labels(n) as labels, count(*) as count
            ORDER BY count DESC
        """)
        for record in result:
            logger.info(f"Labels: {record['labels']}, Count: {record['count']}")
        
        # Check chunks
        logger.info("\n=== Chunk Nodes ===")
        result = session.run("""
            MATCH (n)
            WHERE n.text IS NOT NULL AND n.embedding IS NOT NULL
            RETURN labels(n) as labels, 
                   substring(n.text, 0, 100) as text_preview,
                   size(n.embedding) as embedding_size
            LIMIT 5
        """)
        for record in result:
            logger.info(f"Labels: {record['labels']}")
            logger.info(f"Text: {record['text_preview']}...")
            logger.info(f"Embedding size: {record['embedding_size']}")
            logger.info("-" * 40)
        
        # Check relationships
        logger.info("\n=== Relationship Types ===")
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        for record in result:
            logger.info(f"Type: {record['type']}, Count: {record['count']}")
        
        # Check specific entities
        logger.info("\n=== Sample Entities ===")
        result = session.run("""
            MATCH (n)
            WHERE n.name IS NOT NULL
            RETURN labels(n) as labels, n.name as name
            LIMIT 10
        """)
        for record in result:
            logger.info(f"Entity: {record['name']}, Labels: {record['labels']}")
        
        # Check indexes
        logger.info("\n=== Indexes ===")
        result = session.run("SHOW INDEXES")
        for record in result:
            if record['type'] in ['VECTOR', 'FULLTEXT']:
                logger.info(f"Name: {record['name']}, Type: {record['type']}, Labels: {record['labelsOrTypes']}")
    
    driver.close()

if __name__ == "__main__":
    debug_graph()