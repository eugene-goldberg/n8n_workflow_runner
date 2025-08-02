#!/usr/bin/env python3
"""Check if specific entities mentioned in test script exist"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== CHECKING SPECIFIC ENTITIES ===\n")

with driver.session() as session:
    # Check for TechCorp
    print("1. Checking for 'TechCorp':")
    result = session.run("""
        MATCH (n:__Entity__)
        WHERE n.name = 'TechCorp'
        RETURN labels(n) as labels, n.name as name
    """)
    found = False
    for r in result:
        print(f"   Found: {r['name']} with labels {r['labels']}")
        found = True
    if not found:
        print("   NOT FOUND")
    
    # Check for Multi-region deployment
    print("\n2. Checking for 'Multi-region deployment':")
    result = session.run("""
        MATCH (n:__Entity__)
        WHERE n.name CONTAINS 'Multi-region' OR n.title CONTAINS 'Multi-region'
        RETURN labels(n) as labels, coalesce(n.name, n.title) as name
    """)
    found = False
    for r in result:
        print(f"   Found: {r['name']} with labels {r['labels']}")
        found = True
    if not found:
        print("   NOT FOUND - Checking similar roadmap items:")
        result = session.run("""
            MATCH (n:__Entity__:ROADMAP_ITEM)
            RETURN n.title as title
            LIMIT 5
        """)
        for r in result:
            print(f"     - {r['title']}")
    
    # Check for Market Expansion objective
    print("\n3. Checking for 'Market Expansion' objective:")
    result = session.run("""
        MATCH (n:__Entity__)
        WHERE n.name CONTAINS 'Market Expansion' OR n.title CONTAINS 'Market Expansion'
        RETURN labels(n) as labels, coalesce(n.name, n.title) as name
    """)
    found = False
    for r in result:
        print(f"   Found: {r['name']} with labels {r['labels']}")
        found = True
    if not found:
        print("   NOT FOUND - Checking similar objectives:")
        result = session.run("""
            MATCH (n:__Entity__:OBJECTIVE)
            RETURN n.title as title
            LIMIT 5
        """)
        for r in result:
            print(f"     - {r['title']}")

driver.close()