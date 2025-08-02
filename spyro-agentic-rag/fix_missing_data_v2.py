#!/usr/bin/env python3
"""Add missing data structures to Neo4j - Fixed for LlamaIndex schema"""
from neo4j import GraphDatabase
import os
from datetime import datetime, timedelta

# Get Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def run_query(query):
    """Run a Cypher query"""
    with driver.session() as session:
        result = session.run(query)
        return list(result)

def link_risks_to_objectives():
    """Create relationships between risks and objectives"""
    print("Linking risks to objectives...")
    
    # Market Expansion risks
    run_query("""
        MATCH (r) WHERE ('Risk' IN labels(r) OR ('__Entity__' IN labels(r) AND 'RISK' IN labels(r)))
        AND r.name IN ['Seasonal Risk', 'Competition Risk', 'Integration Risk']
        MATCH (o:Objective {name: 'Market Expansion'})
        MERGE (r)-[:AFFECTS]->(o)
    """)
    
    # Customer Retention risks  
    run_query("""
        MATCH (r) WHERE ('Risk' IN labels(r) OR ('__Entity__' IN labels(r) AND 'RISK' IN labels(r)))
        AND r.name IN ['Churn Risk', 'Customer Dissatisfaction Risk', 'SLA Breach Risk']
        MATCH (o:Objective {name: 'Customer Retention'})
        MERGE (r)-[:AFFECTS]->(o)
    """)
    
    # Product Innovation risks
    run_query("""
        MATCH (r) WHERE ('Risk' IN labels(r) OR ('__Entity__' IN labels(r) AND 'RISK' IN labels(r)))
        AND r.name IN ['Technology Risk', 'Roadmap Delay Risk', 'Integration Risk']
        MATCH (o:Objective {name: 'Product Innovation'})
        MERGE (r)-[:AFFECTS]->(o)
    """)
    
    # Revenue Growth risks
    run_query("""
        MATCH (r) WHERE ('Risk' IN labels(r) OR ('__Entity__' IN labels(r) AND 'RISK' IN labels(r)))
        AND r.severity IN ['HIGH', 'CRITICAL', 'High', 'Critical']
        MATCH (o:Objective {name: 'Revenue Growth'})
        MERGE (r)-[:AFFECTS]->(o)
    """)
    
    print("Risk-objective relationships created")

def add_feature_promises():
    """Add customer promises for features"""
    print("Adding feature promises to customers...")
    
    # Create promised features with proper labels
    promises = [
        ("TechCorp", "Enhanced Security Module", "2024-Q1", "DELIVERED"),
        ("TechCorp", "Multi-region deployment", "2024-Q2", "IN_PROGRESS"),
        ("FinanceHub", "Real-time fraud detection", "2024-Q1", "AT_RISK"),
        ("FinanceHub", "Advanced compliance reporting", "2024-Q2", "ON_TRACK"),
        ("HealthNet", "HIPAA compliance module", "2024-Q1", "DELIVERED"),
        ("HealthNet", "Data residency controls", "2024-Q2", "IN_PROGRESS"),
        ("RetailPlus", "API v3 with better performance", "2024-Q3", "ON_TRACK"),
        ("EduTech", "Student analytics dashboard", "2024-Q1", "DELAYED"),
        ("EduTech", "Mobile app support", "2024-Q2", "AT_RISK")
    ]
    
    for customer, feature, delivery_date, status in promises:
        # Match customer with LlamaIndex format
        run_query(f"""
            MATCH (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
            AND c.name = '{customer}'
            MERGE (f:__Entity__:__Node__:FEATURE {{name: '{feature}'}})
            SET f.delivery_status = '{status}',
                f.promised_delivery = '{delivery_date}',
                f.updated_at = datetime()
            MERGE (c)-[:PROMISED_FEATURE {{
                date_promised: date('2023-10-01'),
                delivery_date: '{delivery_date}',
                status: '{status}'
            }}]->(f)
        """)
    
    print(f"Added {len(promises)} feature promises")

