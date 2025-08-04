#!/usr/bin/env python3
"""Add missing operational risk, project delivery, and team performance data to Neo4j"""

import os
from neo4j import GraphDatabase
from datetime import datetime, timedelta
import random

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def add_operational_risks(session):
    """Add comprehensive operational risk data"""
    print("\n=== Adding Operational Risks ===")
    
    # Define operational risks with severity and impact
    operational_risks = [
        {
            "name": "Insufficient Cloud Infrastructure Capacity",
            "severity": "high",
            "category": "infrastructure",
            "impact_description": "Could cause service outages for 30% of customers",
            "mitigation_status": "in_progress",
            "mitigation_strategy": "Expanding AWS capacity in 3 regions"
        },
        {
            "name": "Key Personnel Dependencies",
            "severity": "critical",
            "category": "staffing",
            "impact_description": "Loss of senior engineers could delay roadmap by 6 months",
            "mitigation_status": "planned",
            "mitigation_strategy": "Implementing knowledge transfer program"
        },
        {
            "name": "Legacy System Integration Risks",
            "severity": "medium",
            "category": "technical_debt",
            "impact_description": "Integration failures affecting 15% of enterprise customers",
            "mitigation_status": "active",
            "mitigation_strategy": "Modernization initiative Q2 2025"
        },
        {
            "name": "Security Vulnerability in API Gateway",
            "severity": "high",
            "category": "security",
            "impact_description": "Potential data breach risk for financial services customers",
            "mitigation_status": "completed",
            "mitigation_strategy": "Patched in v2.3.1, monitoring ongoing"
        },
        {
            "name": "Database Performance Degradation",
            "severity": "medium",
            "category": "performance",
            "impact_description": "Response times increased by 40% during peak hours",
            "mitigation_status": "active",
            "mitigation_strategy": "Database sharding implementation underway"
        },
        {
            "name": "Third-party Service Dependencies",
            "severity": "high",
            "category": "dependencies",
            "impact_description": "Payment processing outages affecting revenue collection",
            "mitigation_status": "planned",
            "mitigation_strategy": "Multi-vendor redundancy strategy"
        },
        {
            "name": "Compliance Gap with GDPR Updates",
            "severity": "critical",
            "category": "compliance",
            "impact_description": "Risk of regulatory fines up to $5M",
            "mitigation_status": "active",
            "mitigation_strategy": "Privacy team implementing new controls"
        },
        {
            "name": "AI Model Drift in Production",
            "severity": "medium",
            "category": "ai_operations",
            "impact_description": "Accuracy degradation affecting 20% of predictions",
            "mitigation_status": "in_progress",
            "mitigation_strategy": "Implementing continuous model monitoring"
        }
    ]
    
    # Create operational risks
    for risk in operational_risks:
        session.run("""
            MERGE (r:__Entity__:OPERATIONAL_RISK {
                id: 'oprisk_' + $name
            })
            ON CREATE SET
                r.name = $name,
                r.severity = $severity,
                r.category = $category,
                r.impact_description = $impact_description,
                r.mitigation_status = $mitigation_status,
                r.mitigation_strategy = $mitigation_strategy,
                r.created_date = date(),
                r.risk_score = CASE 
                    WHEN $severity = 'critical' THEN 90
                    WHEN $severity = 'high' THEN 70
                    WHEN $severity = 'medium' THEN 50
                    ELSE 30
                END
        """, risk)
    
    # Link operational risks to products and SLAs
    session.run("""
        MATCH (r:OPERATIONAL_RISK)
        WHERE r.category = 'infrastructure' OR r.category = 'performance'
        MATCH (p:PRODUCT)
        WHERE p.name CONTAINS 'Cloud' OR p.name CONTAINS 'AI'
        CREATE (r)-[:IMPACTS_PRODUCT {
            impact_level: CASE WHEN r.severity = 'critical' THEN 'severe' ELSE 'moderate' END
        }]->(p)
    """)
    
    session.run("""
        MATCH (r:OPERATIONAL_RISK)
        WHERE r.category IN ['infrastructure', 'performance', 'security']
        MATCH (s:SLA)
        CREATE (r)-[:THREATENS_SLA {
            threat_level: r.severity,
            estimated_impact: 'Could cause ' + toString(toInteger(rand() * 30) + 10) + '% SLA breach'
        }]->(s)
    """)
    
    # Link to customer success scores
    session.run("""
        MATCH (r:OPERATIONAL_RISK)
        WHERE r.severity IN ['high', 'critical']
        MATCH (c:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < 70
        CREATE (r)-[:AFFECTS_CUSTOMER {
            impact_probability: CASE 
                WHEN r.severity = 'critical' THEN 0.8
                ELSE 0.5
            END
        }]->(c)
    """)
    
    # Add operational risk exposures
    risk_exposures = [
        ("SpyroCloud", 850000),
        ("SpyroAI", 1200000),
        ("SpyroSecure", 650000),
        ("SpyroCloud Enterprise Edition", 2100000),
        ("SpyroAI for predictive maintenance", 950000)
    ]
    
    for product, exposure in risk_exposures:
        session.run("""
            MATCH (p:PRODUCT {name: $product})
            MATCH (r:OPERATIONAL_RISK)
            WHERE r.severity IN ['high', 'critical']
            WITH p, r, $exposure as base_exposure
            CREATE (p)-[:HAS_RISK_EXPOSURE {
                amount: base_exposure * (CASE 
                    WHEN r.severity = 'critical' THEN 1.5 
                    ELSE 1.0 
                END),
                currency: 'USD',
                assessment_date: date()
            }]->(r)
        """, {"product": product, "exposure": exposure})
    
    print("✓ Added 8 operational risks with impacts on products, SLAs, and customers")


