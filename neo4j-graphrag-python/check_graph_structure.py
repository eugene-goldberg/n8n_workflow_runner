#!/usr/bin/env python3

import neo4j

driver = neo4j.GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    # Check all node labels
    result = session.run('MATCH (n) RETURN DISTINCT labels(n) as labels, count(*) as count ORDER BY count DESC')
    print('=== Node Labels and Counts ===')
    for record in result:
        print(f'{record["labels"]}: {record["count"]}')
    
    # Check Customer nodes specifically
    result = session.run('MATCH (c:Customer) RETURN c LIMIT 1')
    print('\n=== Sample Customer Node ===')
    for record in result:
        customer = record['c']
        if customer:
            print(f'Properties: {dict(customer)}')
    
    # Check relationships
    result = session.run('MATCH ()-[r]->() RETURN DISTINCT type(r) as type, count(*) as count ORDER BY count DESC')
    print('\n=== Relationship Types and Counts ===')
    for record in result:
        print(f'{record["type"]}: {record["count"]}')
    
    # Check specific customer relationships
    result = session.run('MATCH (c:Customer {name: "TechCorp Industries"})-[r]->(n) RETURN type(r) as rel_type, labels(n) as target_labels, n.name as target_name')
    print('\n=== TechCorp Industries Relationships ===')
    for record in result:
        print(f'{record["rel_type"]} -> {record["target_labels"]}: {record["target_name"]}')

driver.close()