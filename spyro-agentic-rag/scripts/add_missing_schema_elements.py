#!/usr/bin/env python3
"""Add missing schema elements identified from failed queries"""

import os
import sys
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from neo4j import GraphDatabase


class SchemaEnhancer:
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
    
    def add_customer_commitments(self):
        """Add customer commitments and promises"""
        print("\n1. Adding Customer Commitments...")
        
        commitments_data = [
            {
                "customer": "TechCorp",
                "features": [
                    {"name": "Multi-region deployment", "status": "delivered", "delivery_date": "2025-03-31"},
                    {"name": "API v2 integration", "status": "in_progress", "expected_date": "2025-04-30"},
                    {"name": "Advanced analytics dashboard", "status": "planned", "expected_date": "2025-06-30"}
                ],
                "concerns": [
                    {"type": "performance", "description": "API response times during peak hours", "priority": "high"},
                    {"type": "feature_gap", "description": "Missing bulk export functionality", "priority": "medium"}
                ]
            },
            {
                "customer": "FinanceHub",
                "features": [
                    {"name": "Compliance reporting", "status": "in_progress", "expected_date": "2025-05-31"},
                    {"name": "Real-time fraud detection", "status": "planned", "expected_date": "2025-07-31"},
                    {"name": "Advanced encryption", "status": "delivered", "delivery_date": "2025-01-15"}
                ],
                "concerns": [
                    {"type": "compliance", "description": "SOC2 certification timeline", "priority": "critical"},
                    {"type": "integration", "description": "Legacy system compatibility", "priority": "high"}
                ]
            },
            {
                "customer": "EduTech",
                "features": [
                    {"name": "Student analytics", "status": "at_risk", "expected_date": "2025-03-31"},
                    {"name": "Mobile app", "status": "planned", "expected_date": "2025-08-31"},
                    {"name": "Bulk user import", "status": "delivered", "delivery_date": "2024-12-01"}
                ],
                "concerns": [
                    {"type": "performance", "description": "System slowness with 10k+ users", "priority": "critical"},
                    {"type": "usability", "description": "Complex UI for non-technical users", "priority": "high"}
                ]
            }
        ]
        
        for customer_data in commitments_data:
            customer = customer_data["customer"]
            
            # Add feature promises
            for feature in customer_data["features"]:
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})
                    CREATE (fp:FeaturePromise {
                        name: $name,
                        status: $status,
                        delivery_date: CASE WHEN $delivery_date IS NOT NULL THEN date($delivery_date) ELSE NULL END,
                        expected_date: CASE WHEN $expected_date IS NOT NULL THEN date($expected_date) ELSE NULL END,
                        created_date: date('2024-10-01')
                    })
                    CREATE (c)-[:HAS_FEATURE_PROMISE]->(fp)
                    
                    // Link to roadmap items if matching
                    WITH fp
                    MATCH (ri:RoadmapItem)
                    WHERE ri.title CONTAINS fp.name OR fp.name CONTAINS ri.title
                    CREATE (fp)-[:DEPENDS_ON]->(ri)
                """, {
                    "customer": customer,
                    "name": feature["name"],
                    "status": feature["status"],
                    "delivery_date": feature.get("delivery_date"),
                    "expected_date": feature.get("expected_date")
                })
            
            # Add customer concerns
            for concern in customer_data["concerns"]:
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})
                    CREATE (cc:CustomerConcern {
                        type: $type,
                        description: $description,
                        priority: $priority,
                        status: 'open',
                        created_date: date(),
                        last_updated: datetime()
                    })
                    CREATE (c)-[:HAS_CONCERN]->(cc)
                    
                    // Link to teams for resolution
                    WITH cc
                    MATCH (t:Team)
                    WHERE (cc.type = 'performance' AND t.name CONTAINS 'Cloud') OR
                          (cc.type = 'compliance' AND t.name CONTAINS 'Security') OR
                          (cc.type = 'feature_gap' AND t.focus_area CONTAINS 'development')
                    CREATE (t)-[:ADDRESSING]->(cc)
                """, {
                    "customer": customer,
                    "type": concern["type"],
                    "description": concern["description"],
                    "priority": concern["priority"]
                })
        
        print("✓ Added customer commitments and concerns")
    
    def add_regional_data(self):
        """Add regional/geographic information"""
        print("\n2. Adding Regional Data...")
        
        # Add regions
        regions = [
            {"name": "North America", "code": "NA", "currency": "USD"},
            {"name": "Europe", "code": "EU", "currency": "EUR"},
            {"name": "Asia Pacific", "code": "APAC", "currency": "USD"},
            {"name": "Latin America", "code": "LATAM", "currency": "USD"}
        ]
        
        for region in regions:
            self.execute_query("""
                CREATE (r:Region {
                    name: $name,
                    code: $code,
                    currency: $currency
                })
            """, region)
        
        # Assign customers to regions
        customer_regions = [
            ("TechCorp", "North America"),
            ("FinanceHub", "North America"),
            ("StartupXYZ", "North America"),
            ("RetailPlus", "Europe"),
            ("HealthNet", "North America"),
            ("EduTech", "Asia Pacific"),
            ("LogiCorp", "Europe"),
            ("MediaFlow", "Europe"),
            ("DataSync", "Asia Pacific"),
            ("CloudFirst", "North America")
        ]
        
        for customer, region in customer_regions:
            self.execute_query("""
                MATCH (c:Customer {name: $customer})
                MATCH (r:Region {name: $region})
                CREATE (c)-[:LOCATED_IN]->(r)
            """, {"customer": customer, "region": region})
        
        # Add regional costs
        regional_costs = [
            ("SpyroCloud", "North America", 0.85),
            ("SpyroCloud", "Europe", 1.15),
            ("SpyroCloud", "Asia Pacific", 1.25),
            ("SpyroAI", "North America", 0.90),
            ("SpyroAI", "Europe", 1.20),
            ("SpyroAI", "Asia Pacific", 1.30),
            ("SpyroSecure", "North America", 0.95),
            ("SpyroSecure", "Europe", 1.10),
            ("SpyroSecure", "Asia Pacific", 1.20)
        ]
        
        for product, region, cost_multiplier in regional_costs:
            self.execute_query("""
                MATCH (p:Product {name: $product})
                MATCH (r:Region {name: $region})
                CREATE (rc:RegionalCost {
                    cost_multiplier: $cost_multiplier,
                    base_cost_per_customer: 1000,
                    effective_date: date('2025-01-01')
                })
                CREATE (p)-[:HAS_REGIONAL_COST]->(rc)-[:IN_REGION]->(r)
            """, {
                "product": product,
                "region": region,
                "cost_multiplier": cost_multiplier
            })
        
        print("✓ Added regional data and costs")
    
    def add_feature_usage_metrics(self):
        """Add feature usage and adoption tracking"""
        print("\n3. Adding Feature Usage Metrics...")
        
        # Add feature usage for each product
        features_usage = [
            {
                "product": "SpyroCloud",
                "features": [
                    {"name": "Auto-scaling", "adoption_rate": 0.85, "value_score": 9.2},
                    {"name": "Multi-region", "adoption_rate": 0.45, "value_score": 8.7},
                    {"name": "API Gateway", "adoption_rate": 0.92, "value_score": 9.5},
                    {"name": "Monitoring Dashboard", "adoption_rate": 0.78, "value_score": 8.0}
                ]
            },
            {
                "product": "SpyroAI",
                "features": [
                    {"name": "Predictive Analytics", "adoption_rate": 0.72, "value_score": 9.3},
                    {"name": "ML Model Training", "adoption_rate": 0.38, "value_score": 8.5},
                    {"name": "Real-time Insights", "adoption_rate": 0.81, "value_score": 9.1},
                    {"name": "Custom Models", "adoption_rate": 0.25, "value_score": 7.8}
                ]
            },
            {
                "product": "SpyroSecure",
                "features": [
                    {"name": "Threat Detection", "adoption_rate": 0.95, "value_score": 9.8},
                    {"name": "Compliance Reports", "adoption_rate": 0.88, "value_score": 9.0},
                    {"name": "Access Control", "adoption_rate": 0.91, "value_score": 9.4},
                    {"name": "Audit Logs", "adoption_rate": 0.76, "value_score": 8.2}
                ]
            }
        ]
        
        for product_data in features_usage:
            for feature in product_data["features"]:
                # Create feature usage metrics
                self.execute_query("""
                    MATCH (p:Product {name: $product})
                    MATCH (f:Feature {name: $feature_name})
                    WHERE (p)-[:HAS_FEATURE]->(f)
                    CREATE (fu:FeatureUsage {
                        adoption_rate: $adoption_rate,
                        value_score: $value_score,
                        active_users: toInteger($adoption_rate * 1000),
                        last_updated: date(),
                        released_date: date() - duration({months: toInteger(rand() * 12)})
                    })
                    CREATE (f)-[:HAS_USAGE]->(fu)
                    
                    // Link high-value features to enterprise customers
                    WITH f, fu
                    WHERE fu.value_score > 9.0
                    MATCH (c:Customer)
                    WHERE c.size = 'Enterprise' OR c.name IN ['TechCorp', 'FinanceHub', 'CloudFirst']
                    CREATE (c)-[:VALUES_FEATURE {score: fu.value_score}]->(f)
                """, {
                    "product": product_data["product"],
                    "feature_name": feature["name"],
                    "adoption_rate": feature["adoption_rate"],
                    "value_score": feature["value_score"]
                })
        
        print("✓ Added feature usage metrics")
    
    def add_sla_history(self):
        """Add historical SLA tracking"""
        print("\n4. Adding SLA History...")
        
        # Add SLA performance history
        customers_with_sla = ["TechCorp", "FinanceHub", "HealthNet", "CloudFirst"]
        
        for customer in customers_with_sla:
            # Create monthly SLA records for last 3 months
            for months_ago in range(3):
                month_date = datetime.now() - timedelta(days=30 * months_ago)
                
                # Simulate SLA performance
                met_sla = random.random() > 0.2  # 80% meet SLA
                uptime = 99.5 + random.random() * 0.5 if met_sla else 98.5 + random.random()
                
                self.execute_query("""
                    MATCH (c:Customer {name: $customer})-[:HAS_SLA]->(sla:SLA)
                    CREATE (sp:SLAPerformance {
                        month: date($month_date),
                        metric: sla.metric,
                        target: sla.target,
                        actual: $actual,
                        met: $met,
                        penalty_applied: CASE WHEN $met = false THEN sla.penalty_percentage ELSE 0 END
                    })
                    CREATE (sla)-[:HAS_PERFORMANCE]->(sp)
                """, {
                    "customer": customer,
                    "month_date": month_date.strftime("%Y-%m-01"),
                    "actual": uptime,
                    "met": met_sla
                })
        
        print("✓ Added SLA history")
    
    def enhance_team_relationships(self):
        """Enhance team relationships for better multi-hop queries"""
        print("\n5. Enhancing Team Relationships...")
        
        # Add team metrics
        team_metrics = [
            ("Cloud Platform Team", {"velocity": 85, "capacity": 20, "utilization": 0.92}),
            ("AI Research Team", {"velocity": 72, "capacity": 15, "utilization": 0.85}),
            ("Security Team", {"velocity": 78, "capacity": 10, "utilization": 0.95})
        ]
        
        for team_name, metrics in team_metrics:
            self.execute_query("""
                MATCH (t:Team {name: $team_name})
                SET t.velocity = $velocity,
                    t.capacity = $capacity,
                    t.utilization = $utilization
            """, {"team_name": team_name, **metrics})
        
        # Link teams to customer success
        self.execute_query("""
            // Teams impact on customer success through resolved issues
            MATCH (t:Team)-[:ADDRESSING]->(cc:CustomerConcern)<-[:HAS_CONCERN]-(c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
            WHERE cc.status = 'resolved'
            CREATE (t)-[:IMPROVES_SUCCESS {impact: 5.0}]->(css)
        """)
        
        # Link teams to revenue through products
        self.execute_query("""
            // Teams supporting high-revenue products
            MATCH (t:Team)-[:SUPPORTS]->(p:Product)<-[:USES]-(c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
            WITH t, sum(arr.amount) as team_revenue
            SET t.revenue_supported = team_revenue
        """)
        
        print("✓ Enhanced team relationships")
    
    def add_project_dependencies(self):
        """Add project dependencies for better project analysis"""
        print("\n6. Adding Project Dependencies...")
        
        # Create project dependencies
        project_deps = [
            ("Cloud Migration", ["API Enhancement", "Infrastructure Upgrade"]),
            ("AI Enhancement", ["ML Pipeline", "Data Platform"]),
            ("Security Audit", ["Compliance Framework", "Access Control Update"])
        ]
        
        for project, dependencies in project_deps:
            for dep in dependencies:
                self.execute_query("""
                    MATCH (p1:Project {name: $project})
                    MERGE (p2:Project {name: $dep, status: 'active'})
                    CREATE (p1)-[:DEPENDS_ON]->(p2)
                """, {"project": project, "dep": dep})
        
        # Link projects to revenue
        self.execute_query("""
            // Projects critical for revenue (supporting customer commitments)
            MATCH (p:Project)<-[:WORKS_ON]-(t:Team)-[:ADDRESSING]->(cc:CustomerConcern)<-[:HAS_CONCERN]-(c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
            WITH p, sum(arr.amount) as revenue_at_risk
            SET p.revenue_impact = revenue_at_risk
        """)
        
        print("✓ Added project dependencies")
    
    def add_competitive_features(self):
        """Add competitive analysis data"""
        print("\n7. Adding Competitive Features...")
        
        # Industry standards
        industry_sla = {
            "cloud_uptime": 99.95,
            "ai_accuracy": 0.92,
            "security_mttr": 4.0  # hours
        }
        
        # Add competitive advantages
        competitive_features = [
            {
                "product": "SpyroCloud",
                "advantages": [
                    {"feature": "Auto-scaling", "vs_industry": "+15% faster", "segment": "Enterprise"},
                    {"feature": "Multi-region", "vs_industry": "3x locations", "segment": "Global"}
                ]
            },
            {
                "product": "SpyroAI",
                "advantages": [
                    {"feature": "Real-time Insights", "vs_industry": "10x faster", "segment": "FinTech"},
                    {"feature": "Custom Models", "vs_industry": "No-code approach", "segment": "SMB"}
                ]
            },
            {
                "product": "SpyroSecure",
                "advantages": [
                    {"feature": "Threat Detection", "vs_industry": "ML-powered", "segment": "Enterprise"},
                    {"feature": "Compliance Reports", "vs_industry": "Auto-generated", "segment": "Healthcare"}
                ]
            }
        ]
        
        for product_data in competitive_features:
            for advantage in product_data["advantages"]:
                self.execute_query("""
                    MATCH (p:Product {name: $product})-[:HAS_FEATURE]->(f:Feature {name: $feature})
                    CREATE (ca:CompetitiveAdvantage {
                        vs_industry: $vs_industry,
                        market_segment: $segment,
                        created_date: date()
                    })
                    CREATE (f)-[:PROVIDES_ADVANTAGE]->(ca)
                    
                    // Link to market segments
                    MERGE (ms:MarketSegment {name: $segment})
                    CREATE (ca)-[:IN_SEGMENT]->(ms)
                """, {
                    "product": product_data["product"],
                    "feature": advantage["feature"],
                    "vs_industry": advantage["vs_industry"],
                    "segment": advantage["segment"]
                })
        
        # Add industry benchmarks
        self.execute_query("""
            CREATE (ib:IndustryBenchmark {
                cloud_uptime_sla: $cloud_uptime,
                ai_accuracy_target: $ai_accuracy,
                security_mttr_hours: $security_mttr,
                updated_date: date()
            })
        """, industry_sla)
        
        print("✓ Added competitive features")
    
    def create_cross_domain_relationships(self):
        """Create relationships that span multiple domains for complex queries"""
        print("\n8. Creating Cross-Domain Relationships...")
        
        # Link operational risks to customer success
        self.execute_query("""
            // Operational risks impact customer success
            MATCH (r:Risk {type: 'operational'})
            MATCH (css:CustomerSuccessScore)
            WHERE css.score < 70
            CREATE (r)-[:IMPACTS_SUCCESS {severity: r.severity}]->(css)
        """)
        
        # Link feature gaps to risks
        self.execute_query("""
            // Missing features create risks
            MATCH (cc:CustomerConcern {type: 'feature_gap'})
            MATCH (c:Customer)-[:HAS_CONCERN]->(cc)
            CREATE (r:Risk {
                type: 'retention',
                severity: cc.priority,
                description: 'Feature gap: ' + cc.description,
                probability: 0.3,
                identified_date: date()
            })
            CREATE (cc)-[:CREATES_RISK]->(r)
            CREATE (c)-[:HAS_RISK]->(r)
        """)
        
        # Link team capacity to delivery risks
        self.execute_query("""
            // Understaffed teams create delivery risks
            MATCH (t:Team)
            WHERE t.utilization > 0.9
            MATCH (p:Project)<-[:WORKS_ON]-(t)
            CREATE (r:Risk {
                type: 'delivery',
                severity: 'high',
                description: 'Team capacity constraint: ' + t.name,
                probability: 0.6,
                identified_date: date()
            })
            CREATE (t)-[:CREATES_RISK]->(r)
            CREATE (p)-[:HAS_RISK]->(r)
        """)
        
        print("✓ Created cross-domain relationships")
    
    def verify_enhancements(self):
        """Verify all enhancements were applied"""
        print("\n9. Verifying Enhancements...")
        
        checks = [
            ("FeaturePromise nodes", "MATCH (fp:FeaturePromise) RETURN count(fp) as count"),
            ("CustomerConcern nodes", "MATCH (cc:CustomerConcern) RETURN count(cc) as count"),
            ("Region nodes", "MATCH (r:Region) RETURN count(r) as count"),
            ("FeatureUsage metrics", "MATCH (fu:FeatureUsage) RETURN count(fu) as count"),
            ("SLAPerformance history", "MATCH (sp:SLAPerformance) RETURN count(sp) as count"),
            ("CompetitiveAdvantage data", "MATCH (ca:CompetitiveAdvantage) RETURN count(ca) as count"),
            ("Cross-domain risks", "MATCH ()-[:CREATES_RISK]->() RETURN count(*) as count"),
            ("Team revenue metrics", "MATCH (t:Team) WHERE EXISTS(t.revenue_supported) RETURN count(t) as count")
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
            print("\n✅ All schema enhancements successfully applied!")
        else:
            print("\n⚠️  Some enhancements may have failed.")
        
        return all_good


def main():
    print("SpyroSolutions Schema Enhancement")
    print("=================================")
    print("Adding missing elements to improve query success rate")
    
    enhancer = SchemaEnhancer()
    
    try:
        enhancer.add_customer_commitments()
        enhancer.add_regional_data()
        enhancer.add_feature_usage_metrics()
        enhancer.add_sla_history()
        enhancer.enhance_team_relationships()
        enhancer.add_project_dependencies()
        enhancer.add_competitive_features()
        enhancer.create_cross_domain_relationships()
        
        success = enhancer.verify_enhancements()
        
        if success:
            print("\n🎉 Schema enhancement complete!")
            print("\nNew capabilities added:")
            print("  - Customer commitments and feature promises tracking")
            print("  - Regional data with cost variations")
            print("  - Feature usage metrics and adoption rates")
            print("  - Historical SLA performance tracking")
            print("  - Enhanced team-revenue relationships")
            print("  - Project dependencies and revenue impact")
            print("  - Competitive advantage analysis")
            print("  - Cross-domain risk relationships")
            print("\nThe system should now handle complex multi-hop queries better!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        enhancer.close()


if __name__ == "__main__":
    main()