def add_project_delivery_data(session):
    """Add comprehensive project delivery data"""
    print("\n=== Adding Project Delivery Data ===")
    
    # Create projects with detailed attributes
    projects = [
        {
            "name": "Cloud Infrastructure Modernization",
            "status": "in_progress",
            "priority": "critical",
            "start_date": "2024-10-01",
            "target_date": "2025-06-30",
            "completion_percentage": 45,
            "revenue_impact": 3500000,
            "blocked": False,
            "blocking_reason": None
        },
        {
            "name": "AI Model Performance Enhancement",
            "status": "at_risk",
            "priority": "high",
            "start_date": "2024-11-15",
            "target_date": "2025-04-15",
            "completion_percentage": 30,
            "revenue_impact": 2100000,
            "blocked": True,
            "blocking_reason": "Waiting for GPU resources allocation"
        },
        {
            "name": "Enterprise Security Framework",
            "status": "on_track",
            "priority": "high",
            "start_date": "2024-09-01",
            "target_date": "2025-03-31",
            "completion_percentage": 65,
            "revenue_impact": 1800000,
            "blocked": False,
            "blocking_reason": None
        },
        {
            "name": "Customer Portal Redesign",
            "status": "delayed",
            "priority": "medium",
            "start_date": "2024-08-01",
            "target_date": "2025-02-28",
            "completion_percentage": 25,
            "revenue_impact": 950000,
            "blocked": True,
            "blocking_reason": "UX team capacity constraints"
        },
        {
            "name": "Real-time Analytics Platform",
            "status": "in_progress",
            "priority": "high",
            "start_date": "2024-12-01",
            "target_date": "2025-07-31",
            "completion_percentage": 20,
            "revenue_impact": 2800000,
            "blocked": False,
            "blocking_reason": None
        },
        {
            "name": "Global Compliance Initiative",
            "status": "on_track",
            "priority": "critical",
            "start_date": "2024-07-01",
            "target_date": "2025-01-31",
            "completion_percentage": 85,
            "revenue_impact": 4200000,
            "blocked": False,
            "blocking_reason": None
        },
        {
            "name": "API Gateway v3.0",
            "status": "at_risk",
            "priority": "high",
            "start_date": "2024-10-15",
            "target_date": "2025-05-15",
            "completion_percentage": 35,
            "revenue_impact": 1600000,
            "blocked": True,
            "blocking_reason": "Legacy system integration issues"
        },
        {
            "name": "Mobile App Development",
            "status": "delayed",
            "priority": "medium",
            "start_date": "2024-11-01",
            "target_date": "2025-08-31",
            "completion_percentage": 15,
            "revenue_impact": 750000,
            "blocked": True,
            "blocking_reason": "Pending architecture decisions"
        },
        {
            "name": "Data Lake Migration",
            "status": "in_progress",
            "priority": "high",
            "start_date": "2024-09-15",
            "target_date": "2025-04-30",
            "completion_percentage": 55,
            "revenue_impact": 2300000,
            "blocked": False,
            "blocking_reason": None
        },
        {
            "name": "Customer Success Automation",
            "status": "on_track",
            "priority": "medium",
            "start_date": "2024-12-15",
            "target_date": "2025-06-15",
            "completion_percentage": 40,
            "revenue_impact": 1100000,
            "blocked": False,
            "blocking_reason": None
        }
    ]
    
    # Create project nodes
    for proj in projects:
        session.run("""
            MERGE (p:__Entity__:PROJECT {
                id: 'project_' + $name
            })
            ON CREATE SET
                p.name = $name,
                p.status = $status,
                p.priority = $priority,
                p.start_date = date($start_date),
                p.target_date = date($target_date),
                p.completion_percentage = $completion_percentage,
                p.revenue_impact = $revenue_impact,
                p.is_blocked = $blocked,
                p.blocking_reason = $blocking_reason,
                p.days_until_deadline = duration.between(date(), date($target_date)).days,
                p.is_delayed = CASE WHEN $status = 'delayed' THEN true ELSE false END,
                p.is_critical_for_revenue = CASE WHEN $revenue_impact > 2000000 THEN true ELSE false END
        """, proj)
    
    # Create project dependencies
    dependencies = [
        ("Cloud Infrastructure Modernization", "Real-time Analytics Platform"),
        ("AI Model Performance Enhancement", "Real-time Analytics Platform"),
        ("Enterprise Security Framework", "API Gateway v3.0"),
        ("API Gateway v3.0", "Mobile App Development"),
        ("Data Lake Migration", "Real-time Analytics Platform"),
        ("Customer Portal Redesign", "Customer Success Automation")
    ]
    
    for upstream, downstream in dependencies:
        session.run("""
            MATCH (p1:PROJECT {name: $upstream})
            MATCH (p2:PROJECT {name: $downstream})
            CREATE (p1)-[:BLOCKS {
                type: 'hard_dependency',
                impact: 'Cannot start until upstream completes'
            }]->(p2)
        """, {"upstream": upstream, "downstream": downstream})
    
    # Link projects to teams
    project_teams = [
        ("Cloud Infrastructure Modernization", "Cloud Platform Team"),
        ("AI Model Performance Enhancement", "AI Team"),
        ("Enterprise Security Framework", "Security Team"),
        ("Customer Portal Redesign", "Frontend Team"),
        ("Real-time Analytics Platform", "Data Engineering Team"),
        ("Global Compliance Initiative", "Compliance Team"),
        ("API Gateway v3.0", "Backend Team"),
        ("Mobile App Development", "Mobile Team"),
        ("Data Lake Migration", "Data Engineering Team"),
        ("Customer Success Automation", "Customer Success Team")
    ]
    
    for project, team in project_teams:
        session.run("""
            MATCH (p:PROJECT {name: $project})
            MATCH (t:TEAM {name: $team})
            CREATE (t)-[:DELIVERS {
                allocation_percentage: toInteger(rand() * 40) + 60,
                team_members_assigned: toInteger(rand() * 5) + 3
            }]->(p)
        """, {"project": project, "team": team})
    
    # Link projects to products
    project_products = [
        ("Cloud Infrastructure Modernization", ["SpyroCloud", "SpyroCloud Enterprise Edition"]),
        ("AI Model Performance Enhancement", ["SpyroAI", "SpyroAI for predictive maintenance"]),
        ("Enterprise Security Framework", ["SpyroSecure"]),
        ("Real-time Analytics Platform", ["SpyroAI", "SpyroCloud"]),
        ("API Gateway v3.0", ["SpyroCloud", "SpyroCloud Enterprise Edition"])
    ]
    
    for project, products in project_products:
        for product in products:
            session.run("""
                MATCH (proj:PROJECT {name: $project})
                MATCH (prod:PRODUCT {name: $product})
                CREATE (proj)-[:ENHANCES {
                    impact_type: 'performance_improvement',
                    expected_benefit: toString(toInteger(rand() * 30) + 10) + '% improvement'
                }]->(prod)
            """, {"project": project, "product": product})
    
    # Link critical projects to revenue
    session.run("""
        MATCH (p:PROJECT)
        WHERE p.is_critical_for_revenue = true
        CREATE (p)-[:MAINTAINS_REVENUE {
            amount: p.revenue_impact,
            risk_if_delayed: p.revenue_impact * 0.3,
            currency: 'USD'
        }]->(r:REVENUE {
            amount: p.revenue_impact,
            type: 'maintained_by_project',
            project_name: p.name
        })
    """)
    
    # Add operational constraints
    constraints = [
        {
            "name": "GPU Resource Shortage",
            "type": "resource",
            "severity": "high",
            "affected_projects": ["AI Model Performance Enhancement", "Real-time Analytics Platform"]
        },
        {
            "name": "Senior Engineer Availability",
            "type": "staffing",
            "severity": "critical",
            "affected_projects": ["Cloud Infrastructure Modernization", "API Gateway v3.0"]
        },
        {
            "name": "Budget Freeze Q1 2025",
            "type": "financial",
            "severity": "medium",
            "affected_projects": ["Mobile App Development", "Customer Portal Redesign"]
        },
        {
            "name": "Legacy System Access Windows",
            "type": "technical",
            "severity": "high",
            "affected_projects": ["API Gateway v3.0", "Data Lake Migration"]
        }
    ]
    
    for constraint in constraints:
        session.run("""
            MERGE (c:__Entity__:OPERATIONAL_CONSTRAINT {
                id: 'constraint_' + $name
            })
            ON CREATE SET
                c.name = $name,
                c.type = $type,
                c.severity = $severity,
                c.active = true
        """, constraint)
        
        for project in constraint["affected_projects"]:
            session.run("""
                MATCH (c:OPERATIONAL_CONSTRAINT {name: $constraint})
                MATCH (p:PROJECT {name: $project})
                CREATE (c)-[:BLOCKS_PROJECT {
                    impact_level: $severity,
                    mitigation_required: true
                }]->(p)
            """, {"constraint": constraint["name"], "project": project, "severity": constraint["severity"]})
    
    print("✓ Added 10 projects with dependencies, team assignments, and constraints")