def add_roadmap_relationships():
    """Link roadmap items to teams and features"""
    print("Adding roadmap relationships...")
    
    roadmap_teams = [
        ("Enhanced Security Module", "Security Team"),
        ("Multi-region deployment", "Infrastructure Team"),
        ("Real-time fraud detection", "AI Research Team"),
        ("Advanced compliance reporting", "Backend Team"),
        ("HIPAA compliance module", "Security Team"),
        ("Data residency controls", "Infrastructure Team"),
        ("API v3 performance improvements", "Backend Team"),
        ("Student analytics dashboard", "Frontend Team"),
        ("Mobile app support", "Mobile Team")
    ]
    
    for roadmap_item, team in roadmap_teams:
        # Link to teams (using LlamaIndex format)
        run_query(f"""
            MATCH (r:RoadmapItem {{name: '{roadmap_item}'}})
            MATCH (t) WHERE ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t))
            AND t.name = '{team}'
            MERGE (t)-[:RESPONSIBLE_FOR]->(r)
        """)
        
        # Link to features (using LlamaIndex format)
        run_query(f"""
            MATCH (r:RoadmapItem {{name: '{roadmap_item}'}})
            MATCH (f) WHERE ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
            AND f.name = '{roadmap_item}'
            MERGE (r)-[:IMPLEMENTS]->(f)
        """)
    
    print(f"Added roadmap relationships")

def add_feature_adoption_metrics():
    """Add adoption metrics for features"""
    print("Adding feature adoption metrics...")
    
    # Add adoption data for recently released features
    features_adoption = [
        ("Enhanced Security Module", 85.5, 450, "6 months ago"),
        ("Zero-trust network architecture", 72.3, 380, "4 months ago"),
        ("custom threat detection rules", 68.9, 320, "5 months ago"),
        ("Real-time monitoring", 91.2, 520, "3 months ago"),
        ("Automated compliance reporting", 78.6, 410, "5 months ago"),
        ("mobile API", 45.2, 280, "2 months ago")
    ]
    
    for feature, adoption_rate, active_users, released in features_adoption:
        run_query(f"""
            MATCH (f) WHERE ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
            AND f.name = '{feature}'
            SET f.adoption_rate = {adoption_rate},
                f.active_users = {active_users},
                f.released_timeframe = '{released}',
                f.is_new_feature = true
        """)
    
    print(f"Added adoption metrics for {len(features_adoption)} features")

def add_customer_concerns_actions():
    """Add actions being taken for customer concerns"""
    print("Adding actions for customer concerns...")
    
    # Check if concerns exist and add actions
    concerns_query = """
        MATCH (c)-[:HAS_CONCERN]->(concern)
        WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
        RETURN c.name as customer, concern.description as description
    """
    
    concerns = run_query(concerns_query)
    
    if concerns:
        actions = {
            "Complex integration": "Dedicated integration team assigned, creating custom middleware solution",
            "Peak load performance": "Infrastructure upgrade in progress, implementing auto-scaling",
            "SLA breach": "Emergency response team activated, 24/7 monitoring implemented",
            "Low success score": "Customer success manager assigned, weekly check-ins scheduled",
            "Data residency": "Implementing geo-fenced data storage, compliance audit scheduled",
            "Missing critical features": "Fast-track development initiated, features prioritized in current sprint"
        }
        
        for concern in concerns:
            for key, action in actions.items():
                if key.lower() in concern['description'].lower():
                    run_query(f"""
                        MATCH (c)-[:HAS_CONCERN]->(concern)
                        WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
                        AND c.name = '{concern['customer']}'
                        AND concern.description CONTAINS '{key[:20]}'
                        SET concern.action_taken = '{action}',
                            concern.action_status = 'IN_PROGRESS',
                            concern.action_updated = datetime()
                    """)
                    break
    
    print(f"Added actions for customer concerns")

def main():
    """Run all data fixes"""
    print("Fixing missing data structures (LlamaIndex format)...")
    print("=" * 80)
    
    link_risks_to_objectives()
    add_feature_promises()
    add_roadmap_relationships()
    add_feature_adoption_metrics()
    add_customer_concerns_actions()
    
    print("\nData fixes completed!")

if __name__ == "__main__":
    main()
    driver.close()