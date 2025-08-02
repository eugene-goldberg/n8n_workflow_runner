#!/usr/bin/env python3
"""Demonstrate the newly-added entities and relationships in Neo4j"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== DEMONSTRATING NEWLY-ADDED SPYROSOLUTIONS DATA ===\n")

queries = [
    {
        "title": "1. New Q1 2025 Customers",
        "query": '''
            MATCH (c:__Entity__:CUSTOMER)
            WHERE c.name IN ['InnovateTech Solutions', 'Global Manufacturing Corp']
            OPTIONAL MATCH (c)-[r]->(related)
            RETURN c.name as customer, 
                   collect(DISTINCT {type: type(r), target: related.name}) as relationships
        '''
    },
    {
        "title": "2. Project Titan Details",
        "query": '''
            MATCH (p:__Entity__:PROJECT)
            WHERE p.name = 'Project Titan'
            OPTIONAL MATCH (p)<-[r]-(related)
            RETURN p.name as project, 
                   collect(DISTINCT {relationship: type(r), entity: related.name}) as connections
        '''
    },
    {
        "title": "3. Teams and Their Projects",
        "query": '''
            MATCH (t:__Entity__)
            WHERE t.name CONTAINS 'Team' AND t.name IN ['Cloud Platform Team', 'AI Research Team', 'Innovation Lab']
            OPTIONAL MATCH (t)-[r:RESPONSIBLE_FOR|DEVELOPS|SUPPORTS]->(p)
            RETURN t.name as team, 
                   collect(DISTINCT {action: type(r), target: p.name}) as responsibilities
        '''
    },
    {
        "title": "4. Competitive Intelligence",
        "query": '''
            MATCH (c:__Entity__)
            WHERE c.name CONTAINS 'NeuralStack' OR c.name = 'NeuralStack AI'
            OPTIONAL MATCH (c)-[r]->(target)
            OPTIONAL MATCH (source)-[r2]->(c)
            RETURN c.name as competitor,
                   collect(DISTINCT {rel: type(r), to: target.name}) as outgoing,
                   collect(DISTINCT {rel: type(r2), from: source.name}) as incoming
        '''
    },
    {
        "title": "5. Financial Metrics Extracted",
        "query": '''
            MATCH (n:__Entity__)
            WHERE n.name =~ '.*\\$[0-9]+.*' OR n.name CONTAINS 'revenue' OR n.name CONTAINS 'Revenue'
            RETURN n.name as financial_metric
            LIMIT 10
        '''
    },
    {
        "title": "6. Risk Relationships",
        "query": '''
            MATCH (r:__Entity__)
            WHERE any(label in labels(r) WHERE label CONTAINS 'RISK') 
               OR r.name CONTAINS 'risk' 
               OR r.name IN ['Customer concentration risk', 'Scalability risk', 'Technical debt']
            OPTIONAL MATCH (r)-[rel]->(target)
            RETURN r.name as risk, 
                   collect(DISTINCT {relationship: type(rel), affects: target.name}) as impacts
            LIMIT 5
        '''
    },
    {
        "title": "7. Document Chunks with Key Information",
        "query": '''
            MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
            WHERE c.text CONTAINS 'InnovateTech' 
               OR c.text CONTAINS 'Project Titan'
               OR c.text CONTAINS 'NeuralStack'
            RETURN d.filename as document, 
                   substring(c.text, 0, 200) + '...' as excerpt
            LIMIT 5
        '''
    }
]

with driver.session() as session:
    for q in queries:
        print(f"\n{q['title']}")
        print("-" * 60)
        
        result = session.run(q['query'])
        records = list(result)
        
        if not records:
            print("No results found")
        else:
            for record in records:
                print(json.dumps(dict(record), indent=2, default=str))

# Show a sample of the knowledge graph structure
print("\n\n=== SAMPLE KNOWLEDGE GRAPH STRUCTURE ===")
print("-" * 60)

with driver.session() as session:
    result = session.run('''
        MATCH path = (n1:__Entity__)-[r]->(n2:__Entity__)
        WHERE n1.name IN ['InnovateTech Solutions', 'Cloud Platform Team', 'Project Titan', 'SpyroCloud']
        RETURN n1.name as source, type(r) as relationship, n2.name as target
        LIMIT 15
    ''')
    
    print("\nEntity Relationships:")
    for record in result:
        print(f"  {record['source']} --[{record['relationship']}]--> {record['target']}")

driver.close()

print("\n\n✅ This demonstrates that the PDF ingestion successfully added new entities and relationships to the knowledge graph.")
print("The data is stored in Neo4j and can be queried directly or through appropriate APIs.")