def add_team_performance_metrics(session):
    """Add comprehensive team performance metrics"""
    print("\n=== Adding Team Performance Metrics ===")
    
    # First ensure all teams have proper attributes
    teams = [
        ("Cloud Platform Team", 12, 185000),
        ("AI Team", 15, 195000),
        ("Security Team", 8, 175000),
        ("Frontend Team", 10, 155000),
        ("Data Engineering Team", 11, 180000),
        ("Backend Team", 14, 170000),
        ("Mobile Team", 7, 160000),
        ("Customer Success Team", 9, 145000),
        ("Compliance Team", 6, 165000),
        ("DevOps Team", 10, 175000)
    ]
    
    for team_name, size, avg_salary in teams:
        session.run("""
            MATCH (t:TEAM {name: $team_name})
            SET t.team_size = $size,
                t.average_salary = $avg_salary,
                t.total_cost = $size * $avg_salary,
                t.utilization_rate = toFloat(toInteger(rand() * 30) + 70) / 100,
                t.efficiency_score = toFloat(toInteger(rand() * 20) + 80) / 100
        """, {"team_name": team_name, "size": size, "avg_salary": avg_salary})
    
    # Add department hierarchy
    departments = [
        ("Engineering", ["Cloud Platform Team", "AI Team", "Backend Team", "Frontend Team", "Mobile Team", "DevOps Team"]),
        ("Data & Analytics", ["Data Engineering Team"]),
        ("Security & Compliance", ["Security Team", "Compliance Team"]),
        ("Customer Success", ["Customer Success Team"])
    ]
    
    for dept_name, team_names in departments:
        session.run("""
            MERGE (d:__Entity__:DEPARTMENT {
                id: 'dept_' + $dept_name
            })
            ON CREATE SET
                d.name = $dept_name,
                d.created_date = date()
        """, {"dept_name": dept_name})
        
        for team_name in team_names:
            session.run("""
                MATCH (d:DEPARTMENT {name: $dept_name})
                MATCH (t:TEAM {name: $team_name})
                CREATE (t)-[:BELONGS_TO]->(d)
            """, {"dept_name": dept_name, "team_name": team_name})
    
    # Add team performance metrics
    session.run("""
        MATCH (t:TEAM)-[:SUPPORTS]->(p:PRODUCT)-[:GENERATES]->(r:REVENUE)
        WITH t, sum(r.amount) as total_revenue, count(distinct p) as products_supported
        SET t.revenue_supported = total_revenue,
            t.products_supported = products_supported,
            t.revenue_per_member = total_revenue / t.team_size
    """)
    
    # Add team-to-customer impact relationships
    session.run("""
        MATCH (t:TEAM)-[:SUPPORTS]->(p:PRODUCT)<-[:USES]-(c:CUSTOMER)
        WITH t, c
        CREATE (t)-[:IMPACTS_CUSTOMER {
            impact_type: 'product_support',
            impact_level: 'direct'
        }]->(c)
    """)
    
    # Create team workload metrics
    session.run("""
        MATCH (t:TEAM)-[:DELIVERS]->(proj:PROJECT)
        WITH t, count(proj) as active_projects, 
             sum(CASE WHEN proj.is_blocked THEN 1 ELSE 0 END) as blocked_projects,
             sum(CASE WHEN proj.status = 'at_risk' THEN 1 ELSE 0 END) as at_risk_projects
        SET t.active_projects = active_projects,
            t.blocked_projects = blocked_projects,
            t.at_risk_projects = at_risk_projects,
            t.workload_score = active_projects * 1.0 / t.team_size
    """)
    
    # Add critical work assignments
    critical_work = [
        ("AI Team", "Enterprise AI Strategy", 5, 3200000),
        ("Cloud Platform Team", "Multi-region Expansion", 4, 2800000),
        ("Security Team", "Zero Trust Implementation", 3, 1900000),
        ("Data Engineering Team", "Real-time Data Pipeline", 4, 2400000),
        ("Backend Team", "API Performance Optimization", 3, 1700000)
    ]
    
    for team, work_name, team_members, revenue_impact in critical_work:
        session.run("""
            MATCH (t:TEAM {name: $team})
            MERGE (w:__Entity__:CRITICAL_WORK {
                id: 'work_' + $work_name
            })
            ON CREATE SET
                w.name = $work_name,
                w.assigned_team_members = $team_members,
                w.revenue_impact = $revenue_impact,
                w.priority = 'critical',
                w.status = 'in_progress'
            MERGE (t)-[:ASSIGNED_TO {
                team_members: $team_members,
                allocation_percentage: toFloat($team_members) / t.team_size * 100
            }]->(w)
        """, {"team": team, "work_name": work_name, "team_members": team_members, "revenue_impact": revenue_impact})
    
    # Link teams to customer success
    session.run("""
        MATCH (t:TEAM)-[:IMPACTS_CUSTOMER]->(c:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:CUSTOMER_SUCCESS_SCORE)
        WITH t, avg(css.score) as avg_customer_score, count(distinct c) as customers_impacted
        SET t.avg_customer_success_impact = avg_customer_score,
            t.customers_impacted = customers_impacted,
            t.customer_impact_score = avg_customer_score * customers_impacted / 100
    """)
    
    # Add understaffing indicators
    understaffed = ["AI Team", "Cloud Platform Team", "Data Engineering Team"]
    for team in understaffed:
        session.run("""
            MATCH (t:TEAM {name: $team})
            SET t.is_understaffed = true,
                t.staffing_gap = toInteger(rand() * 3) + 2,
                t.staffing_impact = 'Delays in ' + toString(toInteger(rand() * 30) + 20) + '% of deliverables'
        """, {"team": team})
    
    print("✓ Added team performance metrics, department hierarchy, and workload data")


