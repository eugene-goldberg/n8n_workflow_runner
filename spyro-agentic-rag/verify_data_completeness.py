#!/usr/bin/env python3
"""Verify all data structures needed for high success rate"""
from neo4j import GraphDatabase
import os

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'password123'))
)

print('=== DATA VERIFICATION FOR HIGH SUCCESS RATE ===\n')

missing_data = []

with driver.session() as session:
    # 1. Check operational costs
    result = session.run('''
        MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
        AND p.operational_cost IS NOT NULL
        RETURN count(p) as products_with_costs, collect(p.name)[..5] as sample_products
    ''')
    record = result.single()
    print(f'1. Products with operational costs: {record["products_with_costs"]}')
    print(f'   Sample: {record["sample_products"]}\n')
    if record["products_with_costs"] < 3:
        missing_data.append("Product operational costs")
    
    # 2. Check SLA data
    result = session.run('''
        MATCH (c)-[:HAS_SLA]->(sla)
        RETURN count(DISTINCT c) as customers_with_sla, collect(DISTINCT c.name)[..5] as sample_customers
    ''')
    record = result.single()
    print(f'2. Customers with SLA data: {record["customers_with_sla"]}')
    print(f'   Sample: {record["sample_customers"]}\n')
    if record["customers_with_sla"] == 0:
        missing_data.append("Customer SLA relationships")
    
    # 3. Check team attrition data
    result = session.run('''
        MATCH (t) WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
        AND t.attrition_rate IS NOT NULL
        RETURN count(t) as teams_with_attrition, max(t.attrition_rate) as max_attrition
    ''')
    record = result.single()
    print(f'3. Teams with attrition data: {record["teams_with_attrition"]} (max: {record["max_attrition"]})\n')
    if record["teams_with_attrition"] == 0:
        missing_data.append("Team attrition rates")
    
    # 4. Check feature launch data
    result = session.run('''
        MATCH (f) WHERE ('Feature' IN labels(f) OR ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f)))
        AND f.launch_date IS NOT NULL
        RETURN count(f) as features_with_launch_dates
    ''')
    record = result.single()
    print(f'4. Features with launch dates: {record["features_with_launch_dates"]}\n')
    if record["features_with_launch_dates"] == 0:
        missing_data.append("Feature launch dates")
    
    # 5. Check expansion opportunities
    result = session.run('''
        MATCH (c)-[:HAS_EXPANSION_OPPORTUNITY]->(e)
        RETURN count(DISTINCT c) as customers_with_expansion
    ''')
    record = result.single()
    print(f'5. Customers with expansion opportunities: {record["customers_with_expansion"]}\n')
    if record["customers_with_expansion"] == 0:
        missing_data.append("Customer expansion opportunities")
    
    # 6. Check contract lengths
    result = session.run('''
        MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
        AND (c.contract_length IS NOT NULL OR c.contract_end_date IS NOT NULL)
        RETURN count(c) as customers_with_contracts
    ''')
    record = result.single()
    print(f'6. Customers with contract data: {record["customers_with_contracts"]}\n')
    if record["customers_with_contracts"] == 0:
        missing_data.append("Customer contract lengths")
    
    # 7. Check usage growth data
    result = session.run('''
        MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
        AND (c.usage_growth IS NOT NULL OR c.usage_increase_percentage IS NOT NULL)
        RETURN count(c) as customers_with_usage_growth
    ''')
    record = result.single()
    print(f'7. Customers with usage growth data: {record["customers_with_usage_growth"]}\n')
    if record["customers_with_usage_growth"] == 0:
        missing_data.append("Customer usage growth metrics")
    
    # 8. Check POC data
    result = session.run('''
        MATCH (p:POC) RETURN count(p) as poc_count
    ''')
    record = result.single()
    print(f'8. POCs in system: {record["poc_count"]}\n')
    if record["poc_count"] == 0:
        missing_data.append("Proof of Concept records")
    
    # 9. Check support ticket data
    result = session.run('''
        MATCH (t:SupportTicket) RETURN count(t) as ticket_count
    ''')
    record = result.single()
    print(f'9. Support tickets: {record["ticket_count"]}\n')
    if record["ticket_count"] == 0:
        missing_data.append("Support ticket records")
    
    # 10. Check feature request data
    result = session.run('''
        MATCH (f:FeatureRequest) RETURN count(f) as request_count
    ''')
    record = result.single()
    print(f'10. Feature requests: {record["request_count"]}\n')
    if record["request_count"] == 0:
        missing_data.append("Feature request records")
    
    # 11. Check promised features
    result = session.run('''
        MATCH (c)-[:PROMISED_FEATURE]->(f)
        RETURN count(DISTINCT c) as customers_with_promises, count(f) as total_promises
    ''')
    record = result.single()
    print(f'11. Customers with feature promises: {record["customers_with_promises"]} ({record["total_promises"]} total)\n')
    
    # 12. Check roadmap items
    result = session.run('''
        MATCH (r:RoadmapItem) RETURN count(r) as roadmap_count
    ''')
    record = result.single()
    print(f'12. Roadmap items: {record["roadmap_count"]}\n')
    
    # 13. Check risk-objective relationships
    result = session.run('''
        MATCH (r)-[:AFFECTS]->(o:Objective)
        RETURN count(DISTINCT r) as risks_affecting_objectives
    ''')
    record = result.single()
    print(f'13. Risks affecting objectives: {record["risks_affecting_objectives"]}\n')
    
    # 14. Check customer subscription start dates
    result = session.run('''
        MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
        AND c.subscription_start_date IS NOT NULL
        RETURN count(c) as customers_with_start_dates
    ''')
    record = result.single()
    print(f'14. Customers with subscription start dates: {record["customers_with_start_dates"]}\n')
    if record["customers_with_start_dates"] == 0:
        missing_data.append("Customer subscription start dates")
    
    # 15. Check team-customer support relationships
    result = session.run('''
        MATCH (t)-[:SUPPORTS]->(c)
        WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
        AND ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
        RETURN count(DISTINCT t) as teams_supporting, count(DISTINCT c) as customers_supported
    ''')
    record = result.single()
    print(f'15. Team-customer support: {record["teams_supporting"]} teams supporting {record["customers_supported"]} customers\n')
    if record["teams_supporting"] == 0:
        missing_data.append("Team-customer support relationships")

driver.close()

print("\n=== MISSING DATA SUMMARY ===")
if missing_data:
    print(f"Missing {len(missing_data)} critical data structures:")
    for item in missing_data:
        print(f"  - {item}")
    print(f"\nEstimated impact: ~{len(missing_data) * 5}% reduction in success rate")
else:
    print("All critical data structures are present!")
    print("System should be capable of achieving 83%+ success rate")