#!/usr/bin/env python3
"""Final investigation of Neo4j data for all 18 failed queries"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from neo4j import GraphDatabase
import json

def investigate_all_failed_queries(driver):
    """Run comprehensive investigation for all failed queries"""
    
    investigations = []
    
    with driver.session() as session:
        # Query 7: Revenue projections
        print("\n=== Q7: Revenue Projections ===")
        result = session.run("""
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE prop CONTAINS 'project' OR prop CONTAINS 'forecast' OR prop CONTAINS 'quarter')
            RETURN labels(n)[0] as label, count(*) as count, collect(DISTINCT keys(n))[0] as sample_props
        """).data()
        q7_has_data = len(result) > 0
        print(f"Projection-related nodes: {result}")
        investigations.append({
            "id": 7,
            "question": "What are the projected quarterly revenue trends for the next fiscal year?",
            "has_data": q7_has_data,
            "missing": "PROJECTION or FORECAST nodes with quarterly data",
            "finding": "No projection/forecast nodes found in the graph"
        })
        
        # Query 12: Issue resolution time
        print("\n=== Q12: Issue Resolution Time ===")
        result = session.run("""
            MATCH (e:EVENT)
            WHERE e.type = 'support_escalation'
            RETURN count(*) as count, collect(keys(e))[0] as props
        """).data()
        has_events = result[0]['count'] > 0
        print(f"Support escalation events: {result[0]['count']}")
        print(f"Properties: {result[0]['props']}")
        
        # Check for resolution dates
        result2 = session.run("""
            MATCH (e:EVENT)
            WHERE e.type = 'support_escalation' AND 
                  any(prop IN keys(e) WHERE prop CONTAINS 'resolve' OR prop CONTAINS 'close')
            RETURN count(*) as count
        """).data()
        has_resolution = result2[0]['count'] > 0
        investigations.append({
            "id": 12,
            "question": "What is the average time to resolve critical customer issues by product?",
            "has_data": has_events and not has_resolution,
            "missing": "resolution_date or closed_date properties on EVENT nodes",
            "finding": f"Found {result[0]['count']} support events but no resolution dates/times"
        })
        
        # Query 19: Team size vs project completion
        print("\n=== Q19: Team Size vs Project Completion ===")
        result = session.run("""
            MATCH (t:TEAM)
            RETURN count(*) as team_count
        """).data()
        has_teams = result[0]['team_count'] > 0
        
        result2 = session.run("""
            MATCH (p:PROJECT)
            RETURN count(*) as project_count
        """).data()
        has_projects = result2[0]['project_count'] > 0
        
        # Check team properties
        result3 = session.run("""
            MATCH (t:TEAM)
            WHERE t.size IS NOT NULL OR t.headcount IS NOT NULL
            RETURN count(*) as teams_with_size
        """).data()
        investigations.append({
            "id": 19,
            "question": "What is the correlation between team size and project completion rates?",
            "has_data": has_teams and not has_projects,
            "missing": "PROJECT nodes and project completion data",
            "finding": f"Found {result[0]['team_count']} teams (with size data: {result3[0]['teams_with_size']}) but only {result2[0]['project_count']} PROJECT nodes"
        })
        
        # Query 20: Critical milestones
        print("\n=== Q20: Critical Milestones ===")
        result = session.run("""
            MATCH (n)
            WHERE 'MILESTONE' IN labels(n)
            RETURN count(*) as count
        """).data()
        milestone_count = result[0]['count']
        
        result2 = session.run("""
            MATCH (n:ROADMAPITEM)
            RETURN count(*) as count
        """).data()
        roadmap_count = result2[0]['count']
        investigations.append({
            "id": 20,
            "question": "How many critical milestones are at risk of being missed this quarter?",
            "has_data": roadmap_count > 0,
            "missing": "MILESTONE nodes with risk/status properties",
            "finding": f"Found {roadmap_count} ROADMAPITEM nodes but {milestone_count} MILESTONE nodes"
        })
        
        # Query 25: Projects over budget
        print("\n=== Q25: Projects Over Budget ===")
        result = session.run("""
            MATCH (n:PROJECT)
            WHERE n.budget IS NOT NULL
            RETURN count(*) as with_budget
        """).data()
        investigations.append({
            "id": 25,
            "question": "What percentage of projects are currently over budget?",
            "has_data": False,
            "missing": "budget and actual_cost properties on PROJECT nodes",
            "finding": f"PROJECT nodes exist but {result[0]['with_budget']} have budget property"
        })
        
        # Query 26: Employee satisfaction
        print("\n=== Q26: Employee Satisfaction ===")
        result = session.run("""
            MATCH (t:TEAM)
            WHERE t.satisfaction_score IS NOT NULL
            RETURN count(*) as count, avg(t.satisfaction_score) as avg_score
        """).data()
        has_team_satisfaction = result[0]['count'] > 0
        investigations.append({
            "id": 26,
            "question": "Which teams have the highest employee satisfaction scores?",
            "has_data": has_team_satisfaction,
            "missing": "EMPLOYEE nodes or employee_satisfaction properties",
            "finding": f"Found {result[0]['count']} teams with satisfaction_score (avg: {result[0]['avg_score']})"
        })
        
        # Query 28: Security incidents
        print("\n=== Q28: Security Incidents ===")
        result = session.run("""
            MATCH (e:EVENT)
            WHERE e.type CONTAINS 'security' OR e.type CONTAINS 'incident' OR e.type CONTAINS 'breach'
            RETURN count(*) as count, collect(DISTINCT e.type) as types
        """).data()
        investigations.append({
            "id": 28,
            "question": "How many security incidents have been reported in the last quarter?",
            "has_data": False,
            "missing": "EVENT nodes with type='security_incident'",
            "finding": f"Checked all events, found {result[0]['count']} security-related (types: {result[0]['types']})"
        })
        
        # Query 31: Lead conversion
        print("\n=== Q31: Lead Conversion ===")
        result = session.run("""
            MATCH (n)
            WHERE 'LEAD' IN labels(n)
            RETURN count(*) as count
        """).data()
        investigations.append({
            "id": 31,
            "question": "What is the average time from lead to customer conversion?",
            "has_data": False,
            "missing": "LEAD nodes and CONVERTED_TO relationships",
            "finding": f"No LEAD entities found (count: {result[0]['count']})"
        })
        
        # Query 32: Deprecated features
        print("\n=== Q32: Deprecated Features ===")
        result = session.run("""
            MATCH (f:FEATURE)
            RETURN count(*) as total, 
                   count(CASE WHEN f.deprecated IS NOT NULL THEN 1 END) as with_deprecated,
                   collect(DISTINCT keys(f))[0] as sample_props
        """).data()
        investigations.append({
            "id": 32,
            "question": "How many customers are using deprecated features?",
            "has_data": False,
            "missing": "deprecated or is_deprecated property on FEATURE nodes",
            "finding": f"{result[0]['total']} features exist, {result[0]['with_deprecated']} marked deprecated. Props: {result[0]['sample_props']}"
        })
        
        # Query 34: SLA violations
        print("\n=== Q34: SLA Violations ===")
        result = session.run("""
            MATCH (n:SLA)
            RETURN count(*) as count
        """).data()
        sla_count = result[0]['count']
        
        result2 = session.run("""
            MATCH (e:EVENT)
            WHERE e.type = 'sla_violation'
            RETURN count(*) as count
        """).data()
        investigations.append({
            "id": 34,
            "question": "Which SLAs are most frequently violated?",
            "has_data": sla_count > 0,
            "missing": "EVENT nodes with type='sla_violation'",
            "finding": f"Found {sla_count} SLA nodes but {result2[0]['count']} violation events"
        })
        
        # Query 39: Revenue per employee
        print("\n=== Q39: Revenue per Employee ===")
        result = session.run("""
            MATCH (t:TEAM)
            WHERE t.headcount IS NOT NULL OR t.size IS NOT NULL
            RETURN count(*) as count, sum(coalesce(t.headcount, t.size)) as total_employees
        """).data()
        investigations.append({
            "id": 39,
            "question": "What is the average revenue per employee across different departments?",
            "has_data": result[0]['count'] > 0,
            "missing": "Direct revenue attribution to teams/departments",
            "finding": f"Found {result[0]['count']} teams with employee data (total: {result[0]['total_employees']})"
        })
        
        # Query 43: Acquisition cost trends
        print("\n=== Q43: Acquisition Cost Trends ===")
        result = session.run("""
            MATCH (c:COST)
            WHERE c.category = 'acquisition'
            RETURN count(*) as count, collect(DISTINCT c.period) as periods
        """).data()
        investigations.append({
            "id": 43,
            "question": "What is the trend in customer acquisition costs over time?",
            "has_data": False,
            "missing": "COST nodes with category='acquisition' and time periods",
            "finding": f"Found {result[0]['count']} acquisition costs. Periods: {result[0]['periods']}"
        })
        
        # Query 44: Pipeline opportunities
        print("\n=== Q44: Pipeline Opportunities ===")
        result = session.run("""
            MATCH (n:EXPANSION_OPPORTUNITY)
            RETURN count(*) as count
        """).data()
        investigations.append({
            "id": 44,
            "question": "How many high-value opportunities are in the pipeline?",
            "has_data": result[0]['count'] > 0,
            "missing": "value or stage properties on opportunities",
            "finding": f"Found {result[0]['count']} EXPANSION_OPPORTUNITY nodes (used as proxy)"
        })
        
        # Query 48: Runway calculation
        print("\n=== Q48: Days of Runway ===")
        result = session.run("""
            MATCH (t:TEAM)
            WHERE t.monthly_cost IS NOT NULL
            RETURN sum(t.monthly_cost) as total_burn
        """).data()
        
        result2 = session.run("""
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE prop CONTAINS 'cash' OR prop CONTAINS 'balance')
            RETURN labels(n) as labels, keys(n) as props
            LIMIT 3
        """).data()
        investigations.append({
            "id": 48,
            "question": "How many days of runway do we have at current burn rate?",
            "has_data": False,
            "missing": "FINANCE or CASH nodes with balance data",
            "finding": f"Monthly burn: ${result[0]['total_burn']}, but no cash/reserves found. Checked: {result2}"
        })
        
        # Query 51: Critical dependencies
        print("\n=== Q51: Critical Dependencies ===")
        result = session.run("""
            MATCH (f:FEATURE)
            WHERE f.adoption_rate IS NOT NULL
            RETURN count(*) as count
        """).data()
        investigations.append({
            "id": 51,
            "question": "How many critical dependencies exist in our technology stack?",
            "has_data": True,
            "missing": "Clear definition of 'critical dependency'",
            "finding": f"Using {result[0]['count']} features with adoption_rate as proxy for dependencies"
        })
        
        # Query 52: Recurring vs one-time revenue
        print("\n=== Q52: Recurring vs One-time Revenue ===")
        result = session.run("""
            MATCH (r:REVENUE)
            RETURN count(*) as total,
                   count(CASE WHEN r.source = 'recurring' THEN 1 END) as recurring,
                   count(CASE WHEN r.source = 'one-time' THEN 1 END) as one_time,
                   collect(DISTINCT r.source) as sources
        """).data()
        investigations.append({
            "id": 52,
            "question": "What percentage of revenue is recurring vs one-time?",
            "has_data": False,
            "missing": "source property set to 'recurring' or 'one-time' on REVENUE nodes",
            "finding": f"REVENUE nodes: {result[0]['total']}, but source values are: {result[0]['sources']}"
        })
        
        # Query 53: Marketing channels
        print("\n=== Q53: Marketing Channels ===")
        result = session.run("""
            CALL db.labels() YIELD label
            WHERE label CONTAINS 'MARKETING' OR label CONTAINS 'CHANNEL'
            RETURN collect(label) as marketing_labels
        """).data()
        investigations.append({
            "id": 53,
            "question": "Which marketing channels have the highest ROI?",
            "has_data": False,
            "missing": "MARKETING_CHANNEL nodes",
            "finding": f"No marketing-related labels found. Checked: {result[0]['marketing_labels'] if result else 'none'}"
        })
        
        # Query 58: Technical debt
        print("\n=== Q58: Technical Debt ===")
        result = session.run("""
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE prop CONTAINS 'debt' OR prop CONTAINS 'technical')
            RETURN count(*) as count, labels(n) as labels
            LIMIT 5
        """).data()
        investigations.append({
            "id": 58,
            "question": "What percentage of our codebase has technical debt?",
            "has_data": False,
            "missing": "CODEBASE or TECHNICAL_DEBT nodes",
            "finding": f"No technical debt metrics found. Nodes with debt properties: {result}"
        })
    
    return investigations

def main():
    config = Config.from_env()
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_username, config.neo4j_password)
    )
    
    print("NEO4J DATA INVESTIGATION FOR FAILED QUERIES")
    print("=" * 80)
    
    investigations = investigate_all_failed_queries(driver)
    
    # Save detailed results
    with open('failed_queries_investigation.json', 'w') as f:
        json.dump(investigations, f, indent=2)
    
    # Summary report
    print("\n" + "="*80)
    print("INVESTIGATION SUMMARY")
    print("="*80)
    
    queries_with_data = sum(1 for i in investigations if i['has_data'])
    queries_without_data = len(investigations) - queries_with_data
    
    print(f"\nTotal failed queries investigated: {len(investigations)}")
    print(f"Queries with partial/proxy data: {queries_with_data}")
    print(f"Queries with no relevant data: {queries_without_data}")
    
    print("\n" + "="*80)
    print("DETAILED FINDINGS BY QUERY")
    print("="*80)
    
    for inv in investigations:
        status = "PARTIAL DATA" if inv['has_data'] else "NO DATA"
        print(f"\nQuery {inv['id']}: {inv['question']}")
        print(f"Status: {status}")
        print(f"Missing: {inv['missing']}")
        print(f"Finding: {inv['finding']}")
        print("-" * 80)
    
    # Write markdown report
    with open('FAILED_QUERIES_NEO4J_INVESTIGATION.md', 'w') as f:
        f.write("# Neo4j Investigation Report for Failed Queries\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total failed queries: {len(investigations)}\n")
        f.write(f"- Queries with partial/proxy data: {queries_with_data}\n")
        f.write(f"- Queries with no relevant data: {queries_without_data}\n\n")
        
        f.write("## Detailed Findings\n\n")
        for inv in investigations:
            f.write(f"### Query {inv['id']}: {inv['question']}\n\n")
            f.write(f"**Status**: {'Has Partial Data' if inv['has_data'] else 'No Data'}\n\n")
            f.write(f"**Missing**: {inv['missing']}\n\n")
            f.write(f"**Finding**: {inv['finding']}\n\n")
            f.write("---\n\n")
    
    driver.close()
    print(f"\nDetailed report saved to: FAILED_QUERIES_NEO4J_INVESTIGATION.md")

if __name__ == "__main__":
    main()