def add_additional_relationships(session):
    """Add additional cross-cutting relationships"""
    print("\n=== Adding Additional Relationships ===")
    
    # Link operational risks to projects
    session.run("""
        MATCH (r:OPERATIONAL_RISK)
        WHERE r.category IN ['infrastructure', 'technical_debt', 'performance']
        MATCH (p:PROJECT)
        WHERE p.name CONTAINS 'Infrastructure' OR p.name CONTAINS 'Platform' OR p.name CONTAINS 'Migration'
        CREATE (r)-[:IMPACTS_PROJECT {
            delay_risk: CASE 
                WHEN r.severity = 'critical' THEN '3-6 months'
                WHEN r.severity = 'high' THEN '1-3 months'
                ELSE '2-4 weeks'
            END,
            mitigation_priority: r.severity
        }]->(p)
    """)
    
    # Create risk correlation matrix
    session.run("""
        MATCH (r1:OPERATIONAL_RISK)
        MATCH (r2:RISK)
        WHERE r1.severity IN ['high', 'critical'] AND r2.severity IN ['High', 'Critical']
        CREATE (r1)-[:CORRELATES_WITH {
            correlation_strength: CASE 
                WHEN r1.category = 'infrastructure' AND r2.name CONTAINS 'technical' THEN 0.8
                WHEN r1.category = 'staffing' AND r2.name CONTAINS 'delivery' THEN 0.7
                ELSE 0.5
            END,
            combined_impact: 'multiplier_effect'
        }]->(r2)
    """)
    
    # Add regional expansion data
    regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
    for region in regions:
        growth_potential = random.randint(15, 45)
        market_size = random.randint(5000000, 20000000)
        
        session.run("""
            MATCH (r:REGION {name: $region})
            SET r.growth_potential_percentage = $growth,
                r.market_size_usd = $market_size,
                r.competitive_position = CASE 
                    WHEN $growth > 35 THEN 'strong'
                    WHEN $growth > 25 THEN 'moderate'
                    ELSE 'emerging'
                END,
                r.expansion_priority = CASE
                    WHEN $market_size > 15000000 THEN 'high'
                    WHEN $market_size > 10000000 THEN 'medium'
                    ELSE 'low'
                END
        """, {"region": region, "growth": growth_potential, "market_size": market_size})
    
    # Add competitive features
    competitive_features = [
        ("Real-time Analytics", "SpyroAI", "market_leader"),
        ("Enterprise Security", "SpyroSecure", "competitive_advantage"),
        ("Auto-scaling", "SpyroCloud", "industry_standard"),
        ("Predictive Maintenance", "SpyroAI for predictive maintenance", "unique_differentiator"),
        ("Multi-cloud Support", "SpyroCloud Enterprise Edition", "competitive_advantage")
    ]
    
    for feature_name, product, position in competitive_features:
        session.run("""
            MATCH (p:PRODUCT {name: $product})
            MERGE (f:__Entity__:COMPETITIVE_FEATURE {
                id: 'compfeat_' + $feature_name
            })
            ON CREATE SET
                f.name = $feature_name,
                f.competitive_position = $position,
                f.market_advantage = CASE
                    WHEN $position = 'unique_differentiator' THEN 'high'
                    WHEN $position = 'competitive_advantage' THEN 'medium'
                    ELSE 'low'
                END
            CREATE (p)-[:OFFERS_COMPETITIVE_FEATURE]->(f)
        """, {"feature_name": feature_name, "product": product, "position": position})
    
    # Add SLA industry benchmarks
    session.run("""
        MATCH (s:SLA)
        SET s.industry_benchmark = CASE
            WHEN s.type = 'uptime' THEN '99.95%'
            WHEN s.type = 'response_time' THEN '200ms'
            WHEN s.type = 'resolution_time' THEN '4 hours'
            ELSE '95th percentile'
        END,
        s.competitive_position = CASE
            WHEN rand() > 0.6 THEN 'above_industry'
            WHEN rand() > 0.3 THEN 'at_industry'
            ELSE 'below_industry'
        END
    """)
    
    print("✓ Added risk correlations, regional data, and competitive positioning")


