#!/usr/bin/env python3

import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

# Define schema
SPYRO_SCHEMA = """
Node properties:
Customer {name: STRING}
SaaSSubscription {plan: STRING, ARR: STRING}

The relationships:
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
"""

# Example
EXAMPLES = [
    "USER INPUT: 'Show customer subscriptions' QUERY: MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription) RETURN c.name as customer, s.plan as plan, s.ARR as arr"
]

# Create LLM
llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})

with neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
    retriever = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=SPYRO_SCHEMA,
        examples=EXAMPLES
    )
    
    query = "Which customers have which subscription plans and ARR?"
    results = retriever.search(query_text=query)
    
    print(f"Results type: {type(results)}")
    print(f"Results items: {len(results.items)}")
    
    for i, item in enumerate(results.items[:3]):
        print(f"\nItem {i}:")
        print(f"  Type: {type(item)}")
        print(f"  Content type: {type(item.content)}")
        print(f"  Content: {item.content}")
        
        # Try to access the content
        if hasattr(item.content, '__dict__'):
            print(f"  Content dict: {item.content.__dict__}")
        if hasattr(item.content, 'data'):
            print(f"  Content data: {item.content.data()}")
        if hasattr(item.content, 'keys'):
            print(f"  Content keys: {list(item.content.keys())}")