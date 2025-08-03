#!/usr/bin/env python3
"""Investigate Neo4j data for all 18 failed queries"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from neo4j import GraphDatabase

# Failed queries to investigate
FAILED_QUERIES = [
    {
        "id": 7,
        "question": "What are the projected quarterly revenue trends for the next fiscal year?",
        "issue": "No projections data"
    },
    {
        "id": 12,
        "question": "What is the average time to resolve critical customer issues by product?",
        "issue": "No resolution dates"
    },
    {
        "id": 19,
        "question": "What is the correlation between team size and project completion rates?",
        "issue": "No project completion data"
    },
    {
        "id": 20,
        "question": "How many critical milestones are at risk of being missed this quarter?",
        "issue": "No milestone data"
    },
    {
        "id": 25,
        "question": "What percentage of projects are currently over budget?",
        "issue": "No project budget data"
    },
    {
        "id": 26,
        "question": "Which teams have the highest employee satisfaction scores?",
        "issue": "No employee satisfaction data"
    },
    {
        "id": 28,
        "question": "How many security incidents have been reported in the last quarter?",
        "issue": "No security incident data"
    },
    {
        "id": 31,
        "question": "What is the average time from lead to customer conversion?",
        "issue": "No lead entities or conversion data"
    },
    {
        "id": 32,
        "question": "How many customers are using deprecated features?",
        "issue": "No deprecated feature indicators"
    },
    {
        "id": 34,
        "question": "Which SLAs are most frequently violated?",
        "issue": "No SLA entities"
    },
    {
        "id": 39,
        "question": "What is the average revenue per employee across different departments?",
        "issue": "No employee count data"
    },
    {
        "id": 43,
        "question": "What is the trend in customer acquisition costs over time?",
        "issue": "No time-series cost data"
    },
    {
        "id": 44,
        "question": "How many high-value opportunities are in the pipeline?",
        "issue": "No pipeline/opportunity entities"
    },
    {
        "id": 48,
        "question": "How many days of runway do we have at current burn rate?",
        "issue": "No cash/reserves data"
    },
    {
        "id": 51,
        "question": "How many critical dependencies exist in our technology stack?",
        "issue": "Unclear what constitutes 'critical dependencies'"
    },
    {
        "id": 52,
        "question": "What percentage of revenue is recurring vs one-time?",
        "issue": "Division by zero - no revenue categorization"
    },
    {
        "id": 53,
        "question": "Which marketing channels have the highest ROI?",
        "issue": "No MARKETING_CHANNEL entities"
    },
    {
        "id": 58,
        "question": "What percentage of our codebase has technical debt?",
        "issue": "No codebase or technical debt metrics"
    }
]

def investigate_query(driver, query_info):
    """Investigate a specific failed query"""
    print(f"\n{'='*80}")
    print(f"Query {query_info['id']}: {query_info['question']}")
    print(f"Known Issue: {query_info['issue']}")
    print("-" * 80)
    
    with driver.session() as session:
        # Investigate based on query ID
        if query_info['id'] == 7:  # Revenue projections
            result = session.run("""
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE prop CONTAINS 'project' OR prop CONTAINS 'forecast' OR prop CONTAINS 'quarter')
                RETURN labels(n) as labels, keys(n) as properties
                LIMIT 10
            """).data()
            print("Nodes with projection-related properties:", len(result))
            for r in result[:3]:
                print(f"  {r}")
                
        elif query_info['id'] == 12:  # Issue resolution time
            result = session.run("""
                MATCH (e:EVENT)
                WHERE e.type = 'support_escalation'
                RETURN e.date, keys(e) as properties
                LIMIT 5
            """).data()
            print("Support escalation events:", len(result))
            for r in result:
                print(f"  Properties: {r['properties']}")
            
            # Check for resolution relationships
            result = session.run("""
                MATCH (e:EVENT)-[r]->(n)
                WHERE e.type = 'support_escalation'
                RETURN type(r) as rel_type, labels(n) as target_labels
                LIMIT 5
            """).data()
            print("Resolution relationships:", len(result))
            
        elif query_info['id'] == 19:  # Team size vs project completion
            result = session.run("""
                MATCH (t:TEAM)
                RETURN t.name, keys(t) as properties
            """).data()
            print("Team properties:")
            for r in result[:3]:
                print(f"  {r['name']}: {r['properties']}")
                
            # Check for project relationships
            result = session.run("""
                MATCH (t:TEAM)-[r]-(p)
                WHERE 'PROJECT' IN labels(p) OR p.name CONTAINS 'project'
                RETURN t.name, type(r), labels(p)
                LIMIT 5
            """).data()
            print("Team-Project relationships:", len(result))
            
        elif query_info['id'] == 20:  # Critical milestones
            result = session.run("""
                MATCH (n)
                WHERE 'MILESTONE' IN labels(n) OR 
                      'ROADMAPITEM' IN labels(n) OR
                      any(prop IN keys(n) WHERE prop CONTAINS 'milestone')
                RETURN labels(n), keys(n)
                LIMIT 5
            """).data()
            print("Milestone-related nodes:", len(result))
            
        elif query_info['id'] == 25:  # Projects over budget
            result = session.run("""
                MATCH (n:PROJECT)
                RETURN count(n) as project_count, keys(n) as sample_keys
                LIMIT 1
            """).data()
            print("PROJECT nodes:", result)
            
        elif query_info['id'] == 26:  # Employee satisfaction
            result = session.run("""
                MATCH (n)
                WHERE 'EMPLOYEE' IN labels(n) OR 
                      any(prop IN keys(n) WHERE prop CONTAINS 'satisfaction' OR prop CONTAINS 'employee')
                RETURN labels(n), keys(n)
                LIMIT 5
            """).data()
            print("Employee-related nodes:", len(result))
            
        elif query_info['id'] == 28:  # Security incidents
            result = session.run("""
                MATCH (e:EVENT)
                WHERE e.type CONTAINS 'security' OR e.type CONTAINS 'incident'
                RETURN e.type, count(*) as count
            """).data()
            print("Security-related events:", result)
            
        elif query_info['id'] == 31:  # Lead conversion
            result = session.run("""
                MATCH (n)
                WHERE 'LEAD' IN labels(n)
                RETURN count(n) as lead_count
            """).data()
            print("LEAD nodes:", result)
            
            # Check for conversion relationships
            result = session.run("""
                MATCH ()-[r]->()
                WHERE type(r) CONTAINS 'CONVERT'
                RETURN type(r), count(*) as count
            """).data()
            print("Conversion relationships:", result)
            
        elif query_info['id'] == 32:  # Deprecated features
            result = session.run("""
                MATCH (f:FEATURE)
                RETURN keys(f) as properties
                LIMIT 5
            """).data()
            print("Feature properties:")
            for r in result:
                print(f"  {r['properties']}")
                
        elif query_info['id'] == 34:  # SLA violations
            result = session.run("""
                MATCH (n)
                WHERE 'SLA' IN labels(n)
                RETURN count(n) as sla_count
            """).data()
            print("SLA nodes:", result)
            
            # Check events for SLA violations
            result = session.run("""
                MATCH (e:EVENT)
                WHERE e.type CONTAINS 'sla' OR e.type CONTAINS 'violation'
                RETURN e.type, count(*) as count
            """).data()
            print("SLA-related events:", result)
            
        elif query_info['id'] == 39:  # Revenue per employee
            result = session.run("""
                MATCH (t:TEAM)
                WHERE exists(t.employee_count) OR exists(t.headcount) OR exists(t.size)
                RETURN t.name, keys(t)
            """).data()
            print("Teams with employee count data:", len(result))
            
        elif query_info['id'] == 43:  # Acquisition cost trends
            result = session.run("""
                MATCH (c:COST)
                WHERE c.category CONTAINS 'acquisition' OR c.category CONTAINS 'customer'
                RETURN c.category, c.period, count(*) as count
                ORDER BY c.period
            """).data()
            print("Acquisition cost data with periods:", len(result))
            
        elif query_info['id'] == 44:  # Pipeline opportunities
            result = session.run("""
                MATCH (n)
                WHERE 'OPPORTUNITY' IN labels(n) OR 'PIPELINE' IN labels(n)
                RETURN labels(n), count(*) as count
            """).data()
            print("Opportunity/Pipeline nodes:", result)
            
        elif query_info['id'] == 48:  # Runway calculation
            result = session.run("""
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE prop CONTAINS 'cash' OR prop CONTAINS 'reserve' OR prop CONTAINS 'balance')
                RETURN labels(n), keys(n)
                LIMIT 5
            """).data()
            print("Cash/Reserve nodes:", len(result))
            
            # Check team costs
            result = session.run("""
                MATCH (t:TEAM)
                WHERE exists(t.monthly_cost) OR exists(t.operational_cost)
                RETURN sum(coalesce(t.monthly_cost, 0) + coalesce(t.operational_cost, 0)) as total_monthly_burn
            """).data()
            print("Total monthly burn from teams:", result)
            
        elif query_info['id'] == 51:  # Critical dependencies
            result = session.run("""
                MATCH (f:FEATURE)
                WHERE f.adoption_rate IS NOT NULL
                RETURN count(f) as feature_count
            """).data()
            print("Features with adoption rate (used as dependencies):", result)
            
        elif query_info['id'] == 52:  # Recurring vs one-time revenue
            result = session.run("""
                MATCH (r:REVENUE)
                RETURN r.source, count(*) as count, keys(r) as sample_keys
            """).data()
            print("Revenue nodes by source:", result)
            
        elif query_info['id'] == 53:  # Marketing channels
            result = session.run("""
                MATCH (n)
                WHERE 'MARKETING_CHANNEL' IN labels(n) OR 
                      'MARKETING' IN labels(n) OR
                      any(prop IN keys(n) WHERE prop CONTAINS 'channel')
                RETURN labels(n), count(*) as count
            """).data()
            print("Marketing-related nodes:", result)
            
        elif query_info['id'] == 58:  # Technical debt
            result = session.run("""
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE prop CONTAINS 'debt' OR prop CONTAINS 'code' OR prop CONTAINS 'technical')
                RETURN labels(n), keys(n)
                LIMIT 5
            """).data()
            print("Technical debt related nodes:", len(result))

def main():
    config = Config.from_env()
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_username, config.neo4j_password)
    )
    
    print("INVESTIGATION OF FAILED QUERIES IN NEO4J")
    print("=" * 80)
    
    # First, get overview of what's in the database
    with driver.session() as session:
        # Get all labels
        labels = session.run("CALL db.labels()").data()
        print("\nALL LABELS IN DATABASE:")
        for label in labels:
            print(f"  - {label['label']}")
        
        # Get all relationship types
        rels = session.run("CALL db.relationshipTypes()").data()
        print("\nALL RELATIONSHIP TYPES:")
        for rel in rels:
            print(f"  - {rel['relationshipType']}")
        
        # Count nodes with date properties
        result = session.run("""
            MATCH (n)
            WHERE any(key IN keys(n) WHERE key CONTAINS 'date' OR key CONTAINS 'time' OR key CONTAINS 'period')
            RETURN count(n) as count, collect(DISTINCT keys(n))[..5] as sample_keys
        """).data()
        print(f"\nNodes with date/time properties: {result[0]['count']}")
        print(f"Sample properties: {result[0]['sample_keys']}")
    
    # Investigate each failed query
    for query_info in FAILED_QUERIES:
        investigate_query(driver, query_info)
    
    driver.close()
    
    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")

if __name__ == "__main__":
    main()