def verify_data_additions(session):
    """Verify the data additions"""
    print("\n=== Verifying Data Additions ===")
    
    queries = [
        ("Operational Risks", "MATCH (r:OPERATIONAL_RISK) RETURN count(r) as count"),
        ("Projects", "MATCH (p:PROJECT) RETURN count(p) as count"),
        ("Project Dependencies", "MATCH ()-[:BLOCKS]->(:PROJECT) RETURN count(*) as count"),
        ("Operational Constraints", "MATCH (c:OPERATIONAL_CONSTRAINT) RETURN count(c) as count"),
        ("Team Metrics", "MATCH (t:TEAM) WHERE t.revenue_per_member IS NOT NULL RETURN count(t) as count"),
        ("Departments", "MATCH (d:DEPARTMENT) RETURN count(d) as count"),
        ("Critical Work", "MATCH (w:CRITICAL_WORK) RETURN count(w) as count"),
        ("Risk-Project Links", "MATCH (:OPERATIONAL_RISK)-[:IMPACTS_PROJECT]->(:PROJECT) RETURN count(*) as count"),
        ("Team-Customer Impact", "MATCH (:TEAM)-[:IMPACTS_CUSTOMER]->(:CUSTOMER) RETURN count(*) as count"),
        ("Competitive Features", "MATCH (f:COMPETITIVE_FEATURE) RETURN count(f) as count")
    ]
    
    for name, query in queries:
        result = session.run(query).single()
        print(f"✓ {name}: {result['count']}")


