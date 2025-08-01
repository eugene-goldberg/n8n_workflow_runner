#!/usr/bin/env python3

import neo4j

driver = neo4j.GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    # Check Subscription nodes
    result = session.run('MATCH (s:SaaSSubscription) RETURN s LIMIT 5')
    print('=== SaaSSubscription Nodes ===')
    for record in result:
        subscription = record['s']
        print(f'Properties: {dict(subscription)}')
    
    # Check Customer->Subscription->Product chain
    result = session.run('''
        MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)
        RETURN c.name as customer, s as subscription
        LIMIT 5
    ''')
    print('\n=== Customer Subscriptions ===')
    for record in result:
        print(f'Customer: {record["customer"]}')
        print(f'Subscription properties: {dict(record["subscription"])}')
        print('---')
    
    # Check if subscriptions have product relationships
    result = session.run('''
        MATCH (s:SaaSSubscription)-[r]->(p)
        RETURN type(r) as rel_type, labels(p) as target_labels, p.name as product_name
        LIMIT 5
    ''')
    print('\n=== Subscription Relationships ===')
    for record in result:
        print(f'{record["rel_type"]} -> {record["target_labels"]}: {record["product_name"]}')

driver.close()