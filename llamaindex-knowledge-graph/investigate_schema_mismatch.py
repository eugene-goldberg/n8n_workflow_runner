#!/usr/bin/env python3
"""Investigate and demonstrate the schema mismatch between LlamaIndex and Spyro RAG"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== SCHEMA MISMATCH INVESTIGATION ===\n")

with driver.session() as session:
    # 1. Check how Spyro RAG stores entities
    print("1. SPYRO RAG ENTITY STRUCTURE:")
    print("-" * 50)
    result = session.run("""
        MATCH (c:Customer)
        RETURN c.name as name, labels(c) as labels
        LIMIT 3
    """)
    for r in result:
        print(f"Customer: {r['name']}")
        print(f"Labels: {r['labels']}")
    
    # 2. Check how LlamaIndex stores entities
    print("\n2. LLAMAINDEX ENTITY STRUCTURE:")
    print("-" * 50)
    result = session.run("""
        MATCH (n:__Entity__)
        WHERE n.name IN ['InnovateTech Solutions', 'Global Manufacturing Corp']
        RETURN n.name as name, labels(n) as labels
    """)
    for r in result:
        print(f"Entity: {r['name']}")
        print(f"Labels: {r['labels']}")
    
    # 3. Show the query patterns each system uses
    print("\n3. QUERY PATTERNS:")
    print("-" * 50)
    
    # Spyro RAG pattern
    print("Spyro RAG would query like this:")
    print("MATCH (c:Customer) WHERE c.name = 'InnovateTech Solutions'")
    result = session.run("""
        MATCH (c:Customer) 
        WHERE c.name = 'InnovateTech Solutions'
        RETURN count(c) as count
    """)
    spyro_count = result.single()['count']
    print(f"Result: {spyro_count} nodes found")
    
    # LlamaIndex pattern
    print("\nLlamaIndex stored it like this:")
    print("MATCH (n:__Entity__:CUSTOMER) WHERE n.name = 'InnovateTech Solutions'")
    result = session.run("""
        MATCH (n:__Entity__) 
        WHERE n.name = 'InnovateTech Solutions' AND 'CUSTOMER' IN labels(n)
        RETURN count(n) as count
    """)
    llama_count = result.single()['count']
    print(f"Result: {llama_count} nodes found")
    
    # 4. Show all label patterns
    print("\n4. ALL LABEL PATTERNS IN DATABASE:")
    print("-" * 50)
    result = session.run("""
        MATCH (n)
        WITH labels(n) as labelSet
        UNWIND labelSet as label
        RETURN DISTINCT label
        ORDER BY label
        LIMIT 20
    """)
    labels = [r['label'] for r in result]
    print(f"Labels found: {', '.join(labels)}")
    
    # 5. Demonstrate the problem
    print("\n5. DEMONSTRATION OF THE PROBLEM:")
    print("-" * 50)
    print("When Spyro RAG API searches for new customers:")
    
    result = session.run("""
        MATCH (c:Customer)
        WHERE c.name IN ['InnovateTech Solutions', 'Global Manufacturing Corp']
        RETURN c.name as name
    """)
    customers = [r['name'] for r in result]
    print(f"Found with :Customer label: {customers if customers else 'None'}")
    
    result = session.run("""
        MATCH (n:__Entity__)
        WHERE n.name IN ['InnovateTech Solutions', 'Global Manufacturing Corp']
        AND 'CUSTOMER' IN labels(n)
        RETURN n.name as name
    """)
    entities = [r['name'] for r in result]
    print(f"Found with :__Entity__:CUSTOMER labels: {entities}")

driver.close()

print("\n\n=== CONCLUSION ===")
print("The LlamaIndex pipeline stores entities with different labels than what")
print("the Spyro RAG API expects. This is why the API cannot find the new entities.")
print("\nPossible solutions:")
print("1. Update the LlamaIndex schema to match Spyro RAG expectations")
print("2. Modify Spyro RAG to search both label patterns")
print("3. Create a migration script to convert LlamaIndex entities to Spyro format")