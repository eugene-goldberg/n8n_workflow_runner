#!/usr/bin/env python3
"""
Debug chunk nodes and fix labeling
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def debug_and_fix_chunks():
    """Check and fix chunk labels"""
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, 
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )
    
    with driver.session() as session:
        # Check current chunk nodes
        result = session.run("""
            MATCH (n)
            WHERE n.text IS NOT NULL AND n.embedding IS NOT NULL
            RETURN labels(n) as labels, count(*) as count, 
                   collect(id(n))[0..3] as sample_ids
        """)
        
        logger.info("=== Current Chunk Nodes ===")
        for record in result:
            logger.info(f"Labels: {record['labels']}, Count: {record['count']}")
            
            # If nodes have 'Chunk' but not '__Chunk__', add the label
            if 'Chunk' in record['labels'] and '__Chunk__' not in record['labels']:
                logger.info("Adding __Chunk__ label to nodes...")
                session.run("""
                    MATCH (n:Chunk)
                    WHERE n.text IS NOT NULL AND n.embedding IS NOT NULL
                    SET n:`__Chunk__`
                """)
                logger.info("✅ Added __Chunk__ label")
        
        # Verify the fix
        result = session.run("""
            MATCH (n:`__Chunk__`)
            RETURN count(n) as count
        """)
        count = result.single()['count']
        logger.info(f"\n✅ Total nodes with __Chunk__ label: {count}")
        
        # Check a sample chunk
        result = session.run("""
            MATCH (n:`__Chunk__`)
            RETURN substring(n.text, 0, 200) as text_preview,
                   size(n.embedding) as embedding_size,
                   keys(n) as properties
            LIMIT 1
        """)
        
        for record in result:
            logger.info("\n=== Sample Chunk ===")
            logger.info(f"Text preview: {record['text_preview']}...")
            logger.info(f"Embedding size: {record['embedding_size']}")
            logger.info(f"Properties: {record['properties']}")
    
    driver.close()

if __name__ == "__main__":
    debug_and_fix_chunks()