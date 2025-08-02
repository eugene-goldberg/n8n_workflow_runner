#!/usr/bin/env python3
"""Analyze existing Neo4j data for SpyroSolutions"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'), 
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session() as session:
    print('=== EXISTING SPYROSOLUTIONS ENTITIES ===\n')
    
    # Sample Customers
    result = session.run('''
        MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
        RETURN c.name as name, c.industry as industry, c.size as size, 
               c.region as region, css.score as score, css.trend as trend
        LIMIT 5
    ''')
    print('CUSTOMERS:')
    for r in result:
        print(f'  - {r["name"]} ({r["industry"]}, {r["size"]}) - Score: {r["score"]} ({r["trend"]})')
    
    # Sample Products
    result = session.run('''
        MATCH (p:Product)
        OPTIONAL MATCH (p)-[:HAS_COST]->(oc:OperationalCost)
        RETURN p.name as name, p.type as type, p.features as features, 
               p.sla_uptime_target as sla, oc.amount as cost
        LIMIT 5
    ''')
    print('\nPRODUCTS:')
    for r in result:
        print(f'  - {r["name"]} ({r["type"]}) - SLA: {r["sla"]}%, Cost: ${r["cost"]}/mo')
    
    # Sample Teams and Projects  
    result = session.run('''
        MATCH (t:Team)
        OPTIONAL MATCH (t)-[:SUPPORTS]->(p:Product)
        RETURN t.name as team, t.department as dept, t.size as size, 
               collect(p.name) as products
        LIMIT 5
    ''')
    print('\nTEAMS:')
    for r in result:
        products = r['products'] if r['products'] else ['All Products']
        print(f'  - {r["team"]} ({r["dept"]}, {r["size"]} people) - Supports: {", ".join(products) if products else "All Products"}')
    
    # Sample Risks
    result = session.run('''
        MATCH (r:Risk)
        OPTIONAL MATCH (c:Customer)-[:HAS_RISK]->(r)
        RETURN r.type as type, r.severity as severity, r.description as desc,
               r.probability as prob, c.name as customer
        LIMIT 5
    ''')
    print('\nRISKS:')
    for r in result:
        print(f'  - {r["type"]}/{r["severity"]}: {r["desc"][:50]}... (Customer: {r["customer"]})')
    
    # Sample Roadmap Items
    result = session.run('''
        MATCH (ri:RoadmapItem)<-[:HAS_ROADMAP]-(p:Product)
        OPTIONAL MATCH (t:Team)-[:RESPONSIBLE_FOR]->(ri)
        RETURN ri.title as title, ri.status as status, p.name as product,
               t.name as team, ri.priority as priority
        LIMIT 5
    ''')
    print('\nROADMAP ITEMS:')
    for r in result:
        print(f'  - {r["title"]} ({r["status"]}) - Product: {r["product"]}, Team: {r["team"]}')
    
    # Sample Subscriptions
    result = session.run('''
        MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:FOR_PRODUCT]->(p:Product)
        MATCH (s)-[:GENERATES]->(arr:AnnualRecurringRevenue)
        RETURN c.name as customer, p.name as product, s.value as value,
               s.status as status, arr.amount as arr
        LIMIT 5
    ''')
    print('\nSUBSCRIPTIONS:')
    for r in result:
        print(f'  - {r["customer"]} → {r["product"]}: {r["value"]} ({r["status"]}), ARR: ${r["arr"]:,.0f}')
    
    # Sample Objectives
    result = session.run('''
        MATCH (o:Objective)
        OPTIONAL MATCH (o)-[:AT_RISK]->(r:Risk)
        RETURN o.title as title, o.description as desc, o.status as status,
               count(r) as risk_count
        LIMIT 5
    ''')
    print('\nOBJECTIVES:')
    for r in result:
        print(f'  - {r["title"]} ({r["status"]}) - Risks: {r["risk_count"]}')
    
    # Sample Profitability
    result = session.run('''
        MATCH (p:Product)-[:HAS_PROFITABILITY]->(prof:Profitability)
        RETURN p.name as product, prof.revenue as revenue, prof.cost as cost,
               prof.margin as margin
        LIMIT 5
    ''')
    print('\nPROFITABILITY:')
    for r in result:
        margin_pct = r["margin"] * 100 if r["margin"] else 0
        print(f'  - {r["product"]}: Revenue ${r["revenue"]:,.0f}, Cost ${r["cost"]:,.0f}, Margin {margin_pct:.1f}%')
    
    # Key Relationships
    result = session.run('''
        MATCH ()-[r]->()
        WHERE type(r) IN ['HAS_RISK', 'SUPPORTS', 'RESPONSIBLE_FOR', 'HAS_ROADMAP', 
                          'AT_RISK', 'HAS_PROFITABILITY', 'HAS_SLA', 'HAS_COMMITMENT']
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
    ''')
    print('\nKEY RELATIONSHIPS:')
    for r in result:
        print(f'  - {r["rel_type"]}: {r["count"]} instances')

driver.close()