#!/usr/bin/env python3
"""
Add missing data to Neo4j to fix failing queries
"""

import os
from neo4j import GraphDatabase
from datetime import datetime, timedelta
import random

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def add_support_tickets():
    """Add support ticket data for Q20, Q35"""
    print("Adding support tickets...")
    
    with driver.session() as session:
        # Create SUPPORT_TICKET entities
        session.run("""
        // High-risk customers get more tickets
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < 60
        WITH c, css.score as score
        UNWIND range(1, CASE WHEN score < 40 THEN 5 ELSE 3 END) as ticket_num
        CREATE (st:__Entity__:SUPPORT_TICKET {
            id: c.name + '_ticket_' + ticket_num,
            customer_id: c.name,
            status: CASE WHEN rand() < 0.7 THEN 'resolved' ELSE 'open' END,
            priority: CASE 
                WHEN score < 40 THEN 'high'
                WHEN score < 50 THEN 'medium'
                ELSE 'low'
            END,
            created_date: datetime() - duration('P' + toString(toInteger(rand() * 90)) + 'D'),
            category: CASE toInteger(rand() * 4)
                WHEN 0 THEN 'technical'
                WHEN 1 THEN 'billing'
                WHEN 2 THEN 'feature_request'
                ELSE 'general'
            END
        })
        MERGE (c)-[:FILED_TICKET]->(st)
        """)
        
        # Add some tickets for medium-score customers
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score >= 60 AND css.score < 80
        WITH c, css.score as score
        WHERE rand() < 0.3  // 30% of medium customers have tickets
        CREATE (st:__Entity__:SUPPORT_TICKET {
            id: c.name + '_ticket_1',
            customer_id: c.name,
            status: 'resolved',
            priority: 'low',
            created_date: datetime() - duration('P' + toString(toInteger(rand() * 30)) + 'D'),
            category: 'general'
        })
        MERGE (c)-[:FILED_TICKET]->(st)
        """)
        
        print("✓ Support tickets added")

def add_integration_issues():
    """Add integration issue data for Q15, Q24"""
    print("Adding integration issues...")
    
    with driver.session() as session:
        # Create integration issues for customers with technical challenges
        session.run("""
        // Create integration issues for customers using multiple products
        MATCH (c:__Entity__:CUSTOMER)-[:USES]->(p:__Entity__:PRODUCT)
        WITH c, COUNT(DISTINCT p) as product_count
        WHERE product_count > 1
        UNWIND range(1, product_count - 1) as issue_num
        CREATE (ii:__Entity__:INTEGRATION_ISSUE {
            id: c.name + '_integration_' + issue_num,
            customer_id: c.name,
            status: CASE WHEN rand() < 0.6 THEN 'resolved' ELSE 'open' END,
            severity: CASE 
                WHEN rand() < 0.2 THEN 'critical'
                WHEN rand() < 0.5 THEN 'high'
                ELSE 'medium'
            END,
            description: CASE toInteger(rand() * 4)
                WHEN 0 THEN 'API compatibility issue'
                WHEN 1 THEN 'Data sync problem'
                WHEN 2 THEN 'Authentication conflict'
                ELSE 'Performance degradation'
            END,
            created_date: datetime() - duration('P' + toString(toInteger(rand() * 60)) + 'D')
        })
        MERGE (c)-[:HAS_INTEGRATION_ISSUE]->(ii)
        """)
        
        # Add some integration issues for low-score customers
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < 50
        CREATE (ii:__Entity__:INTEGRATION_ISSUE {
            id: c.name + '_integration_critical',
            customer_id: c.name,
            status: 'open',
            severity: 'critical',
            description: 'Major integration failure affecting core functionality',
            created_date: datetime() - duration('P7D')
        })
        MERGE (c)-[:HAS_INTEGRATION_ISSUE]->(ii)
        """)
        
        print("✓ Integration issues added")

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
        
        print("✓ Executive sponsors added")

def add_project_priorities():
    """Add project priority data for Q37"""
    print("Adding project priorities...")
    
    with driver.session() as session:
        # Add priorities to existing projects
        session.run("""
        MATCH (p:__Entity__:PROJECT)
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
        UNWIND ['Data Migration', 'Security Audit', 'UI Redesign', 'API v3', 'Mobile App'] as project_name
        CREATE (p:__Entity__:PROJECT {
            name: project_name,
            priority: CASE project_name
                WHEN 'Security Audit' THEN 'critical'
                WHEN 'Data Migration' THEN 'high'
                WHEN 'API v3' THEN 'high'
                WHEN 'UI Redesign' THEN 'medium'
                ELSE 'low'
            END,
            status: CASE toInteger(rand() * 3)
                WHEN 0 THEN 'planning'
                WHEN 1 THEN 'in_progress'
                ELSE 'completed'
            END,
            created_date: datetime() - duration('P' + toString(toInteger(rand() * 180)) + 'D')
        })
        """)
        
        print("✓ Project priorities added")

