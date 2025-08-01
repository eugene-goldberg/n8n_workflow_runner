#!/usr/bin/env python3

import neo4j

driver = neo4j.GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    # Check customers
    result = session.run('MATCH (c:Customer) RETURN c.name as name, c.arr as arr LIMIT 5')
    print('=== Customers ===')
    for record in result:
        print(f'{record["name"]}: ARR ${record["arr"]:,}')
    
    # Check products
    result = session.run('MATCH (p:Product) RETURN p.name as name LIMIT 5')
    print('\n=== Products ===')
    for record in result:
        print(record['name'])
    
    # Check relationships
    result = session.run('MATCH (c:Customer)-[r:USES]->(p:Product) RETURN c.name as customer, p.name as product LIMIT 5')
    print('\n=== Customer->Product Relationships ===')
    for record in result:
        print(f'{record["customer"]} uses {record["product"]}')
    
    # Check if customers have all required fields
    result = session.run('MATCH (c:Customer) RETURN c LIMIT 1')
    print('\n=== Customer Properties ===')
    for record in result:
        customer = record['c']
        print(f'Properties: {list(customer.keys())}')

driver.close()