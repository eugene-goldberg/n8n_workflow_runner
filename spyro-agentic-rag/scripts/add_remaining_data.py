#!/usr/bin/env python3
"""
Add only the remaining missing data to Neo4j
"""

import os
from neo4j import GraphDatabase

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def add_executive_sponsors():
    """Add executive sponsor data for Q58"""
    print("Adding executive sponsors...")
    
    with driver.session() as session:
        # High-value customers get executive sponsors
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
        WITH c, SUM(CASE 
            WHEN s.value CONTAINS 'M' THEN toFloat(replace(s.value, '$', '')) * 1000000
            WHEN s.value CONTAINS 'K' THEN toFloat(replace(s.value, '$', '')) * 1000
            ELSE toFloat(replace(replace(s.value, '$', ''), ',', ''))
        END) AS total_value
        WHERE total_value > 500000  // Customers with >$500K ARR
        CREATE (es:__Entity__:EXECUTIVE_SPONSOR {
            name: CASE toInteger(rand() * 5)
                WHEN 0 THEN 'John Smith, VP Sales'
                WHEN 1 THEN 'Sarah Johnson, CTO'
                WHEN 2 THEN 'Michael Chen, CEO'
                WHEN 3 THEN 'Lisa Williams, VP Customer Success'
                ELSE 'David Brown, VP Operations'
            END,
            role: CASE toInteger(rand() * 3)
                WHEN 0 THEN 'Executive Champion'
                WHEN 1 THEN 'Technical Sponsor'
                ELSE 'Business Sponsor'
            END,
            engagement_level: CASE 
                WHEN total_value > 1000000 THEN 'high'
                WHEN total_value > 750000 THEN 'medium'
                ELSE 'low'
            END
        })
        MERGE (c)-[:HAS_EXECUTIVE_SPONSOR]->(es)
        """)
        
        count = session.run("MATCH (es:__Entity__:EXECUTIVE_SPONSOR) RETURN COUNT(es) as count").single()['count']
        print(f"✓ Executive sponsors added: {count}")

def add_project_priorities():
    """Add project priority data for Q37"""
    print("Adding project priorities...")
    
    with driver.session() as session:
        # Add priorities to existing projects
        session.run("""
        MATCH (p:__Entity__:PROJECT)
        WHERE p.priority IS NULL
        WITH p, toInteger(rand() * 100) as priority_score
        SET p.priority = CASE 
            WHEN priority_score <= 20 THEN 'critical'
            WHEN priority_score <= 45 THEN 'high'
            WHEN priority_score <= 75 THEN 'medium'
            ELSE 'low'
        END
        """)
        
        # Create some additional projects with priorities
        session.run("""
        MERGE (p1:__Entity__:PROJECT {name: 'Security Audit'})
        SET p1.priority = 'critical', p1.status = 'in_progress'
        
        MERGE (p2:__Entity__:PROJECT {name: 'Data Migration'})
        SET p2.priority = 'high', p2.status = 'planning'
        
        MERGE (p3:__Entity__:PROJECT {name: 'API v3'})
        SET p3.priority = 'high', p3.status = 'in_progress'
        
        MERGE (p4:__Entity__:PROJECT {name: 'UI Redesign'})
        SET p4.priority = 'medium', p4.status = 'planning'
        
        MERGE (p5:__Entity__:PROJECT {name: 'Mobile App'})
        SET p5.priority = 'low', p5.status = 'completed'
        """)
        
        count = session.run("MATCH (p:__Entity__:PROJECT) WHERE p.priority IS NOT NULL RETURN COUNT(p) as count").single()['count']
        print(f"✓ Projects with priorities: {count}")

def add_external_dependencies():
    """Add external vendor dependencies for Q44, Q57"""
    print("Adding external vendor dependencies...")
    
    with driver.session() as session:
        # Create external dependencies
        session.run("""
        CREATE (ed1:__Entity__:EXTERNAL_DEPENDENCY {
            name: 'AWS Infrastructure',
            type: 'cloud_provider',
            criticality: 'critical',
            status: 'active',
            vendor: 'AWS'
        })
        
        CREATE (ed2:__Entity__:EXTERNAL_DEPENDENCY {
            name: 'Stripe Payment Processing',
            type: 'payment_provider',
            criticality: 'critical',
            status: 'active',
            vendor: 'Stripe'
        })
        
        CREATE (ed3:__Entity__:EXTERNAL_DEPENDENCY {
            name: 'SendGrid Email Service',
            type: 'email_provider',
            criticality: 'high',
            status: 'active',
            vendor: 'SendGrid'
        })
        
        CREATE (ed4:__Entity__:EXTERNAL_DEPENDENCY {
            name: 'Twilio SMS Gateway',
            type: 'sms_provider',
            criticality: 'medium',
            status: 'active',
            vendor: 'Twilio'
        })
        
        CREATE (ed5:__Entity__:EXTERNAL_DEPENDENCY {
            name: 'Salesforce Integration',
            type: 'crm_provider',
            criticality: 'high',
            status: 'active',
            vendor: 'Salesforce'
        })
        """)
        
        # Link some objectives to external dependencies
        session.run("""
        MATCH (o:__Entity__:OBJECTIVE)
        WHERE o.name CONTAINS 'scale' OR o.name CONTAINS 'expand' OR o.name CONTAINS 'integration'
        WITH o LIMIT 3
        MATCH (ed:__Entity__:EXTERNAL_DEPENDENCY)
        WHERE ed.criticality = 'critical'
        WITH o, ed LIMIT 5
        MERGE (o)-[:DEPENDS_ON]->(ed)
        """)
        
        # Create risks for blocked objectives
        session.run("""
        MATCH (o:__Entity__:OBJECTIVE)-[:DEPENDS_ON]->(ed:__Entity__:EXTERNAL_DEPENDENCY)
        WHERE ed.criticality = 'critical'
        CREATE (r:__Entity__:RISK {
            description: 'Blocked by ' + ed.name + ' dependency',
            category: 'dependency',
            status: 'active',
            impact_amount: 500000,
            mitigation_status: 'none'
        })
        MERGE (o)-[:BLOCKED_BY]->(r)
        """)
        
        count = session.run("MATCH (ed:__Entity__:EXTERNAL_DEPENDENCY) RETURN COUNT(ed) as count").single()['count']
        print(f"✓ External dependencies added: {count}")

def add_feature_release_dates():
    """Add feature release dates for Q34"""
    print("Adding feature release dates...")
    
    with driver.session() as session:
        # Add launch dates to features
        session.run("""
        MATCH (f:__Entity__:FEATURE)
        WHERE (f.status = 'launched' OR f.status = 'delivered') AND f.launch_date IS NULL
        SET f.launch_date = CASE 
            WHEN rand() < 0.3 THEN datetime() - duration('P30D')  // Last month
            WHEN rand() < 0.5 THEN datetime() - duration('P60D')  // 2 months ago
            WHEN rand() < 0.7 THEN datetime() - duration('P90D')  // Last quarter
            ELSE datetime() - duration('P180D')  // Older
        END
        """)
        
        # Mark recent features
        session.run("""
        MATCH (f:__Entity__:FEATURE)
        WHERE f.launch_date > datetime() - duration('P90D')
        SET f.is_recent = true, f.quarter_released = 'Q4 2024'
        """)
        
        count = session.run("MATCH (f:__Entity__:FEATURE) WHERE f.launch_date IS NOT NULL RETURN COUNT(f) as count").single()['count']
        print(f"✓ Features with launch dates: {count}")

def add_lifecycle_stages():
    """Add proper lifecycle stages for Q60"""
    print("Adding lifecycle stages...")
    
    with driver.session() as session:
        # First add created_date if missing
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)
        WHERE c.created_date IS NULL
        SET c.created_date = datetime() - duration('P' + toString(toInteger(rand() * 365)) + 'D')
        """)
        
        # Add lifecycle stages based on various factors
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)
        WHERE c.lifecycle_stage IS NULL
        OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(s:__Entity__:SUBSCRIPTION)
        WITH c, css.score as score, COUNT(s) as subscription_count
        SET c.lifecycle_stage = CASE
            WHEN c.created_date > datetime() - duration('P90D') THEN 'Onboarding'
            WHEN score < 50 THEN 'At Risk'
            WHEN score > 80 AND subscription_count > 1 THEN 'Expansion'
            WHEN score > 70 THEN 'Established'
            WHEN score >= 50 THEN 'Growing'
            ELSE 'Evaluation'
        END
        """)
        
        # Show distribution
        result = session.run("""
        MATCH (c:__Entity__:CUSTOMER)
        RETURN c.lifecycle_stage as stage, COUNT(c) as count
        ORDER BY count DESC
        """)
        
        print("✓ Lifecycle stages added:")
        for record in result:
            print(f"  - {record['stage']}: {record['count']} customers")

def add_more_support_data():
    """Enhance support ticket data for better correlation"""
    print("Enhancing support ticket data...")
    
    with driver.session() as session:
        # Update ticket counts based on customer health
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)-[:FILED_TICKET]->(st:__Entity__:SUPPORT_TICKET)
        WITH c, COUNT(st) as ticket_count
        SET c.support_ticket_count = ticket_count
        """)
        
        # Add segment support data
        result = session.run("""
        MATCH (c:__Entity__:CUSTOMER)-[:FILED_TICKET]->(st:__Entity__:SUPPORT_TICKET)
        WITH c.segment as segment, COUNT(st) as ticket_count
        RETURN segment, ticket_count
        ORDER BY ticket_count DESC
        """)
        
        print("✓ Support tickets by segment:")
        for record in result:
            print(f"  - {record['segment'] or 'Unknown'}: {record['ticket_count']} tickets")

def main():
    """Add all remaining missing data"""
    print("Adding remaining missing data to Neo4j...")
    print("=" * 50)
    
    try:
        add_executive_sponsors()
        add_project_priorities()
        add_external_dependencies()
        add_feature_release_dates()
        add_lifecycle_stages()
        add_more_support_data()
        
        print("\n✅ All remaining data added successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()

if __name__ == "__main__":
    main()