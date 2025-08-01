#!/usr/bin/env python3
"""
Script to fill all identified data gaps in the SpyroSolutions Neo4j database
"""

import os
import sys
from datetime import datetime, timedelta
import random
from neo4j import GraphDatabase

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config


class DataGapsFiller:
    def __init__(self):
        self.config = Config.from_env()
        self.driver = GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_username, self.config.neo4j_password)
        )
        
    def close(self):
        self.driver.close()
        
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session(database=self.config.neo4j_database) as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def clear_existing_data(self):
        """Optional: Clear existing data for a fresh start"""
        print("Clearing existing incomplete data...")
        queries = [
            # Clear incomplete nodes
            "MATCH (r:Risk) DETACH DELETE r",
            "MATCH (sla:SLA) DETACH DELETE sla",
            "MATCH (c:Commitment) DETACH DELETE c",
            "MATCH (ri:RoadmapItem) DETACH DELETE ri",
            "MATCH (oc:OperationalCost) DETACH DELETE oc",
            "MATCH (p:Profitability) DETACH DELETE p",
            "MATCH (e:Event) DETACH DELETE e"
        ]
        for query in queries:
            self.execute_query(query)
        print("✓ Cleared incomplete data")
    
    def add_missing_properties(self):
        """Add missing properties to existing nodes"""
        print("\n1. Adding missing properties to existing nodes...")
        
        # Add trend to CustomerSuccessScore
        self.execute_query("""
            MATCH (css:CustomerSuccessScore)
            WHERE css.score >= 80
            SET css.trend = 'improving'
        """)
        
        self.execute_query("""
            MATCH (css:CustomerSuccessScore)
            WHERE css.score >= 60 AND css.score < 80
            SET css.trend = 'stable'
        """)
        
        self.execute_query("""
            MATCH (css:CustomerSuccessScore)
            WHERE css.score < 60
            SET css.trend = 'declining'
        """)
        
        # Add size to teams
        self.execute_query("""
            MATCH (t:Team)
            SET t.size = CASE t.name
                WHEN 'CloudOps' THEN 15
                WHEN 'AI Research' THEN 12
                WHEN 'Security' THEN 8
                ELSE 10
            END
        """)
        
        # Add team_size requirements to projects
        self.execute_query("""
            MATCH (p:Project)
            SET p.team_size = CASE p.name
                WHEN 'Cloud Migration' THEN 20
                WHEN 'AI Enhancement' THEN 15
                WHEN 'Security Audit' THEN 10
                ELSE 12
            END
        """)
        
        print("✓ Added missing properties")
    
    def create_diverse_customers(self):
        """Create customers with diverse success scores"""
        print("\n2. Creating diverse customer data...")
        
        # First, update existing customers
        customers_data = [
            ("TechCorp", 85, "stable", "$8M"),
            ("FinanceHub", 75, "improving", "$5M"),
            ("StartupXYZ", 45, "declining", "$2M"),  # At risk
            ("RetailPlus", 58, "declining", "$3M"),  # At risk
            ("HealthNet", 92, "stable", "$6M"),
            ("EduTech", 35, "declining", "$1.5M"),   # High risk
            ("LogiCorp", 68, "stable", "$4M"),
            ("MediaFlow", 78, "improving", "$3.5M"),
            ("DataSync", 52, "declining", "$2.5M"),  # At risk
            ("CloudFirst", 88, "improving", "$7M")
        ]
        
        for name, score, trend, arr_value in customers_data:
            # First create/update customer and success score
            self.execute_query("""
                MERGE (c:Customer {name: $name})
                MERGE (css:CustomerSuccessScore {customerId: $name})
                SET css.score = $score,
                    css.trend = $trend,
                    css.lastUpdated = datetime()
                MERGE (c)-[:HAS_SUCCESS_SCORE]->(css)
            """, {
                "name": name,
                "score": score,
                "trend": trend
            })
            
            # Then update subscription value
            self.execute_query("""
                MATCH (c:Customer {name: $name})-[:SUBSCRIBES_TO]->(s:SaaSSubscription)
                SET s.value = $arr_value
            """, {
                "name": name,
                "arr_value": arr_value
            })
        
        # Ensure ARR relationships exist
        self.execute_query("""
            MATCH (s:SaaSSubscription)
            WHERE NOT EXISTS((s)-[:GENERATES]->(:AnnualRecurringRevenue))
            CREATE (arr:AnnualRecurringRevenue {
                amount: toFloat(replace(replace(s.value, '$', ''), 'M', '')) * 1000000,
                currency: 'USD',
                period: 'annual'
            })
            CREATE (s)-[:GENERATES]->(arr)
        """)
        
        print("✓ Created diverse customer profiles")
    
    def add_events_with_timestamps(self):
        """Add events with timestamps and impacts"""
        print("\n3. Adding time-series events...")
        
        events_template = [
            {
                "type": "service_outage",
                "impact": "negative",
                "severity": "high",
                "description": "Major API outage affecting core services"
            },
            {
                "type": "feature_request",
                "impact": "neutral",
                "severity": "medium",
                "description": "Customer requested advanced analytics dashboard"
            },
            {
                "type": "support_escalation",
                "impact": "negative",
                "severity": "medium",
                "description": "Multiple support tickets about performance issues"
            },
            {
                "type": "contract_renewal",
                "impact": "positive",
                "severity": "high",
                "description": "Customer renewed contract with 20% expansion"
            },
            {
                "type": "security_incident",
                "impact": "negative",
                "severity": "critical",
                "description": "Security vulnerability discovered in product"
            },
            {
                "type": "positive_feedback",
                "impact": "positive",
                "severity": "low",
                "description": "Customer praised new features in review"
            },
            {
                "type": "performance_issue",
                "impact": "negative",
                "severity": "medium",
                "description": "Slow response times reported during peak hours"
            },
            {
                "type": "training_completed",
                "impact": "positive",
                "severity": "low",
                "description": "Customer team completed advanced training"
            }
        ]
        
        # Get all customers with success scores
        customers = self.execute_query("""
            MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
            RETURN c.name as name, css.score as score
        """)
        
        # Add events for each customer based on their score
        for customer in customers:
            num_events = 5 if customer['score'] < 60 else 3
            
            # More negative events for low-scoring customers
            if customer['score'] < 60:
                event_pool = [e for e in events_template if e['impact'] in ['negative', 'neutral']]
            else:
                event_pool = events_template
            
            for i in range(num_events):
                event = random.choice(event_pool)
                days_ago = random.randint(1, 180)  # Last 6 months
                
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
                    CREATE (e:Event {
                        type: $type,
                        impact: $impact,
                        severity: $severity,
                        description: $description,
                        timestamp: datetime() - duration({days: $days_ago}),
                        eventId: $customer + '_event_' + toString($event_num)
                    })
                    CREATE (css)-[:INFLUENCED_BY]->(e)
                """, {
                    "customer": customer['name'],
                    "type": event['type'],
                    "impact": event['impact'],
                    "severity": event['severity'],
                    "description": event['description'],
                    "days_ago": days_ago,
                    "event_num": i
                })
        
        print("✓ Added time-series events")
    
    def add_roadmap_items(self):
        """Add RoadmapItem nodes and relationships"""
        print("\n4. Adding roadmap items...")
        
        roadmap_items = [
            {
                "product": "SpyroCloud",
                "items": [
                    {
                        "title": "Multi-region deployment",
                        "status": "completed",
                        "estimated_completion": "2025-03-31",
                        "priority": "high"
                    },
                    {
                        "title": "Auto-scaling improvements",
                        "status": "in_progress",
                        "estimated_completion": "2025-06-30",
                        "priority": "high"
                    },
                    {
                        "title": "Advanced monitoring dashboard",
                        "status": "behind_schedule",
                        "estimated_completion": "2025-05-15",
                        "priority": "medium"
                    }
                ]
            },
            {
                "product": "SpyroAI",
                "items": [
                    {
                        "title": "AI Enhancement Phase 2",
                        "status": "behind_schedule",
                        "estimated_completion": "2025-07-31",
                        "priority": "critical"
                    },
                    {
                        "title": "Real-time prediction engine",
                        "status": "in_progress",
                        "estimated_completion": "2025-09-30",
                        "priority": "high"
                    },
                    {
                        "title": "Custom model training",
                        "status": "planned",
                        "estimated_completion": "2025-12-31",
                        "priority": "medium"
                    }
                ]
            },
            {
                "product": "SpyroSecure",
                "items": [
                    {
                        "title": "Zero-trust architecture",
                        "status": "in_progress",
                        "estimated_completion": "2025-08-31",
                        "priority": "critical"
                    },
                    {
                        "title": "Compliance automation",
                        "status": "planned",
                        "estimated_completion": "2025-10-31",
                        "priority": "high"
                    }
                ]
            }
        ]
        
        teams = ["Cloud Platform Team", "AI Research Team", "Security Team"]
        
        for product_roadmap in roadmap_items:
            product_name = product_roadmap["product"]
            
            for idx, item in enumerate(product_roadmap["items"]):
                team = teams[idx % len(teams)]
                
                self.execute_query("""
                    MATCH (p:Product {name: $product})
                    MATCH (t:Team {name: $team})
                    CREATE (ri:RoadmapItem {
                        title: $title,
                        status: $status,
                        estimated_completion: date($completion),
                        priority: $priority,
                        created_date: date('2025-01-01')
                    })
                    CREATE (p)-[:HAS_ROADMAP]->(ri)
                    CREATE (t)-[:RESPONSIBLE_FOR]->(ri)
                """, {
                    "product": product_name,
                    "team": team,
                    "title": item["title"],
                    "status": item["status"],
                    "completion": item["estimated_completion"],
                    "priority": item["priority"]
                })
        
        print("✓ Added roadmap items")
    
    def add_risk_profiles(self):
        """Add risk profiles for customers and objectives"""
        print("\n5. Adding risk profiles...")
        
        # Customer risks
        customer_risks = [
            {
                "customer": "StartupXYZ",
                "risks": [
                    {"type": "churn", "severity": "high", "description": "Low success score and declining trend", "probability": 0.7},
                    {"type": "payment", "severity": "medium", "description": "Late payments in last quarter", "probability": 0.4}
                ]
            },
            {
                "customer": "EduTech",
                "risks": [
                    {"type": "churn", "severity": "critical", "description": "Very low success score", "probability": 0.8},
                    {"type": "feature_gap", "severity": "high", "description": "Missing critical features", "probability": 0.6}
                ]
            },
            {
                "customer": "RetailPlus",
                "risks": [
                    {"type": "competitive", "severity": "medium", "description": "Evaluating competitor solutions", "probability": 0.5},
                    {"type": "integration", "severity": "low", "description": "Integration challenges with legacy systems", "probability": 0.3}
                ]
            },
            {
                "customer": "DataSync",
                "risks": [
                    {"type": "performance", "severity": "high", "description": "Performance not meeting expectations", "probability": 0.6},
                    {"type": "support", "severity": "medium", "description": "High support ticket volume", "probability": 0.5}
                ]
            }
        ]
        
        for customer_risk in customer_risks:
            for risk in customer_risk["risks"]:
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})
                    CREATE (r:Risk {
                        type: $type,
                        severity: $severity,
                        description: $description,
                        probability: $probability,
                        impact_amount: $impact,
                        identified_date: date(),
                        status: 'active'
                    })
                    CREATE (c)-[:HAS_RISK]->(r)
                """, {
                    "customer": customer_risk["customer"],
                    "type": risk["type"],
                    "severity": risk["severity"],
                    "description": risk["description"],
                    "probability": risk["probability"],
                    "impact": random.randint(100000, 2000000)
                })
        
        # Objective risks
        objective_risks = [
            {
                "objective": "Market Expansion",
                "risk": {"type": "market", "severity": "high", "description": "Economic downturn affecting expansion plans"}
            },
            {
                "objective": "Product Innovation",
                "risk": {"type": "technical", "severity": "medium", "description": "Key technical talent shortage"}
            },
            {
                "objective": "Customer Retention",
                "risk": {"type": "competitive", "severity": "high", "description": "New competitor with aggressive pricing"}
            }
        ]
        
        for obj_risk in objective_risks:
            self.execute_query("""
                MATCH (o:Objective {title: $objective})
                CREATE (r:Risk {
                    type: $type,
                    severity: $severity,
                    description: $description,
                    probability: 0.4,
                    impact_amount: $impact,
                    identified_date: date(),
                    status: 'active'
                })
                CREATE (o)-[:AT_RISK]->(r)
            """, {
                "objective": obj_risk["objective"],
                "type": obj_risk["risk"]["type"],
                "severity": obj_risk["risk"]["severity"],
                "description": obj_risk["risk"]["description"],
                "impact": random.randint(500000, 5000000)
            })
        
        # Roadmap risks
        self.execute_query("""
            MATCH (ri:RoadmapItem)
            WHERE ri.status = 'behind_schedule'
            CREATE (r:Risk {
                type: 'delivery',
                severity: 'high',
                description: 'Roadmap item behind schedule: ' + ri.title,
                probability: 0.6,
                impact_amount: 1000000,
                identified_date: date(),
                status: 'active'
            })
            CREATE (ri)-[:AT_RISK]->(r)
        """)
        
        print("✓ Added risk profiles")
    
    def add_sla_and_commitments(self):
        """Add SLA and commitment data"""
        print("\n6. Adding SLA and commitments...")
        
        # SLAs for major customers
        sla_data = [
            {"customer": "TechCorp", "metric": "uptime", "target": 99.9, "penalty": 10},
            {"customer": "FinanceHub", "metric": "uptime", "target": 99.95, "penalty": 15},
            {"customer": "HealthNet", "metric": "response_time", "target": 200, "penalty": 5},
            {"customer": "CloudFirst", "metric": "uptime", "target": 99.9, "penalty": 10}
        ]
        
        for sla in sla_data:
            self.execute_query("""
                MATCH (c:Customer {name: $customer})
                CREATE (s:SLA {
                    metric: $metric,
                    target: $target,
                    penalty_percentage: $penalty,
                    measurement_period: 'monthly',
                    effective_date: date('2025-01-01')
                })
                CREATE (c)-[:HAS_SLA]->(s)
            """, sla)
        
        # Commitments
        commitments = [
            {
                "customer": "TechCorp",
                "commitments": [
                    {"description": "Multi-region deployment by Q2", "due_date": "2025-06-30", "status": "on_track"},
                    {"description": "Custom API integration", "due_date": "2025-04-30", "status": "at_risk"}
                ]
            },
            {
                "customer": "FinanceHub",
                "commitments": [
                    {"description": "Compliance reporting features", "due_date": "2025-05-31", "status": "on_track"},
                    {"description": "Advanced encryption implementation", "due_date": "2025-07-31", "status": "planned"}
                ]
            },
            {
                "customer": "EduTech",
                "commitments": [
                    {"description": "Performance improvements", "due_date": "2025-03-31", "status": "at_risk"},
                    {"description": "User interface redesign", "due_date": "2025-08-31", "status": "planned"}
                ]
            }
        ]
        
        for customer_commit in commitments:
            for commit in customer_commit["commitments"]:
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})
                    CREATE (cm:Commitment {
                        description: $description,
                        due_date: date($due_date),
                        status: $status,
                        created_date: date('2025-01-01')
                    })
                    CREATE (c)-[:HAS_COMMITMENT]->(cm)
                    
                    // Link to roadmap items if relevant
                    WITH cm
                    MATCH (ri:RoadmapItem)
                    WHERE ri.title CONTAINS $keyword
                    CREATE (cm)-[:DEPENDS_ON]->(ri)
                """, {
                    "customer": customer_commit["customer"],
                    "description": commit["description"],
                    "due_date": commit["due_date"],
                    "status": commit["status"],
                    "keyword": commit["description"].split()[0]  # Simple keyword matching
                })
        
        print("✓ Added SLA and commitments")
    
    def add_financial_data(self):
        """Add operational costs and profitability data"""
        print("\n7. Adding financial data...")
        
        # Operational costs per product
        operational_costs = [
            {
                "product": "SpyroCloud",
                "costs": [
                    {"category": "infrastructure", "amount": 800000, "period": "monthly"},
                    {"category": "support", "amount": 200000, "period": "monthly"},
                    {"category": "development", "amount": 500000, "period": "monthly"}
                ]
            },
            {
                "product": "SpyroAI",
                "costs": [
                    {"category": "compute", "amount": 600000, "period": "monthly"},
                    {"category": "research", "amount": 400000, "period": "monthly"},
                    {"category": "licensing", "amount": 150000, "period": "monthly"}
                ]
            },
            {
                "product": "SpyroSecure",
                "costs": [
                    {"category": "security_ops", "amount": 300000, "period": "monthly"},
                    {"category": "compliance", "amount": 200000, "period": "monthly"},
                    {"category": "infrastructure", "amount": 250000, "period": "monthly"}
                ]
            }
        ]
        
        for product_cost in operational_costs:
            total_cost = sum(cost["amount"] for cost in product_cost["costs"])
            
            # Create operational costs
            for cost in product_cost["costs"]:
                self.execute_query("""
                    MATCH (p:Product {name: $product})
                    CREATE (oc:OperationalCost {
                        category: $category,
                        amount: $amount,
                        period: $period,
                        last_updated: date()
                    })
                    CREATE (p)-[:HAS_COST]->(oc)
                """, {
                    "product": product_cost["product"],
                    "category": cost["category"],
                    "amount": cost["amount"],
                    "period": cost["period"]
                })
            
            # Calculate and create profitability
            self.execute_query("""
                MATCH (p:Product {name: $product})
                MATCH (p)<-[:USES]-(c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)
                WITH p, SUM(toFloat(replace(replace(s.value, '$', ''), 'M', '')) * 1000000) as revenue
                CREATE (prof:Profitability {
                    revenue: revenue,
                    cost: $total_cost * 12,  // Annual cost
                    margin: (revenue - ($total_cost * 12)) / revenue,
                    period: 'annual',
                    last_calculated: date()
                })
                CREATE (p)-[:HAS_PROFITABILITY]->(prof)
            """, {
                "product": product_cost["product"],
                "total_cost": total_cost
            })
        
        # Link operational costs to teams
        self.execute_query("""
            MATCH (t:Team {name: 'CloudOps'})
            MATCH (oc:OperationalCost)
            WHERE oc.category IN ['infrastructure', 'support']
            CREATE (t)-[:INCURS_COST]->(oc)
        """)
        
        self.execute_query("""
            MATCH (t:Team {name: 'AI Research'})
            MATCH (oc:OperationalCost)
            WHERE oc.category IN ['research', 'compute']
            CREATE (t)-[:INCURS_COST]->(oc)
        """)
        
        self.execute_query("""
            MATCH (t:Team {name: 'Security'})
            MATCH (oc:OperationalCost)
            WHERE oc.category IN ['security_ops', 'compliance']
            CREATE (t)-[:INCURS_COST]->(oc)
        """)
        
        print("✓ Added financial data")
    
    def create_additional_relationships(self):
        """Create additional relationships for better connectivity"""
        print("\n8. Creating additional relationships...")
        
        # Link events to risks
        self.execute_query("""
            MATCH (e:Event)
            WHERE e.impact = 'negative' AND e.severity IN ['high', 'critical']
            MATCH (r:Risk)
            WHERE r.type = 'churn'
            CREATE (e)-[:CONTRIBUTES_TO]->(r)
        """)
        
        # Link commitments to roadmap items
        self.execute_query("""
            MATCH (c:Commitment)
            WHERE c.status = 'at_risk'
            MATCH (ri:RoadmapItem)
            WHERE ri.status = 'behind_schedule'
            AND NOT EXISTS((c)-[:DEPENDS_ON]->(ri))
            CREATE (c)-[:DEPENDS_ON]->(ri)
        """)
        
        # Link profitability to objectives
        self.execute_query("""
            MATCH (p:Profitability)
            MATCH (o:Objective)
            WHERE o.title CONTAINS 'Revenue' OR o.title CONTAINS 'Growth'
            CREATE (p)-[:IMPACTS]->(o)
        """)
        
        print("✓ Created additional relationships")
    
    def verify_data_completeness(self):
        """Verify that all data gaps have been filled"""
        print("\n9. Verifying data completeness...")
        
        checks = [
            ("Customers with varied success scores", 
             "MATCH (css:CustomerSuccessScore) WHERE css.score < 70 RETURN count(css) as count"),
            ("Events with timestamps", 
             "MATCH (e:Event) WHERE e.timestamp IS NOT NULL RETURN count(e) as count"),
            ("RoadmapItem nodes", 
             "MATCH (ri:RoadmapItem) RETURN count(ri) as count"),
            ("Risk profiles", 
             "MATCH (r:Risk) RETURN count(r) as count"),
            ("SLA relationships", 
             "MATCH ()-[:HAS_SLA]->() RETURN count(*) as count"),
            ("Operational costs", 
             "MATCH (oc:OperationalCost) RETURN count(oc) as count"),
            ("Profitability data", 
             "MATCH (p:Profitability) RETURN count(p) as count"),
            ("Customer commitments", 
             "MATCH (c:Commitment) RETURN count(c) as count")
        ]
        
        all_good = True
        for check_name, query in checks:
            result = self.execute_query(query)
            count = result[0]['count'] if result else 0
            status = "✓" if count > 0 else "✗"
            print(f"  {status} {check_name}: {count}")
            if count == 0:
                all_good = False
        
        if all_good:
            print("\n✅ All data gaps have been successfully filled!")
        else:
            print("\n⚠️  Some data gaps remain. Please check the output above.")
        
        return all_good


def main():
    print("SpyroSolutions Data Gap Filler")
    print("==============================")
    print("This script will add all missing data identified in the gap analysis.")
    print()
    
    filler = DataGapsFiller()
    
    try:
        # Optional: Clear existing incomplete data
        # filler.clear_existing_data()
        
        # Fill all data gaps
        filler.add_missing_properties()
        filler.create_diverse_customers()
        filler.add_events_with_timestamps()
        filler.add_roadmap_items()
        filler.add_risk_profiles()
        filler.add_sla_and_commitments()
        filler.add_financial_data()
        filler.create_additional_relationships()
        
        # Verify completeness
        success = filler.verify_data_completeness()
        
        if success:
            print("\n🎉 Database enrichment complete! The system now has:")
            print("  - Diverse customer profiles with varying success scores")
            print("  - Time-series events with timestamps")
            print("  - Complete roadmap items with status tracking")
            print("  - Risk profiles for customers and objectives")
            print("  - SLA and commitment tracking")
            print("  - Financial data including costs and profitability")
            print("\nThe SpyroSolutions Agentic RAG system is now ready for comprehensive testing!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        filler.close()


if __name__ == "__main__":
    main()