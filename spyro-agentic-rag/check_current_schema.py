#!/usr/bin/env python3
"""Check current schema status in Neo4j"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== CURRENT SCHEMA STATUS ===\n")

with driver.session() as session:
    # Check for old Spyro RAG format
    print("1. OLD SPYRO RAG FORMAT (e.g., :Customer):")
    print("-" * 50)
    
    old_labels = ["Customer", "Product", "Team", "Risk", "SaaSSubscription", 
                  "AnnualRecurringRevenue", "Feature", "Project"]
    
    for label in old_labels:
        result = session.run(f"""
            MATCH (n:{label})
            RETURN count(n) as count
        """)
        count = result.single()['count']
        if count > 0:
            print(f"  {label}: {count} entities")
    
    # Check for LlamaIndex format
    print("\n2. LLAMAINDEX FORMAT (e.g., :__Entity__:CUSTOMER):")
    print("-" * 50)
    
    # Get distinct entity types
    entity_types = ['CUSTOMER', 'PRODUCT', 'TEAM', 'PROJECT', 'RISK', 'SUBSCRIPTION', 
                    'REVENUE', 'FEATURE', 'ROADMAP_ITEM', 'CUSTOMER_SUCCESS_SCORE', 
                    'EVENT', 'COST', 'PROFITABILITY', 'OBJECTIVE']
    
    for entity_type in entity_types:
        result = session.run(f"""
            MATCH (n:__Entity__:{entity_type})
            RETURN count(n) as count
        """)
        count = result.single()['count']
        if count > 0:
            print(f"  {entity_type}: {count} entities")
    
    # Total counts
    print("\n3. TOTAL ENTITY COUNTS:")
    print("-" * 50)
    
    # Old format total
    result = session.run("""
        MATCH (n)
        WHERE any(label in labels(n) WHERE label IN $old_labels)
        RETURN count(n) as count
    """, old_labels=old_labels)
    old_total = result.single()['count']
    
    # LlamaIndex format total
    result = session.run("""
        MATCH (n:__Entity__)
        RETURN count(n) as count
    """)
    llama_total = result.single()['count']
    
    print(f"  Old Spyro RAG format: {old_total} entities")
    print(f"  LlamaIndex format: {llama_total} entities")
    print(f"  Total entities: {old_total + llama_total}")
    
    # Sample entities
    print("\n4. SAMPLE ENTITIES:")
    print("-" * 50)
    
    # Old format samples
    if old_total > 0:
        print("\nOld format samples:")
        result = session.run("""
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN $old_labels)
            RETURN n.name as name, labels(n) as labels
            LIMIT 3
        """, old_labels=old_labels)
        for r in result:
            print(f"  - {r['name']}: {r['labels']}")
    
    # LlamaIndex format samples
    if llama_total > 0:
        print("\nLlamaIndex format samples:")
        result = session.run("""
            MATCH (n:__Entity__)
            WHERE n.name IS NOT NULL
            RETURN n.name as name, labels(n) as labels
            LIMIT 3
        """)
        for r in result:
            print(f"  - {r['name']}: {r['labels']}")

driver.close()

print("\n=== RECOMMENDATION ===")
if old_total > 0 and llama_total > 0:
    print("You have MIXED schemas. Run ./migrate_to_llamaindex.py to migrate all data to LlamaIndex format.")
elif old_total > 0:
    print("You have ONLY old Spyro RAG format. Run ./migrate_to_llamaindex.py to migrate to LlamaIndex format.")
elif llama_total > 0:
    print("You have ONLY LlamaIndex format. No migration needed!")
else:
    print("No entities found in the database.")