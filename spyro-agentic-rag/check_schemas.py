#!/usr/bin/env python3
"""Check what schemas exist in Neo4j"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== SCHEMA CHECK ===\n")

with driver.session() as session:
    # 1. Count entities by label format
    print("1. ENTITY COUNTS BY FORMAT:")
    print("-" * 40)
    
    # Spyro RAG format
    result = session.run("""
        MATCH (n)
        WHERE 'Customer' IN labels(n) 
           OR 'Product' IN labels(n) 
           OR 'Team' IN labels(n)
           OR 'Risk' IN labels(n)
        RETURN 'Spyro RAG Format' as format, count(n) as count
    """)
    for r in result:
        print(f"{r['format']}: {r['count']} entities")
    
    # LlamaIndex format
    result = session.run("""
        MATCH (n:__Entity__)
        RETURN 'LlamaIndex Format' as format, count(n) as count
    """)
    for r in result:
        print(f"{r['format']}: {r['count']} entities")
    
    # 2. Sample customers from each format
    print("\n2. SAMPLE CUSTOMERS:")
    print("-" * 40)
    
    print("\nSpyro RAG Customers:")
    result = session.run("""
        MATCH (c:Customer)
        RETURN c.name as name
        LIMIT 5
    """)
    for r in result:
        print(f"  - {r['name']}")
    
    print("\nLlamaIndex Customers:")
    result = session.run("""
        MATCH (c:__Entity__)
        WHERE 'CUSTOMER' IN labels(c)
        RETURN c.name as name
        LIMIT 5
    """)
    for r in result:
        print(f"  - {r['name']}")
    
    # 3. Test a compatible query
    print("\n3. COMPATIBLE QUERY TEST:")
    print("-" * 40)
    print("Query: Find all customers (both formats)")
    
    result = session.run("""
        MATCH (c) 
        WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
        RETURN c.name as name, labels(c) as labels
        ORDER BY c.name
    """)
    
    count = 0
    for r in result:
        count += 1
        print(f"  - {r['name']} | Labels: {r['labels']}")
    
    print(f"\nTotal customers found: {count}")

driver.close()

print("\n=== END SCHEMA CHECK ===")