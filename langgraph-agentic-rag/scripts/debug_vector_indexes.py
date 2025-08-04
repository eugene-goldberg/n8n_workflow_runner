#!/usr/bin/env python3
"""Debug vector indexes in Neo4j"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings

def debug_vector_indexes():
    """Debug what's in the vector indexes"""
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    with driver.session() as session:
        print("=== DEBUGGING VECTOR INDEXES ===\n")
        
        # Check __Entity__ nodes properties
        print("1. Sample __Entity__ nodes with embeddings:")
        result = session.run("""
            MATCH (n:__Entity__)
            WHERE n.embedding IS NOT NULL
            RETURN labels(n) as labels,
                   keys(n) as properties,
                   n.name as name,
                   n.description as description,
                   n.text as text,
                   n.content as content
            LIMIT 10
        """)
        for i, record in enumerate(result, 1):
            print(f"\n   Entity {i}:")
            print(f"   - Labels: {record['labels']}")
            print(f"   - Properties: {record['properties']}")
            print(f"   - Name: {record['name']}")
            print(f"   - Description: {record['description']}")
            print(f"   - Text: {record['text']}")
            print(f"   - Content: {record['content']}")
        
        # Check if there are any EVENT entities with embedding and descriptions
        print("\n\n2. EVENT entities with embeddings:")
        result = session.run("""
            MATCH (n:__Entity__:EVENT)
            WHERE n.embedding IS NOT NULL
            RETURN n.name as name,
                   n.description as description,
                   n.type as type,
                   n.impact as impact
            LIMIT 5
        """)
        count = 0
        for record in result:
            count += 1
            print(f"\n   Event: {record['name'] or 'Unnamed'}")
            print(f"   - Description: {record['description']}")
            print(f"   - Type: {record['type']}")
            print(f"   - Impact: {record['impact']}")
        
        if count == 0:
            print("   No EVENT entities found with embeddings")
        
        # Check vector index configuration
        print("\n\n3. Vector Index Details:")
        result = session.run("""
            SHOW INDEXES
            WHERE name IN ['entity', 'spyro_vector_index']
        """)
        for record in result:
            print(f"\n   Index: {record['name']}")
            print(f"   - Type: {record['type']}")
            print(f"   - Entity type: {record['labelsOrTypes']}")
            print(f"   - Properties: {record['properties']}")
            print(f"   - State: {record['state']}")
            
    driver.close()

if __name__ == "__main__":
    debug_vector_indexes()