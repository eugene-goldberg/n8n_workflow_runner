#!/usr/bin/env python3
"""Simple test of Neo4j connectivity and basic queries"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from config.settings import settings

def test_basic_connection():
    """Test basic Neo4j connection"""
    print("=== TESTING NEO4J CONNECTION ===\n")
    
    print(f"URI: {settings.neo4j.uri}")
    print(f"Username: {settings.neo4j.username}")
    
    # Test with neo4j driver
    try:
        driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
        
        with driver.session() as session:
            # Simple test query
            result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
            count = result.single()['count']
            print(f"\n✓ Connected successfully! Total nodes: {count}")
            
            # Test specific entities
            print("\nTesting specific queries:")
            
            # Customers
            result = session.run("""
                MATCH (c:__Entity__:CUSTOMER)
                RETURN c.name as name
                LIMIT 5
            """)
            customers = [r['name'] for r in result]
            print(f"✓ Sample customers: {customers}")
            
            # Products
            result = session.run("""
                MATCH (p:__Entity__:PRODUCT)
                RETURN p.name as name
                LIMIT 5
            """)
            products = [r['name'] for r in result]
            print(f"✓ Sample products: {products}")
            
        driver.close()
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False
    
    # Test with LangChain Neo4jGraph
    print("\n\nTesting LangChain Neo4jGraph:")
    try:
        graph = Neo4jGraph(
            url=settings.neo4j.uri,
            username=settings.neo4j.username,
            password=settings.neo4j.password
        )
        
        # Get schema
        print("✓ Connected via LangChain")
        print(f"✓ Schema loaded: {len(graph.get_schema)} characters")
        
        # Test a simple query
        result = graph.query("MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT) RETURN c.name as customer, p.name as product LIMIT 3")
        print(f"✓ Sample relationships: {result}")
        
    except Exception as e:
        print(f"✗ LangChain connection failed: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    return True

if __name__ == "__main__":
    test_basic_connection()