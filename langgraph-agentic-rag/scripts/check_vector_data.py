#!/usr/bin/env python3
"""Check vector data in Neo4j"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings

def check_vector_data():
    """Check what vector data exists in Neo4j"""
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    with driver.session() as session:
        print("=== VECTOR DATA IN NEO4J ===\n")
        
        # Check __Entity__ nodes with embeddings
        result = session.run("""
            MATCH (n:__Entity__)
            WHERE n.embedding IS NOT NULL
            RETURN count(n) as count, 
                   collect(DISTINCT labels(n)) as label_combinations
        """)
        record = result.single()
        print(f"1. __Entity__ nodes with embeddings: {record['count']}")
        print(f"   Label combinations: {record['label_combinations'][:5]}...")
        
        # Check __Chunk__ nodes with embeddings
        result = session.run("""
            MATCH (n:__Chunk__)
            WHERE n.embedding IS NOT NULL
            RETURN count(n) as count
        """)
        record = result.single()
        print(f"\n2. __Chunk__ nodes with embeddings: {record['count']}")
        
        # Sample some entities with embeddings
        print("\n3. Sample entities with embeddings:")
        result = session.run("""
            MATCH (n:__Entity__)
            WHERE n.embedding IS NOT NULL
            RETURN labels(n) as labels, 
                   n.name as name,
                   n.description as description,
                   size(n.embedding) as embedding_size
            LIMIT 5
        """)
        for record in result:
            print(f"   - {record['labels']}: {record['name']} (embedding size: {record['embedding_size']})")
            if record['description']:
                print(f"     Description: {record['description'][:100]}...")
        
        # Sample some chunks with embeddings
        print("\n4. Sample chunks with embeddings:")
        result = session.run("""
            MATCH (n:__Chunk__)
            WHERE n.embedding IS NOT NULL
            RETURN n.text as text,
                   size(n.embedding) as embedding_size
            LIMIT 3
        """)
        for record in result:
            print(f"   - Text: {record['text'][:100]}...")
            print(f"     Embedding size: {record['embedding_size']}")
        
        # Check if there are any EVENT nodes with date properties
        print("\n5. Event data check:")
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            RETURN count(e) as total_events,
                   count(e.date) as events_with_date,
                   count(e.event_date) as events_with_event_date,
                   count(e.timestamp) as events_with_timestamp
        """)
        record = result.single()
        print(f"   Total EVENT entities: {record['total_events']}")
        print(f"   Events with 'date' property: {record['events_with_date']}")
        print(f"   Events with 'event_date' property: {record['events_with_event_date']}")
        print(f"   Events with 'timestamp' property: {record['events_with_timestamp']}")
        
        # Sample EVENT properties
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            RETURN keys(e) as properties
            LIMIT 5
        """)
        print("\n   Sample EVENT properties:")
        for record in result:
            print(f"   - {record['properties']}")
        
    driver.close()

if __name__ == "__main__":
    check_vector_data()