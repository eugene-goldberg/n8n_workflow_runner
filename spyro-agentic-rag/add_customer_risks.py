#!/usr/bin/env python3
"""Add risk profiles to customers"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def add_customer_risks():
    """Add risk profiles to top customers"""
    with driver.session() as session:
        print("Adding risk profiles to customers...")
        
        # Add risks to TechCorp
        session.run("""
            MATCH (tc) WHERE ('Customer' IN labels(tc) OR ('__Entity__' IN labels(tc) AND 'CUSTOMER' IN labels(tc)))
            AND toLower(tc.name) = 'techcorp'
            CREATE (tc)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Integration',
                severity: 'Medium',
                description: 'Complex integration requirements with legacy systems',
                probability: 0.4,
                impact: 'Service delays'
            })
            CREATE (tc)-[:HAS_RISK]->(r2:__Entity__:__Node__:RISK {
                type: 'Performance',
                severity: 'High',
                description: 'Peak load performance issues affecting user experience',
                probability: 0.6,
                impact: 'SLA violations'
            })
        """)
        
        # Add risks to GlobalRetail
        session.run("""
            MATCH (gr) WHERE ('Customer' IN labels(gr) OR ('__Entity__' IN labels(gr) AND 'CUSTOMER' IN labels(gr)))
            AND (gr.name = 'GlobalRetail' OR gr.name = 'Global Retail')
            CREATE (gr)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Seasonal',
                severity: 'Medium',
                description: 'High dependency on holiday season traffic',
                probability: 0.3,
                impact: 'Revenue volatility'
            })
        """)
        
        # Add risks to AutoDrive
        session.run("""
            MATCH (ad) WHERE ('Customer' IN labels(ad) OR ('__Entity__' IN labels(ad) AND 'CUSTOMER' IN labels(ad)))
            AND ad.name = 'AutoDrive'
            CREATE (ad)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Compliance',
                severity: 'High',
                description: 'New automotive industry regulations pending',
                probability: 0.5,
                impact: 'Feature restrictions'
            })
        """)
        
        # Add risks to CloudFirst
        session.run("""
            MATCH (cf) WHERE ('Customer' IN labels(cf) OR ('__Entity__' IN labels(cf) AND 'CUSTOMER' IN labels(cf)))
            AND cf.name = 'CloudFirst'
            CREATE (cf)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Competition',
                severity: 'Medium',
                description: 'Evaluating competitor offerings',
                probability: 0.35,
                impact: 'Contract renewal risk'
            })
        """)
        
        # Add risks to EnergyCore
        session.run("""
            MATCH (ec) WHERE ('Customer' IN labels(ec) OR ('__Entity__' IN labels(ec) AND 'CUSTOMER' IN labels(ec)))
            AND ec.name = 'EnergyCore'
            CREATE (ec)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Budget',
                severity: 'Low',
                description: 'Budget constraints for next fiscal year',
                probability: 0.25,
                impact: 'Limited expansion'
            })
        """)
        
        # Add risks to HealthNet
        session.run("""
            MATCH (hn) WHERE ('Customer' IN labels(hn) OR ('__Entity__' IN labels(hn) AND 'CUSTOMER' IN labels(hn)))
            AND hn.name = 'HealthNet'
            CREATE (hn)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Security',
                severity: 'High',
                description: 'HIPAA compliance requirements',
                probability: 0.7,
                impact: 'Additional security features needed'
            })
            CREATE (hn)-[:HAS_RISK]->(r2:__Entity__:__Node__:RISK {
                type: 'Data Privacy',
                severity: 'Critical',
                description: 'Strict data residency requirements',
                probability: 0.8,
                impact: 'Architecture changes required'
            })
        """)
        
        # Add risks to FinTech Pro
        session.run("""
            MATCH (fp) WHERE ('Customer' IN labels(fp) OR ('__Entity__' IN labels(fp) AND 'CUSTOMER' IN labels(fp)))
            AND (fp.name = 'FinTech Pro' OR fp.name = 'FinTech Solutions')
            CREATE (fp)-[:HAS_RISK]->(r1:__Entity__:__Node__:RISK {
                type: 'Regulatory',
                severity: 'High',
                description: 'Financial services compliance requirements',
                probability: 0.6,
                impact: 'Feature limitations'
            })
        """)
        
        print("✅ Risk profiles added to all major customers!")

if __name__ == "__main__":
    try:
        add_customer_risks()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()