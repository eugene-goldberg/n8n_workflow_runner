#!/usr/bin/env python3
"""Add comprehensive financial relationships to Neo4j for better query support"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from datetime import datetime, timedelta
import random
from config.settings import settings

class FinancialDataEnhancer:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
        self.stats = {
            'relationships_created': 0,
            'properties_added': 0,
            'nodes_created': 0
        }
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def add_customer_subscriptions_and_revenue(self):
        """Ensure all customers have proper subscription and revenue relationships"""
        print("\n1. Adding Customer Subscriptions and Revenue...")
        
        # Get all customers
        query = """
        MATCH (c:__Entity__:CUSTOMER)
        WHERE NOT (c)-[:PAYS]->()
        RETURN c.name as name, c
        """
        customers_without_subs = self.run_query(query)
        
        subscription_plans = [
            ('Enterprise', 50000, 100000),
            ('Professional', 10000, 50000),
            ('Business', 5000, 10000),
            ('Starter', 1000, 5000)
        ]
        
        for record in customers_without_subs:
            # Select subscription plan based on some logic
            plan_name, min_amount, max_amount = random.choice(subscription_plans)
            monthly_amount = random.randint(min_amount, max_amount)
            
            create_query = """
            MATCH (c:__Entity__:CUSTOMER {name: $name})
            CREATE (s:__Entity__:SUBSCRIPTION {
                plan: $plan,
                amount: $amount,
                value: $amount,
                billing_cycle: 'monthly',
                start_date: datetime() - duration({days: $days_active}),
                status: 'active',
                id: randomUUID()
            })
            CREATE (c)-[:PAYS]->(s)
            CREATE (r:__Entity__:REVENUE {
                amount: $annual_amount,
                type: 'recurring',
                period: 'annual',
                source: 'subscription',
                id: randomUUID()
            })
            CREATE (s)-[:GENERATES]->(r)
            """
            
            days_active = random.randint(90, 730)  # 3 months to 2 years
            self.run_query(create_query, {
                'name': record['name'],
                'plan': plan_name,
                'amount': monthly_amount,
                'annual_amount': monthly_amount * 12,
                'days_active': days_active
            })
            self.stats['nodes_created'] += 2
            self.stats['relationships_created'] += 2
            print(f"  Created {plan_name} subscription (${monthly_amount:,}/mo) for {record['name']}")
    
    def add_team_operational_costs(self):
        """Add operational costs to teams"""
        print("\n2. Adding Team Operational Costs...")
        
        # Get all teams
        query = """
        MATCH (t:__Entity__:TEAM)
        WHERE NOT (t)-[:HAS_COST]->()
        RETURN t.name as name, t
        """
        teams = self.run_query(query)
        
        # Cost ranges by team type
        cost_ranges = {
            'Engineering': (200000, 500000),
            'Sales': (150000, 300000),
            'Marketing': (100000, 250000),
            'Support': (80000, 200000),
            'Operations': (120000, 300000),
            'Product': (150000, 350000),
            'Security': (180000, 400000),
            'Data': (200000, 450000),
            'Cloud': (250000, 500000),
            'AI': (300000, 600000)
        }
        
        for record in teams:
            team_name = record['name']
            # Determine team type from name
            team_type = None
            for key in cost_ranges:
                if key.lower() in team_name.lower():
                    team_type = key
                    break
            
            if not team_type:
                team_type = 'Operations'  # Default
            
            min_cost, max_cost = cost_ranges[team_type]
            annual_cost = random.randint(min_cost, max_cost)
            
            # Add team member count if not exists
            member_count = random.randint(3, 15)
            update_query = """
            MATCH (t:__Entity__:TEAM {name: $name})
            SET t.member_count = coalesce(t.member_count, $member_count)
            """
            self.run_query(update_query, {'name': team_name, 'member_count': member_count})
            
            create_query = """
            MATCH (t:__Entity__:TEAM {name: $name})
            CREATE (cost:__Entity__:OPERATIONAL_COST {
                amount: $amount,
                type: 'team_operational',
                category: 'personnel',
                period: 'annual',
                id: randomUUID()
            })
            CREATE (t)-[:HAS_COST]->(cost)
            """
            
            self.run_query(create_query, {
                'name': team_name,
                'amount': annual_cost
            })
            self.stats['nodes_created'] += 1
            self.stats['relationships_created'] += 1
            self.stats['properties_added'] += 1
            print(f"  Added operational cost ${annual_cost:,} for {team_name} ({member_count} members)")
    
    def add_product_customer_relationships(self):
        """Ensure customers are linked to products they use"""
        print("\n3. Linking Customers to Products...")
        
        # Get customers without product relationships
        query = """
        MATCH (c:__Entity__:CUSTOMER)
        WHERE NOT (c)-[:USES]->()
        RETURN c.name as name
        """
        customers = self.run_query(query)
        
        # Get all products
        products_query = """
        MATCH (p:__Entity__:PRODUCT)
        RETURN p.name as name
        """
        products = self.run_query(products_query)
        product_names = [p['name'] for p in products]
        
        if not product_names:
            print("  No products found, skipping...")
            return
        
        for record in customers:
            # Each customer uses 1-3 products
            num_products = min(random.randint(1, 3), len(product_names))
            selected_products = random.sample(product_names, num_products)
            
            for product_name in selected_products:
                create_query = """
                MATCH (c:__Entity__:CUSTOMER {name: $customer_name})
                MATCH (p:__Entity__:PRODUCT {name: $product_name})
                CREATE (c)-[:USES]->(p)
                """
                self.run_query(create_query, {
                    'customer_name': record['name'],
                    'product_name': product_name
                })
                self.stats['relationships_created'] += 1
            
            print(f"  Linked {record['name']} to {num_products} products")
    
    def add_historical_revenue_data(self):
        """Add historical revenue for growth calculations"""
        print("\n4. Adding Historical Revenue Data...")
        
        # Get all customers with current revenue
        query = """
        MATCH (c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        RETURN c.name as name, s.amount as current_monthly
        """
        customers = self.run_query(query)
        
        current_year = datetime.now().year
        
        for record in customers:
            # Calculate last year's revenue (80-120% of current)
            growth_factor = random.uniform(0.8, 1.2)
            last_year_monthly = record['current_monthly'] / growth_factor
            
            create_query = """
            MATCH (c:__Entity__:CUSTOMER {name: $name})
            CREATE (hr:__Entity__:HISTORICAL_REVENUE {
                amount: $amount,
                year: $year,
                type: 'subscription',
                id: randomUUID()
            })
            CREATE (c)-[:HAD_REVENUE]->(hr)
            """
            
            self.run_query(create_query, {
                'name': record['name'],
                'amount': last_year_monthly * 12,
                'year': current_year - 1
            })
            self.stats['nodes_created'] += 1
            self.stats['relationships_created'] += 1
            
            growth_percent = (growth_factor - 1) * 100
            print(f"  Added historical revenue for {record['name']} ({growth_percent:+.1f}% growth)")
    
    def add_customer_segments_and_regions(self):
        """Add segment and region data to customers"""
        print("\n5. Adding Customer Segments and Regions...")
        
        segments = ['Enterprise', 'Mid-Market', 'SMB', 'Startup']
        regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
        industries = ['Technology', 'Finance', 'Healthcare', 'Retail', 'Manufacturing', 'Education']
        
        # Get customers without segment/region
        query = """
        MATCH (c:__Entity__:CUSTOMER)
        WHERE c.segment IS NULL OR c.region IS NULL
        RETURN c.name as name, c
        """
        customers = self.run_query(query)
        
        for record in customers:
            update_query = """
            MATCH (c:__Entity__:CUSTOMER {name: $name})
            SET c.segment = coalesce(c.segment, $segment),
                c.region = coalesce(c.region, $region),
                c.industry = coalesce(c.industry, $industry),
                c.size = coalesce(c.size, $segment)
            """
            
            self.run_query(update_query, {
                'name': record['name'],
                'segment': random.choice(segments),
                'region': random.choice(regions),
                'industry': random.choice(industries)
            })
            self.stats['properties_added'] += 4
            print(f"  Updated {record['name']} with segment/region/industry data")
    
    def add_feature_release_dates(self):
        """Add release dates to features for adoption tracking"""
        print("\n6. Adding Feature Release Dates...")
        
        # Get features without release dates
        query = """
        MATCH (f:__Entity__:FEATURE)
        WHERE f.release_date IS NULL
        RETURN f.name as name, f
        """
        features = self.run_query(query)
        
        for record in features:
            # Random release date in last 18 months
            days_ago = random.randint(30, 540)
            
            update_query = """
            MATCH (f:__Entity__:FEATURE {name: $name})
            SET f.release_date = datetime() - duration({days: $days_ago})
            """
            
            self.run_query(update_query, {
                'name': record['name'],
                'days_ago': days_ago
            })
            self.stats['properties_added'] += 1
            
            # Link some customers to use this feature
            if days_ago < 180:  # Recent features
                adopt_query = """
                MATCH (f:__Entity__:FEATURE {name: $feature_name})
                MATCH (c:__Entity__:CUSTOMER)
                WITH f, c, rand() as r
                WHERE r < $adoption_rate
                CREATE (c)-[:USES]->(f)
                """
                adoption_rate = random.uniform(0.1, 0.6)  # 10-60% adoption
                self.run_query(adopt_query, {
                    'feature_name': record['name'],
                    'adoption_rate': adoption_rate
                })
                print(f"  Set release date for {record['name']} ({days_ago} days ago, {adoption_rate*100:.0f}% adoption)")
    
    def add_sla_data(self):
        """Add SLA commitments and performance"""
        print("\n7. Adding SLA Data...")
        
        # Get customers without SLAs
        query = """
        MATCH (c:__Entity__:CUSTOMER)
        WHERE NOT (c)-[:HAS_SLA]->()
        RETURN c.name as name
        LIMIT 15
        """
        customers = self.run_query(query)
        
        sla_metrics = [
            ('uptime', 99.9, 'percentage'),
            ('response_time', 200, 'milliseconds'),
            ('support_response', 4, 'hours'),
            ('data_processing', 99.5, 'percentage')
        ]
        
        for record in customers:
            # Create 1-2 SLAs per customer
            num_slas = random.randint(1, 2)
            selected_metrics = random.sample(sla_metrics, num_slas)
            
            for metric_name, target, unit in selected_metrics:
                # Performance is usually close to target but sometimes misses
                if random.random() < 0.3:  # 30% chance of missing SLA
                    performance = target * random.uniform(0.85, 0.98)
                else:
                    performance = target * random.uniform(0.99, 1.01)
                
                create_query = """
                MATCH (c:__Entity__:CUSTOMER {name: $name})
                CREATE (sla:__Entity__:SLA {
                    metric: $metric,
                    target: $target,
                    performance: $performance,
                    unit: $unit,
                    penalty_percentage: $penalty,
                    last_measured: datetime(),
                    id: randomUUID()
                })
                CREATE (c)-[:HAS_SLA]->(sla)
                """
                
                self.run_query(create_query, {
                    'name': record['name'],
                    'metric': metric_name,
                    'target': target,
                    'performance': performance,
                    'unit': unit,
                    'penalty': random.choice([5, 10, 15])
                })
                self.stats['nodes_created'] += 1
                self.stats['relationships_created'] += 1
                
                status = "✓" if performance >= target else "✗"
                print(f"  Added {metric_name} SLA for {record['name']} {status} ({performance:.2f}/{target})")
    
    def add_project_dependencies(self):
        """Add dependencies between projects and commitments"""
        print("\n8. Adding Project Dependencies...")
        
        # Link roadmap items to commitments
        query = """
        MATCH (ri:__Entity__:ROADMAP_ITEM)
        WHERE ri.status IN ['behind_schedule', 'at_risk']
        MATCH (com:__Entity__:COMMITMENT)
        WHERE com.type = 'feature'
        WITH ri, com, rand() as r
        WHERE r < 0.3
        CREATE (com)-[:DEPENDS_ON]->(ri)
        RETURN count(*) as dependencies_created
        """
        result = self.run_query(query)
        if result:
            count = result[0]['dependencies_created']
            self.stats['relationships_created'] += count
            print(f"  Created {count} commitment-roadmap dependencies")
        
        # Add blocked status to some projects
        block_query = """
        MATCH (p:__Entity__:PROJECT)
        WHERE p.status = 'at_risk' AND rand() < 0.3
        SET p.status = 'blocked',
            p.blocked_by = 'Resource constraints'
        RETURN count(*) as blocked_count
        """
        result = self.run_query(block_query)
        if result:
            count = result[0]['blocked_count']
            self.stats['properties_added'] += count * 2
            print(f"  Marked {count} projects as blocked")
    
    def add_risk_to_objective_relationships(self):
        """Link risks to objectives they threaten"""
        print("\n9. Linking Risks to Objectives...")
        
        # Create some objectives if they don't exist
        objectives = [
            ('$500M revenue by 2027', 'REVENUE', 'critical', 500000000, 350000000),
            ('50% market share', 'MARKET', 'high', 50, 35),
            ('NPS > 70', 'SATISFACTION', 'high', 70, 65),
            ('99.99% uptime', 'OPERATIONAL', 'critical', 99.99, 99.5),
            ('Reduce churn < 5%', 'RETENTION', 'high', 5, 8)
        ]
        
        for name, obj_type, priority, target, current in objectives:
            create_obj_query = """
            MERGE (o:__Entity__:OBJECTIVE {name: $name})
            SET o.type = $type,
                o.priority = $priority,
                o.target_value = $target,
                o.current_value = $current,
                o.id = coalesce(o.id, randomUUID())
            """
            self.run_query(create_obj_query, {
                'name': name,
                'type': obj_type,
                'priority': priority,
                'target': target,
                'current': current
            })
        
        # Link risks to objectives
        link_query = """
        MATCH (r:__Entity__:RISK)
        WHERE r.severity IN ['high', 'critical']
        MATCH (o:__Entity__:OBJECTIVE)
        WITH r, o, rand() as rand_val
        WHERE rand_val < 0.3
        CREATE (o)-[:AT_RISK_FROM]->(r)
        RETURN count(*) as links_created
        """
        result = self.run_query(link_query)
        if result:
            count = result[0]['links_created']
            self.stats['relationships_created'] += count
            print(f"  Created {count} objective-risk relationships")
    
    def print_summary(self):
        """Print summary of changes made"""
        print("\n" + "="*60)
        print("FINANCIAL DATA ENHANCEMENT SUMMARY")
        print("="*60)
        print(f"Nodes created: {self.stats['nodes_created']}")
        print(f"Relationships created: {self.stats['relationships_created']}")
        print(f"Properties added: {self.stats['properties_added']}")
        print("\nFinancial relationships have been enhanced for better query support!")

def main():
    print("=== NEO4J FINANCIAL DATA ENHANCER ===")
    print("Adding comprehensive financial relationships for better query support\n")
    
    enhancer = FinancialDataEnhancer()
    
    try:
        # Run all enhancements
        enhancer.add_customer_subscriptions_and_revenue()
        enhancer.add_team_operational_costs()
        enhancer.add_product_customer_relationships()
        enhancer.add_historical_revenue_data()
        enhancer.add_customer_segments_and_regions()
        enhancer.add_feature_release_dates()
        enhancer.add_sla_data()
        enhancer.add_project_dependencies()
        enhancer.add_risk_to_objective_relationships()
        
        # Print summary
        enhancer.print_summary()
        
    finally:
        enhancer.close()

if __name__ == "__main__":
    main()