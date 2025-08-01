#!/usr/bin/env python3
"""Fix missing subscriptions and ARR data"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from neo4j import GraphDatabase

config = Config.from_env()
driver = GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password))

with driver.session(database=config.neo4j_database) as session:
    # Create subscriptions for customers that don't have them
    customers_data = [
        ('EduTech', 'SpyroCloud', 1500000),      # $1.5M
        ('StartupXYZ', 'SpyroAI', 2000000),      # $2M
        ('DataSync', 'SpyroCloud', 2500000),     # $2.5M
        ('RetailPlus', 'SpyroSecure', 3000000),  # $3M
        ('LogiCorp', 'SpyroCloud', 4000000),     # $4M
        ('MediaFlow', 'SpyroAI', 3500000),       # $3.5M
        ('HealthNet', 'SpyroSecure', 6000000),   # $6M
        ('CloudFirst', 'SpyroCloud', 7000000)    # $7M
    ]
    
    for customer, product, arr_amount in customers_data:
        # Create subscription
        session.run('''
            MATCH (c:Customer {name: $customer})
            MATCH (p:Product {name: $product})
            MERGE (s:SaaSSubscription {
                customer: $customer,
                product: $product,
                value: $value,
                status: 'Active',
                start_date: date('2024-01-01')
            })
            MERGE (c)-[:SUBSCRIBES_TO]->(s)
            MERGE (c)-[:USES]->(p)
            
            WITH s
            MERGE (arr:AnnualRecurringRevenue {
                subscription_id: s.customer + '_' + s.product,
                amount: $arr_amount,
                currency: 'USD',
                period: 'annual'
            })
            MERGE (s)-[:GENERATES]->(arr)
        ''', {
            'customer': customer,
            'product': product,
            'value': f'${arr_amount/1000000}M',
            'arr_amount': arr_amount
        })
    
    print('Created subscriptions and ARR for all customers')
    
    # Verify the data
    result = session.run('''
        MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
        WHERE css.score < 70
        MATCH (c)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
        WITH sum(arr.amount) as lowScoreARR
        MATCH (arr2:AnnualRecurringRevenue)
        WITH lowScoreARR, sum(arr2.amount) as totalARR
        RETURN (lowScoreARR / totalARR * 100) as percentage, lowScoreARR, totalARR
    ''')
    
    for record in result:
        print(f'\nLow-score customer ARR: ${record["lowScoreARR"]:,.0f}')
        print(f'Total ARR: ${record["totalARR"]:,.0f}')
        print(f'Percentage: {record["percentage"]:.1f}%')

driver.close()