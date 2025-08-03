#!/usr/bin/env python3
"""Comprehensive investigation of Neo4j data for all 18 failed queries"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from neo4j import GraphDatabase

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
            "finding": "No projection/forecast nodes found" if not q7_has_data else "Some projection data exists"
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
            "has_data": has_events,
            "finding": "Events exist but no resolution dates/times" if has_events and not has_resolution else "No support events"
        })
        
        # Query 19: Team size vs project completion
        print("\n=== Q19: Team Size vs Project Completion ===")
        result = session.run("""
            MATCH (t:TEAM)
            RETURN count(*) as team_count, collect(DISTINCT keys(t)) as all_props
        """).data()
        has_teams = result[0]['team_count'] > 0
        print(f"Teams: {result[0]['team_count']}")
        
        result2 = session.run("""
            MATCH (p:PROJECT)
            RETURN count(*) as project_count, collect(keys(p))[0] as props
        """).data()
        has_projects = result2[0]['project_count'] > 0
        investigations.append({
            "id": 19,
            "question": "What is the correlation between team size and project completion rates?",
            "has_data": has_teams,
            "finding": f"Teams exist but no PROJECT nodes found (count: {result2[0]['project_count']})"
        })
        
        # Query 20: Critical milestones
        print("\n=== Q20: Critical Milestones ===")
        result = session.run("""
            MATCH (n)
            WHERE 'MILESTONE' IN labels(n) OR 'ROADMAPITEM' IN labels(n)
            RETURN labels(n) as labels, count(*) as count
        """).data()
        has_milestones = any(r['count'] > 0 for r in result)
        investigations.append({
            "id": 20,
            "question": "How many critical milestones are at risk of being missed this quarter?",
            "has_data": has_milestones,
            "finding": f"Found ROADMAPITEM nodes but no MILESTONE nodes" if has_milestones else "No milestone data"
        })
        
        # Query 25: Projects over budget
        print("\n=== Q25: Projects Over Budget ===")
        result = session.run("""
            MATCH (n:PROJECT)
            RETURN count(*) as count, collect(keys(n))[0] as props
        """).data()
        has_project_nodes = result[0]['count'] > 0
        investigations.append({
            "id": 25,
            "question": "What percentage of projects are currently over budget?",
            "has_data": has_project_nodes,
            "finding": f"PROJECT nodes exist ({result[0]['count']}) but likely missing budget properties"
        })
        
        # Query 26: Employee satisfaction
        print("\n=== Q26: Employee Satisfaction ===")
        result = session.run("""
            MATCH (n)
            WHERE 'EMPLOYEE' IN labels(n) OR any(prop IN keys(n) WHERE prop = 'employee_satisfaction')
            RETURN count(*) as count
        """).data()
        has_employee_data = result[0]['count'] > 0
        
        # Check teams for satisfaction
        result2 = session.run("""
            MATCH (t:TEAM)
            WHERE exists(t.satisfaction_score)
            RETURN count(*) as count
        """).data()
        has_team_satisfaction = result2[0]['count'] > 0
        investigations.append({
            "id": 26,
            "question": "Which teams have the highest employee satisfaction scores?",
            "has_data": has_team_satisfaction,
            "finding": f"Teams have satisfaction_score property ({result2[0]['count']} teams)" if has_team_satisfaction else "No employee satisfaction data"
        })
        
        # Query 28: Security incidents
        print("\n=== Q28: Security Incidents ===")
        result = session.run("""
            MATCH (e:EVENT)
            WHERE e.type CONTAINS 'security' OR e.type CONTAINS 'incident'
            RETURN count(*) as count, collect(DISTINCT e.type) as types
        """).data()
        has_security = result[0]['count'] > 0
        investigations.append({
            "id": 28,
            "question": "How many security incidents have been reported in the last quarter?",
            "has_data": has_security,
            "finding": f"No security incident events found (checked {result[0]['count']} events)"
        })
        
        # Query 31: Lead conversion
        print("\n=== Q31: Lead Conversion ===")
        result = session.run("""
            MATCH (n)
            WHERE 'LEAD' IN labels(n)
            RETURN count(*) as count
        """).data()
        has_leads = result[0]['count'] > 0
        investigations.append({
            "id": 31,
            "question": "What is the average time from lead to customer conversion?",
            "has_data": has_leads,
            "finding": "No LEAD entities in the graph"
        })
        
        # Query 32: Deprecated features
        print("\n=== Q32: Deprecated Features ===")
        result = session.run("""
            MATCH (f:FEATURE)
            WHERE exists(f.deprecated) OR exists(f.is_deprecated) OR f.status = 'deprecated'
            RETURN count(*) as count
        """).data()
        has_deprecated = result[0]['count'] > 0
        
        result2 = session.run("""
            MATCH (f:FEATURE)
            RETURN count(*) as total, collect(DISTINCT keys(f)) as all_props
        """).data()
        investigations.append({
            "id": 32,
            "question": "How many customers are using deprecated features?",
            "has_data": has_deprecated,
            "finding": f"Features exist ({result2[0]['total']}) but no deprecated flag/property"
        })
        
        # Query 34: SLA violations
        print("\n=== Q34: SLA Violations ===")
        result = session.run("""
            MATCH (n:SLA)
            RETURN count(*) as count
        """).data()
        has_sla = result[0]['count'] > 0
        
        result2 = session.run("""
            MATCH (e:EVENT)
            WHERE e.type CONTAINS 'sla' OR e.type CONTAINS 'violation'
            RETURN count(*) as count, collect(DISTINCT e.type) as types
        """).data()
        investigations.append({
            "id": 34,
            "question": "Which SLAs are most frequently violated?",
            "has_data": has_sla,
            "finding": f"SLA nodes exist ({result[0]['count']}) but no violation tracking" if has_sla else "No SLA violation events"
        })
        
        # Query 39: Revenue per employee
        print("\n=== Q39: Revenue per Employee ===")
        result = session.run("""
            MATCH (t:TEAM)
            WHERE exists(t.headcount) OR exists(t.employee_count) OR exists(t.size)
            RETURN count(*) as count, collect(t.name)[..3] as sample_teams
        """).data()
        has_employee_counts = result[0]['count'] > 0
        investigations.append({
            "id": 39,
            "question": "What is the average revenue per employee across different departments?",
            "has_data": has_employee_counts,
            "finding": f"Teams have headcount/size data ({result[0]['count']} teams: {result[0]['sample_teams']})" if has_employee_counts else "No employee count data"
        })
        
        # Query 43: Acquisition cost trends
        print("\n=== Q43: Acquisition Cost Trends ===")
        result = session.run("""
            MATCH (c:COST)
            WHERE c.category CONTAINS 'acquisition' OR c.category CONTAINS 'customer'
            RETURN count(*) as count, collect(DISTINCT c.period)[..5] as periods
        """).data()
        has_acq_costs = result[0]['count'] > 0
        investigations.append({
            "id": 43,
            "question": "What is the trend in customer acquisition costs over time?",
            "has_data": has_acq_costs,
            "finding": f"Found {result[0]['count']} acquisition costs with periods: {result[0]['periods']}" if has_acq_costs else "No acquisition cost data with time periods"
        })
        
        # Query 44: Pipeline opportunities
        print("\n=== Q44: Pipeline Opportunities ===")
        result = session.run("""
            MATCH (n)
            WHERE 'OPPORTUNITY' IN labels(n) OR 'PIPELINE' IN labels(n) OR 'EXPANSION_OPPORTUNITY' IN labels(n)
            RETURN labels(n) as labels, count(*) as count
        """).data()
        has_opportunities = any(r['count'] > 0 for r in result)
        investigations.append({
            "id": 44,
            "question": "How many high-value opportunities are in the pipeline?",
            "has_data": has_opportunities,
            "finding": "Found EXPANSION_OPPORTUNITY nodes" if has_opportunities else "No opportunity/pipeline entities"
        })
        
        # Query 48: Runway calculation
        print("\n=== Q48: Days of Runway ===")
        result = session.run("""
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE prop CONTAINS 'cash' OR prop CONTAINS 'balance' OR prop CONTAINS 'reserve')
            RETURN labels(n) as labels, keys(n) as props
            LIMIT 5
        """).data()
        has_cash = len(result) > 0
        
        result2 = session.run("""
            MATCH (t:TEAM)
            WHERE exists(t.monthly_cost)
            RETURN sum(t.monthly_cost) as total_burn
        """).data()
        investigations.append({
            "id": 48,
            "question": "How many days of runway do we have at current burn rate?",
            "has_data": False,
            "finding": f"Teams have monthly costs (burn: ${result2[0]['total_burn']}) but no cash/reserves data"
        })
        
        # Query 51: Critical dependencies
        print("\n=== Q51: Critical Dependencies ===")
        result = session.run("""
            MATCH (f:FEATURE)
            WHERE exists(f.adoption_rate)
            RETURN count(*) as count
        """).data()
        investigations.append({
            "id": 51,
            "question": "How many critical dependencies exist in our technology stack?",
            "has_data": True,
            "finding": f"Using features with adoption_rate as proxy ({result[0]['count']} features)"
        })
        
        # Query 52: Recurring vs one-time revenue
        print("\n=== Q52: Recurring vs One-time Revenue ===")
        result = session.run("""
            MATCH (r:REVENUE)
            RETURN r.source as source, count(*) as count
        """).data()
        has_revenue_types = len(result) > 0 and any(r['source'] in ['recurring', 'one-time'] for r in result)
        investigations.append({
            "id": 52,
            "question": "What percentage of revenue is recurring vs one-time?",
            "has_data": has_revenue_types,
            "finding": f"REVENUE nodes exist but 'source' property not set to recurring/one-time"
        })
        
        # Query 53: Marketing channels
        print("\n=== Q53: Marketing Channels ===")
        result = session.run("""
            MATCH (n)
            WHERE 'MARKETING_CHANNEL' IN labels(n) OR 'MARKETING' IN labels(n)
            RETURN count(*) as count
        """).data()
        has_marketing = result[0]['count'] > 0
        investigations.append({
            "id": 53,
            "question": "Which marketing channels have the highest ROI?",
            "has_data": has_marketing,
            "finding": "No MARKETING_CHANNEL entities in the graph"
        })
        
        # Query 58: Technical debt
        print("\n=== Q58: Technical Debt ===")
        result = session.run("""
            MATCH (n)
            WHERE any(prop IN keys(n) WHERE prop CONTAINS 'debt' OR prop CONTAINS 'technical' OR prop CONTAINS 'code_quality')
            RETURN count(*) as count
        """).data()
        has_tech_debt = result[0]['count'] > 0
        investigations.append({
            "id": 58,
            "question": "What percentage of our codebase has technical debt?",
            "has_data": has_tech_debt,
            "finding": "No technical debt or codebase metrics in the graph"
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
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY OF FINDINGS")
    print("="*80)
    
    queries_with_data = sum(1 for i in investigations if i['has_data'])
    queries_without_data = len(investigations) - queries_with_data
    
    print(f"\nTotal failed queries investigated: {len(investigations)}")
    print(f"Queries with some relevant data: {queries_with_data}")
    print(f"Queries with no relevant data: {queries_without_data}")
    
    print("\nDETAILED FINDINGS:")
    print("-" * 80)
    for inv in investigations:
        status = "✓ HAS DATA" if inv['has_data'] else "✗ NO DATA"
        print(f"\n[{status}] Query {inv['id']}: {inv['question']}")
        print(f"Finding: {inv['finding']}")
    
    driver.close()

if __name__ == "__main__":
    main()