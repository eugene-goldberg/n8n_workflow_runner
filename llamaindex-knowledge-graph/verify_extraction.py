#!/usr/bin/env python3
"""Verify what was extracted from the SpyroSolutions reports"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

print("=== VERIFYING SPYROSOLUTIONS KNOWLEDGE GRAPH EXTRACTION ===\n")

with driver.session() as session:
    # Count new entities by type
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE n.name IS NOT NULL
        RETURN labels(n) as labels, n.name as name
        ORDER BY n.name
        LIMIT 50
    ''')
    
    print("EXTRACTED ENTITIES:")
    entities_by_type = {}
    for record in result:
        labels = [l for l in record['labels'] if l != '__Entity__']
        entity_type = labels[0] if labels else 'Unknown'
        name = record['name']
        
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(name)
    
    for entity_type, names in sorted(entities_by_type.items()):
        print(f"\n{entity_type} ({len(names)}):")
        for name in names[:5]:  # Show first 5
            print(f"  - {name}")
        if len(names) > 5:
            print(f"  ... and {len(names) - 5} more")
    
    # Look for specific entities mentioned in reports
    print("\n\nSPECIFIC ENTITIES FROM REPORTS:")
    
    # New customers
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE n.name IN ['InnovateTech Solutions', 'Global Manufacturing Corp', 'InnovateTech', 'Global Manufacturing']
        RETURN n.name as name, labels(n) as labels
    ''')
    print("\nNew Customers Found:")
    for r in result:
        print(f"  - {r['name']} (Type: {[l for l in r['labels'] if l != '__Entity__']})")
    
    # Teams
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE n.name CONTAINS 'Team' OR n.name IN ['Cloud Platform Team', 'AI Research Team', 'Innovation Lab']
        RETURN DISTINCT n.name as name
        LIMIT 10
    ''')
    print("\nTeams Extracted:")
    for r in result:
        print(f"  - {r['name']}")
    
    # Projects and features
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE n.name IN ['Project Titan', 'Project Mercury', 'Project Venus', 'Multi-region deployment', 'Kubernetes migration']
        RETURN n.name as name, labels(n) as labels
    ''')
    print("\nProjects/Features Found:")
    for r in result:
        print(f"  - {r['name']} (Type: {[l for l in r['labels'] if l != '__Entity__']})")
    
    # Risks
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE any(label in labels(n) WHERE label CONTAINS 'RISK') OR n.name CONTAINS 'risk'
        RETURN DISTINCT n.name as name
        LIMIT 10
    ''')
    print("\nRisks Identified:")
    for r in result:
        print(f"  - {r['name']}")
    
    # Financial metrics
    result = session.run('''
        MATCH (n:__Entity__)
        WHERE any(label in labels(n) WHERE label IN ['REVENUE', 'COST', 'PROFITABILITY', 'ARR'])
        OR n.name CONTAINS 'revenue' OR n.name CONTAINS 'cost' OR n.name CONTAINS '$'
        RETURN DISTINCT n.name as name
        LIMIT 10
    ''')
    print("\nFinancial Entities:")
    for r in result:
        print(f"  - {r['name']}")
    
    # Key relationships discovered
    print("\n\nKEY RELATIONSHIPS DISCOVERED:")
    
    result = session.run('''
        MATCH (n1:__Entity__)-[r]->(n2:__Entity__)
        WHERE n1.name IS NOT NULL AND n2.name IS NOT NULL
        RETURN n1.name as source, type(r) as relationship, n2.name as target
        LIMIT 20
    ''')
    
    relationships = []
    for r in result:
        relationships.append(f"{r['source']} --[{r['relationship']}]--> {r['target']}")
    
    for rel in relationships[:15]:
        print(f"  - {rel}")
    if len(relationships) > 15:
        print(f"  ... and more relationships")
    
    # Summary statistics
    print("\n\nSUMMARY STATISTICS:")
    
    # Total extracted entities
    result = session.run('MATCH (n:__Entity__) RETURN count(n) as count')
    total_entities = result.single()['count']
    
    # Total relationships
    result = session.run('MATCH (n1:__Entity__)-[r]->(n2:__Entity__) RETURN count(r) as count')
    total_relationships = result.single()['count']
    
    print(f"Total entities extracted: {total_entities}")
    print(f"Total relationships created: {total_relationships}")
    
    # Document chunks
    result = session.run('MATCH (n:Chunk) RETURN count(n) as count')
    chunks = result.single()['count']
    print(f"Document chunks processed: {chunks}")

driver.close()

print("\n✅ Verification complete! The knowledge graph has been enriched with SpyroSolutions business data.")