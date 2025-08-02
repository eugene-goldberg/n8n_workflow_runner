#!/usr/bin/env python3
"""Add missing data to Neo4j for complete business question answering"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def add_missing_data():
    """Add missing entities and relationships"""
    with driver.session() as session:
        print("Adding missing data to Neo4j...")
        
        # 1. Add customer concerns
        print("\n1. Adding customer concerns...")
        session.run("""
            // Top customer concerns
            CREATE (c1:__Entity__:__Node__:CONCERN {
                id: 'concern-1',
                type: 'Performance Issues',
                description: 'SpyroCloud API response times exceed 500ms during peak hours',
                priority: 'High',
                status: 'In Progress',
                created_date: datetime('2024-10-15')
            })
            CREATE (c2:__Entity__:__Node__:CONCERN {
                id: 'concern-2',
                type: 'Missing Features',
                description: 'Multi-region deployment capability not available',
                priority: 'Critical',
                status: 'Planned',
                created_date: datetime('2024-09-20')
            })
            CREATE (c3:__Entity__:__Node__:CONCERN {
                id: 'concern-3',
                type: 'Documentation',
                description: 'API documentation incomplete for SpyroAI endpoints',
                priority: 'Medium',
                status: 'In Progress',
                created_date: datetime('2024-11-01')
            })
            CREATE (c4:__Entity__:__Node__:CONCERN {
                id: 'concern-4',
                type: 'Security',
                description: 'Need SOC2 compliance certification for SpyroSecure',
                priority: 'High',
                status: 'Planned',
                created_date: datetime('2024-10-10')
            })
            CREATE (c5:__Entity__:__Node__:CONCERN {
                id: 'concern-5',
                type: 'Integration',
                description: 'Salesforce integration not working properly',
                priority: 'Medium',
                status: 'Investigating',
                created_date: datetime('2024-11-15')
            })
        """)
        
        # Link concerns to customers
        session.run("""
            MATCH (tc:__Entity__:CUSTOMER {name: 'TechCorp'})
            MATCH (c1:__Entity__:CONCERN {type: 'Performance Issues'})
            MATCH (c2:__Entity__:CONCERN {type: 'Missing Features'})
            CREATE (tc)-[:HAS_CONCERN]->(c1)
            CREATE (tc)-[:HAS_CONCERN]->(c2)
        """)
        
        session.run("""
            MATCH (fh:__Entity__:CUSTOMER {name: 'FinanceHub'})
            MATCH (c4:__Entity__:CONCERN {type: 'Security'})
            CREATE (fh)-[:HAS_CONCERN]->(c4)
        """)
        
        # 2. Add promised features
        print("2. Adding promised features...")
        session.run("""
            CREATE (f1:__Entity__:__Node__:FEATURE {
                id: 'feature-1',
                name: 'Multi-region Deployment',
                description: 'Deploy SpyroCloud across multiple AWS regions',
                status: 'In Development',
                expected_date: date('2025-03-15'),
                promised: true,
                commitment_date: date('2024-10-01')
            })
            CREATE (f2:__Entity__:__Node__:FEATURE {
                id: 'feature-2',
                name: 'AI-powered Analytics',
                description: 'Advanced analytics using SpyroAI ML models',
                status: 'Delivered',
                expected_date: date('2024-12-01'),
                actual_date: date('2024-11-28'),
                promised: true,
                commitment_date: date('2024-09-15')
            })
            CREATE (f3:__Entity__:__Node__:FEATURE {
                id: 'feature-3',
                name: 'Real-time Dashboards',
                description: 'Live metrics dashboard for all products',
                status: 'Testing',
                expected_date: date('2025-01-30'),
                promised: true,
                commitment_date: date('2024-11-01')
            })
            CREATE (f4:__Entity__:__Node__:FEATURE {
                id: 'feature-4',
                name: 'Enhanced API Rate Limits',
                description: 'Increase API rate limits for enterprise customers',
                status: 'Delayed',
                expected_date: date('2024-12-15'),
                promised: true,
                commitment_date: date('2024-08-01')
            })
        """)
        
        # Link features to waiting customers
        session.run("""
            MATCH (tc:__Entity__:CUSTOMER {name: 'TechCorp'})
            MATCH (gm:__Entity__:CUSTOMER {name: 'Global Manufacturing Corp'})
            MATCH (f1:__Entity__:FEATURE {name: 'Multi-region Deployment'})
            CREATE (tc)-[:WAITING_FOR]->(f1)
            CREATE (gm)-[:WAITING_FOR]->(f1)
        """)
        
        # 3. Add customer commitments
        print("3. Adding customer commitments...")
        session.run("""
            CREATE (cm1:__Entity__:__Node__:COMMITMENT {
                id: 'commitment-1',
                type: 'SLA Guarantee',
                description: '99.9% uptime for SpyroCloud services',
                target: '99.9%',
                current_performance: '99.7%',
                status: 'At Risk',
                risk_level: 'Medium'
            })
            CREATE (cm2:__Entity__:__Node__:COMMITMENT {
                id: 'commitment-2',
                type: 'Response Time',
                description: 'API response time under 200ms',
                target: '200ms',
                current_performance: '450ms',
                status: 'Not Met',
                risk_level: 'High'
            })
            CREATE (cm3:__Entity__:__Node__:COMMITMENT {
                id: 'commitment-3',
                type: 'Feature Delivery',
                description: 'Deliver all Q1 2025 roadmap items on time',
                target: '100%',
                current_performance: '60%',
                status: 'At Risk',
                risk_level: 'High'
            })
        """)
        
        # 4. Add operational cost data
        print("4. Adding operational costs...")
        session.run("""
            MATCH (sp:__Entity__:PRODUCT {name: 'SpyroCloud'})
            CREATE (sp)-[:HAS_COST]->(cost1:__Entity__:__Node__:COST {
                amount: 2500000,
                type: 'operational',
                region: 'US-East',
                period: 'annual'
            })
            CREATE (sp)-[:HAS_COST]->(cost2:__Entity__:__Node__:COST {
                amount: 1800000,
                type: 'operational',
                region: 'EU-West',
                period: 'annual'
            })
        """)
        
        session.run("""
            MATCH (sa:__Entity__:PRODUCT {name: 'SpyroAI'})
            CREATE (sa)-[:HAS_COST]->(cost3:__Entity__:__Node__:COST {
                amount: 3200000,
                type: 'operational',
                region: 'US-East',
                period: 'annual'
            })
        """)
        
        # 5. Update team costs
        print("5. Updating team operational costs...")
        session.run("""
            MATCH (t:__Entity__:TEAM)
            WHERE t.name = 'Platform Team'
            SET t.operational_cost = 2400000, t.cost = 2400000
        """)
        
        session.run("""
            MATCH (t:__Entity__:TEAM)
            WHERE t.name = 'Security Team'
            SET t.operational_cost = 1800000, t.cost = 1800000
        """)
        
        # 6. Add negative events for date-based queries
        print("6. Adding recent events...")
        recent_date = datetime.now() - timedelta(days=30)
        session.run("""
            CREATE (e1:__Entity__:__Node__:EVENT {
                id: 'event-1',
                type: 'Service Outage',
                description: 'SpyroCloud US-East region down for 2 hours',
                severity: 'Critical',
                date: $recent_date,
                impact: 'High'
            })
            CREATE (e2:__Entity__:__Node__:EVENT {
                id: 'event-2',
                type: 'Performance Degradation',
                description: 'API response times increased by 300%',
                severity: 'High',
                date: $recent_date2,
                impact: 'Medium'
            })
        """, recent_date=recent_date, recent_date2=recent_date - timedelta(days=15))
        
        # Link events to customers
        session.run("""
            MATCH (tc:__Entity__:CUSTOMER {name: 'TechCorp'})
            MATCH (e1:__Entity__:EVENT {type: 'Service Outage'})
            CREATE (tc)-[:EXPERIENCED]->(e1)
        """)
        
        # 7. Add SLA data
        print("7. Adding SLA information...")
        session.run("""
            MATCH (tc:__Entity__:CUSTOMER {name: 'TechCorp'})
            CREATE (tc)-[:HAS_SLA]->(sla:__Entity__:__Node__:SLA {
                type: 'Enterprise',
                uptime_target: '99.9%',
                response_time_target: '200ms',
                penalty_percentage: 15,
                credit_per_hour_downtime: 1000
            })
        """)
        
        # 8. Add risk profiles to customers
        print("8. Adding risk profiles...")
        session.run("""
            MATCH (gm:__Entity__:CUSTOMER {name: 'Global Manufacturing Corp'})
            CREATE (gm)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Contract Renewal',
                severity: 'High',
                description: 'Considering competitor solutions'
            })
            CREATE (gm)-[:HAS_RISK]->(r2:__Entity__:__Node__:RISK {
                type: 'Technical',
                severity: 'Medium',
                description: 'Integration challenges with legacy systems'
            })
        """)
        
        # 9. Add product satisfaction scores
        print("9. Adding product satisfaction scores...")
        session.run("""
            MATCH (sp:__Entity__:PRODUCT {name: 'SpyroCloud'})
            SET sp.satisfaction_score = 4.2, sp.nps_score = 42
        """)
        session.run("""
            MATCH (sa:__Entity__:PRODUCT {name: 'SpyroAI'})
            SET sa.satisfaction_score = 4.5, sa.nps_score = 58
        """)
        session.run("""
            MATCH (ss:__Entity__:PRODUCT {name: 'SpyroSecure'})
            SET ss.satisfaction_score = 4.7, ss.nps_score = 65
        """)
        
        # 10. Fix missing revenue data
        print("10. Fixing missing subscription relationships...")
        session.run("""
            // Ensure all customers have subscription relationships
            MATCH (c:__Entity__:CUSTOMER)
            WHERE NOT EXISTS((c)-[:SUBSCRIBES_TO]->())
            WITH c
            MATCH (sub:__Entity__:SUBSCRIPTION)
            WHERE sub.customer_name = c.name OR sub.customer = c.name
            CREATE (c)-[:SUBSCRIBES_TO]->(sub)
        """)
        
        print("\n✅ All missing data added successfully!")

if __name__ == "__main__":
    try:
        add_missing_data()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()