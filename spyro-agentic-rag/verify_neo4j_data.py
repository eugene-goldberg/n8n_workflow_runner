#!/usr/bin/env python3
"""Verify Neo4j data and indexes"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def check_data():
    """Check what data exists in Neo4j"""
    with driver.session() as session:
        print("=== Checking Neo4j Data ===\n")
        
        # Count entities by type
        print("1. Entity counts by label:")
        result = session.run("""
            MATCH (n)
            UNWIND labels(n) as label
            RETURN label, count(*) as count
            ORDER BY count DESC
        """)
        for record in result:
            print(f"   {record['label']}: {record['count']}")
        
        # Check for customers
        print("\n2. Sample customers:")
        result = session.run("""
            MATCH (c) 
            WHERE 'Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
            RETURN c.name as name, labels(c) as labels
            LIMIT 5
        """)
        for record in result:
            print(f"   - {record['name']} (labels: {record['labels']})")
        
        # Check for subscriptions
        print("\n3. Sample subscriptions:")
        result = session.run("""
            MATCH (c)-[:SUBSCRIBES_TO]->(s)
            WHERE 'Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
            RETURN c.name as customer, s.value as value, labels(s) as labels
            LIMIT 5
        """)
        for record in result:
            print(f"   - {record['customer']}: {record['value']} (labels: {record['labels']})")
        
        # Check for success scores
        print("\n4. Sample success scores:")
        result = session.run("""
            MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
            WHERE 'Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
            RETURN c.name as customer, s.score as score, s.value as value
            LIMIT 5
        """)
        for record in result:
            score = record['score'] or record['value']
            print(f"   - {record['customer']}: {score}")
        
        # Check indexes
        print("\n5. Indexes:")
        result = session.run("SHOW INDEXES")
        for record in result:
            print(f"   - {record['name']} on {record['labelsOrTypes']} ({record['properties']})")

if __name__ == "__main__":
    try:
        check_data()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()