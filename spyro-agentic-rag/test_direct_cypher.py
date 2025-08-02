#!/usr/bin/env python3
"""Test Cypher queries directly against Neo4j"""

from neo4j import GraphDatabase
import os
from src.utils.cypher_examples_extracted import EXTRACTED_CYPHER_EXAMPLES

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("Testing direct Cypher queries from examples...")
print("="*80)

with driver.session() as session:
    # Test the first few examples
    for i, example in enumerate(EXTRACTED_CYPHER_EXAMPLES[:3]):
        print(f"\n{i+1}. {example['question']}")
        print("-"*80)
        
        try:
            result = session.run(example['cypher'])
            records = list(result)
            
            if records:
                print(f"✅ Found {len(records)} results:")
                for j, record in enumerate(records[:3]):
                    print(f"   {dict(record)}")
                if len(records) > 3:
                    print(f"   ... and {len(records) - 3} more")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error: {e}")

driver.close()

print("\n" + "="*80)
print("Testing simple direct queries...")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

simple_queries = [
    ("Count products", "MATCH (p:__Entity__:PRODUCT) RETURN count(p) as count"),
    ("List products", "MATCH (p:__Entity__:PRODUCT) RETURN p.name as name"),
    ("Count operational costs", "MATCH (c:__Entity__:OPERATIONAL_COST) RETURN count(c) as count"),
    ("Sample costs", "MATCH (c:__Entity__:OPERATIONAL_COST) RETURN c.total_monthly_cost as cost LIMIT 5")
]

with driver.session() as session:
    for desc, query in simple_queries:
        print(f"\n{desc}: {query}")
        try:
            result = session.run(query)
            records = list(result)
            print(f"Results: {[dict(r) for r in records]}")
        except Exception as e:
            print(f"Error: {e}")

driver.close()