def main():
    print("=== Adding Missing Neo4j Data for Operational Risk, Project Delivery, and Team Performance ===")
    print(f"Connecting to Neo4j at {NEO4J_URI}")
    
    with driver.session() as session:
        # Add all missing data
        add_operational_risks(session)
        add_project_delivery_data(session)
        add_team_performance_metrics(session)
        add_additional_relationships(session)
        
        # Verify additions
        verify_data_additions(session)
        
        # Get total counts
        result = session.run("""
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN ['OPERATIONAL_RISK', 'PROJECT', 'OPERATIONAL_CONSTRAINT', 'DEPARTMENT', 'CRITICAL_WORK', 'COMPETITIVE_FEATURE'])
            RETURN count(n) as new_nodes
        """).single()
        
        result2 = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) IN ['IMPACTS_PRODUCT', 'THREATENS_SLA', 'AFFECTS_CUSTOMER', 'HAS_RISK_EXPOSURE', 
                              'BLOCKS', 'DELIVERS', 'ENHANCES', 'MAINTAINS_REVENUE', 'BLOCKS_PROJECT',
                              'BELONGS_TO', 'IMPACTS_CUSTOMER', 'ASSIGNED_TO', 'IMPACTS_PROJECT', 
                              'CORRELATES_WITH', 'OFFERS_COMPETITIVE_FEATURE']
            RETURN count(r) as new_relationships
        """).single()
        
        print(f"\n=== SUMMARY ===")
        print(f"✓ Added {result['new_nodes']} new nodes")
        print(f"✓ Added {result2['new_relationships']} new relationships")
        print(f"✓ Data additions complete!")


if __name__ == "__main__":
    main()