def add_external_dependencies():
    """Add external vendor dependencies for Q44, Q57"""
    print("Adding external vendor dependencies...")
    
    with driver.session() as session:
        # Create external dependencies
        external_deps = [
            ("AWS Infrastructure", "cloud_provider", "critical"),
            ("Stripe Payment Processing", "payment_provider", "critical"),
            ("SendGrid Email Service", "email_provider", "high"),
            ("Twilio SMS Gateway", "sms_provider", "medium"),
            ("Salesforce Integration", "crm_provider", "high")
        ]
        
        for dep_name, dep_type, criticality in external_deps:
            session.run("""
            CREATE (ed:__Entity__:EXTERNAL_DEPENDENCY {
                name: $name,
                type: $type,
                criticality: $criticality,
                status: 'active',
                vendor: SPLIT($name, ' ')[0]
            })
            """, name=dep_name, type=dep_type, criticality=criticality)
        
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
        
        print("✓ External dependencies added")

def add_feature_release_dates():
    """Add feature release dates for Q34"""
    print("Adding feature release dates...")
    
    with driver.session() as session:
        # Add launch dates to features
        session.run("""
        MATCH (f:__Entity__:FEATURE)
        WHERE f.status = 'launched' OR f.status = 'delivered'
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
        
        print("✓ Feature release dates added")

def add_lifecycle_stages():
    """Add proper lifecycle stages for Q60"""
    print("Adding lifecycle stages...")
    
    with driver.session() as session:
        # Add lifecycle stages based on various factors
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)
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
        
        print("✓ Lifecycle stages added")

def add_skill_gaps():
    """Add skill gap data for Q50"""
    print("Adding skill gaps...")
    
    with driver.session() as session:
        # Create required skills for teams
        skills = ['Cloud Architecture', 'Machine Learning', 'Security', 'DevOps', 'Data Engineering']
        
        session.run("""
        MATCH (t:__Entity__:TEAM)
        WHERE t.name IN ['AI Research Team', 'Security Team', 'Data Science Team']
        UNWIND $skills as skill_name
        CREATE (s:__Entity__:SKILL {
            name: skill_name,
            level_required: CASE 
                WHEN skill_name CONTAINS 'Security' AND t.name = 'Security Team' THEN 'expert'
                WHEN skill_name CONTAINS 'Machine Learning' AND t.name = 'AI Research Team' THEN 'expert'
                ELSE 'intermediate'
            END
        })
        MERGE (t)-[:REQUIRES_SKILL]->(s)
        """, skills=skills)
        
        # Mark some teams as having skill gaps
        session.run("""
        MATCH (t:__Entity__:TEAM)-[:REQUIRES_SKILL]->(rs:__Entity__:SKILL)
        WITH t, COUNT(rs) as required_count
        WHERE required_count > 2
        SET t.has_skill_gap = true, t.skill_gap_count = toInteger(required_count * 0.4)
        """)
        
        print("✓ Skill gaps added")

def main():
    """Add all missing data"""
    print("Adding missing data to Neo4j...")
    print("=" * 50)
    
    try:
        add_support_tickets()
        add_integration_issues()
        add_executive_sponsors()
        add_project_priorities()
        add_external_dependencies()
        add_feature_release_dates()
        add_lifecycle_stages()
        add_skill_gaps()
        
        print("\n✅ All missing data added successfully!")
        
        # Verify counts
        with driver.session() as session:
            counts = session.run("""
            MATCH (st:__Entity__:SUPPORT_TICKET) WITH COUNT(st) as support_tickets
            MATCH (ii:__Entity__:INTEGRATION_ISSUE) WITH support_tickets, COUNT(ii) as integration_issues
            MATCH (es:__Entity__:EXECUTIVE_SPONSOR) WITH support_tickets, integration_issues, COUNT(es) as executive_sponsors
            MATCH (ed:__Entity__:EXTERNAL_DEPENDENCY) WITH support_tickets, integration_issues, executive_sponsors, COUNT(ed) as external_deps
            MATCH (p:__Entity__:PROJECT) WHERE p.priority IS NOT NULL WITH support_tickets, integration_issues, executive_sponsors, external_deps, COUNT(p) as prioritized_projects
            MATCH (f:__Entity__:FEATURE) WHERE f.launch_date IS NOT NULL WITH support_tickets, integration_issues, executive_sponsors, external_deps, prioritized_projects, COUNT(f) as dated_features
            RETURN support_tickets, integration_issues, executive_sponsors, external_deps, prioritized_projects, dated_features
            """).single()
            
            print("\nData added:")
            print(f"- Support Tickets: {counts['support_tickets']}")
            print(f"- Integration Issues: {counts['integration_issues']}")
            print(f"- Executive Sponsors: {counts['executive_sponsors']}")
            print(f"- External Dependencies: {counts['external_deps']}")
            print(f"- Prioritized Projects: {counts['prioritized_projects']}")
            print(f"- Features with dates: {counts['dated_features']}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()