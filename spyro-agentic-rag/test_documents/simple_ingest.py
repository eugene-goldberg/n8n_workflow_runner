#!/usr/bin/env python3
"""
Simplified Document Ingestion to Neo4j
Direct ingestion without requiring all implementation modules
"""

import os
import sys
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase
import logging
from datetime import datetime
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleNeo4jIngestion:
    """Direct ingestion of test documents to Neo4j"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.entities = {}
        self.relationships = []
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear existing data"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing database")
    
    def process_customers_csv(self, filepath):
        """Process customers CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} customers")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create customer
                session.run("""
                CREATE (c:Customer {
                    name: $name,
                    industry: $industry,
                    size: $size,
                    region: $region,
                    primary_product: $product
                })
                """, {
                    "name": row['customer_name'],
                    "industry": row['industry'],
                    "size": row['size'],
                    "region": row['region'],
                    "product": row['primary_product']
                })
                
                # Create success score
                session.run("""
                MATCH (c:Customer {name: $name})
                CREATE (css:CustomerSuccessScore {
                    score: $score,
                    trend: $trend,
                    customerId: $name,
                    lastUpdated: datetime()
                })
                CREATE (c)-[:HAS_SUCCESS_SCORE]->(css)
                """, {
                    "name": row['customer_name'],
                    "score": float(row['success_score']),
                    "trend": row['trend']
                })
                
                self.entities[row['customer_name']] = 'Customer'
    
    def process_products_csv(self, filepath):
        """Process products CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} products")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create product
                session.run("""
                CREATE (p:Product {
                    name: $name,
                    type: $type,
                    market_focus: $market,
                    features: $features,
                    sla_uptime_target: $sla,
                    adoption_rate: $adoption
                })
                """, {
                    "name": row['product_name'],
                    "type": row['type'],
                    "market": row['market_focus'],
                    "features": row['features'].split(';'),
                    "sla": float(row['sla_uptime_target']),
                    "adoption": row['adoption_rate']
                })
                
                # Create operational cost
                session.run("""
                MATCH (p:Product {name: $name})
                CREATE (oc:OperationalCost {
                    amount: $amount,
                    period: 'monthly',
                    category: 'total'
                })
                CREATE (p)-[:HAS_COST]->(oc)
                """, {
                    "name": row['product_name'],
                    "amount": float(row['monthly_operational_cost'])
                })
                
                self.entities[row['product_name']] = 'Product'
    
    def process_subscriptions_csv(self, filepath):
        """Process subscriptions CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} subscriptions")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create subscription
                value_str = row['value'].replace('$', '').replace('M', '')
                value_float = float(value_str) * 1000000
                
                session.run("""
                MATCH (c:Customer {name: $customer})
                MATCH (p:Product {name: $product})
                CREATE (s:SaaSSubscription {
                    subscriptionId: $id,
                    value: $value,
                    start_date: date($start),
                    end_date: date($end),
                    status: $status,
                    renewal_probability: $renewal
                })
                CREATE (c)-[:SUBSCRIBES_TO]->(s)
                CREATE (s)-[:FOR_PRODUCT]->(p)
                CREATE (c)-[:USES]->(p)
                CREATE (arr:AnnualRecurringRevenue {
                    amount: $arr_amount,
                    currency: 'USD',
                    period: 'annual'
                })
                CREATE (s)-[:GENERATES]->(arr)
                """, {
                    "id": row['subscription_id'],
                    "customer": row['customer_name'],
                    "product": row['product_name'],
                    "value": row['value'],
                    "start": row['start_date'],
                    "end": row['end_date'],
                    "status": row['status'],
                    "renewal": float(row['renewal_probability']),
                    "arr_amount": value_float
                })
    
    def process_teams_csv(self, filepath):
        """Process teams CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} teams")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create team
                session.run("""
                CREATE (t:Team {
                    name: $name,
                    department: $dept,
                    size: $size,
                    focus_area: $focus
                })
                """, {
                    "name": row['team_name'],
                    "dept": row['department'],
                    "size": int(row['size']),
                    "focus": row['focus_area']
                })
                
                # Link to product if not "All Products"
                if row['supporting_product'] != 'All Products':
                    session.run("""
                    MATCH (t:Team {name: $team})
                    MATCH (p:Product {name: $product})
                    CREATE (t)-[:SUPPORTS]->(p)
                    """, {
                        "team": row['team_name'],
                        "product": row['supporting_product']
                    })
                
                self.entities[row['team_name']] = 'Team'
    
    def process_risks_csv(self, filepath):
        """Process risks CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} risks")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create risk
                session.run("""
                CREATE (r:Risk {
                    riskId: $id,
                    type: $type,
                    severity: $severity,
                    description: $desc,
                    probability: $prob,
                    impact_amount: $impact,
                    status: $status
                })
                """, {
                    "id": row['risk_id'],
                    "type": row['type'],
                    "severity": row['severity'],
                    "desc": row['description'],
                    "prob": float(row['probability']),
                    "impact": float(row['impact_amount']),
                    "status": row['status']
                })
                
                # Link to related entity
                if row['related_entity_type'] == 'Customer':
                    session.run("""
                    MATCH (r:Risk {riskId: $id})
                    MATCH (c:Customer {name: $name})
                    CREATE (c)-[:HAS_RISK]->(r)
                    """, {
                        "id": row['risk_id'],
                        "name": row['related_entity_name']
                    })
    
    def process_roadmap_csv(self, filepath):
        """Process roadmap items CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} roadmap items")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create roadmap item
                session.run("""
                CREATE (ri:RoadmapItem {
                    roadmapId: $id,
                    title: $title,
                    status: $status,
                    estimated_completion: date($completion),
                    priority: $priority
                })
                """, {
                    "id": row['roadmap_id'],
                    "title": row['title'],
                    "status": row['status'],
                    "completion": row['estimated_completion'],
                    "priority": row['priority']
                })
                
                # Link to product
                session.run("""
                MATCH (ri:RoadmapItem {roadmapId: $id})
                MATCH (p:Product {name: $product})
                CREATE (p)-[:HAS_ROADMAP]->(ri)
                """, {
                    "id": row['roadmap_id'],
                    "product": row['product_name']
                })
                
                # Link to team
                session.run("""
                MATCH (ri:RoadmapItem {roadmapId: $id})
                MATCH (t:Team {name: $team})
                CREATE (t)-[:RESPONSIBLE_FOR]->(ri)
                """, {
                    "id": row['roadmap_id'],
                    "team": row['responsible_team']
                })
    
    def process_events_csv(self, filepath):
        """Process events CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} events")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create event
                session.run("""
                CREATE (e:Event {
                    eventId: $id,
                    type: $type,
                    impact: $impact,
                    severity: $severity,
                    description: $desc,
                    timestamp: datetime($timestamp)
                })
                """, {
                    "id": row['event_id'],
                    "type": row['event_type'],
                    "impact": row['impact'],
                    "severity": row['severity'],
                    "desc": row['description'],
                    "timestamp": row['timestamp']
                })
                
                # Link to customer
                session.run("""
                MATCH (e:Event {eventId: $id})
                MATCH (c:Customer {name: $customer})
                MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
                CREATE (css)-[:INFLUENCED_BY]->(e)
                """, {
                    "id": row['event_id'],
                    "customer": row['customer_name']
                })
    
    def process_sla_csv(self, filepath):
        """Process SLA commitments CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} SLAs")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create SLA
                session.run("""
                MATCH (c:Customer {name: $customer})
                CREATE (sla:SLA {
                    slaId: $id,
                    metric: $metric,
                    target: $target,
                    current_performance: $current,
                    penalty_percentage: $penalty,
                    status: $status
                })
                CREATE (c)-[:HAS_SLA]->(sla)
                """, {
                    "id": row['sla_id'],
                    "customer": row['customer_name'],
                    "metric": row['metric'],
                    "target": float(row['target']),
                    "current": float(row['current_performance']),
                    "penalty": float(row['penalty_percentage']),
                    "status": row['status']
                })
    
    def process_commitments_csv(self, filepath):
        """Process customer commitments CSV"""
        df = pd.read_csv(filepath)
        logger.info(f"Processing {len(df)} commitments")
        
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Create commitment
                session.run("""
                MATCH (c:Customer {name: $customer})
                CREATE (cm:Commitment {
                    commitmentId: $id,
                    description: $desc,
                    due_date: date($due),
                    status: $status
                })
                CREATE (c)-[:HAS_COMMITMENT]->(cm)
                """, {
                    "id": row['commitment_id'],
                    "customer": row['customer_name'],
                    "desc": row['description'],
                    "due": row['due_date'],
                    "status": row['status']
                })
                
                # Link to roadmap if specified
                if pd.notna(row.get('dependent_roadmap_item')):
                    session.run("""
                    MATCH (cm:Commitment {commitmentId: $id})
                    MATCH (ri:RoadmapItem {roadmapId: $roadmap})
                    CREATE (cm)-[:DEPENDS_ON]->(ri)
                    """, {
                        "id": row['commitment_id'],
                        "roadmap": row['dependent_roadmap_item']
                    })
    
    def process_text_documents(self, text_dir):
        """Process text documents to create additional nodes"""
        logger.info("Processing text documents")
        
        text_files = list(Path(text_dir).glob("*.txt"))
        
        with self.driver.session() as session:
            for text_file in text_files:
                with open(text_file, 'r') as f:
                    content = f.read()
                
                # Create document node
                session.run("""
                CREATE (d:Document {
                    name: $name,
                    type: 'text',
                    content: $content,
                    created: datetime()
                })
                """, {
                    "name": text_file.name,
                    "content": content[:5000]  # Limit content size
                })
                
                logger.info(f"Processed {text_file.name}")
    
    def create_additional_relationships(self):
        """Create inferred relationships based on data patterns"""
        logger.info("Creating additional relationships")
        
        with self.driver.session() as session:
            # Link risks to objectives based on descriptions
            session.run("""
            CREATE (o1:Objective {
                title: 'Market Expansion',
                description: 'Expand into new markets',
                status: 'In Progress'
            })
            CREATE (o2:Objective {
                title: 'Product Innovation', 
                description: 'Enhance AI capabilities',
                status: 'On Track'
            })
            CREATE (o3:Objective {
                title: 'Customer Retention',
                description: 'Improve customer success',
                status: 'At Risk'
            })
            """)
            
            # Link objectives to risks
            session.run("""
            MATCH (o:Objective {title: 'Market Expansion'})
            MATCH (r:Risk)
            WHERE r.type IN ['market', 'technical']
            CREATE (o)-[:AT_RISK]->(r)
            """)
            
            # Create profitability nodes
            session.run("""
            MATCH (p:Product)
            MATCH (p)-[:HAS_COST]->(oc:OperationalCost)
            MATCH (s:SaaSSubscription)-[:FOR_PRODUCT]->(p)
            MATCH (s)-[:GENERATES]->(arr:AnnualRecurringRevenue)
            WITH p, SUM(oc.amount) * 12 as annual_cost, SUM(arr.amount) as annual_revenue
            CREATE (prof:Profitability {
                revenue: annual_revenue,
                cost: annual_cost,
                margin: (annual_revenue - annual_cost) / annual_revenue,
                period: 'annual'
            })
            CREATE (p)-[:HAS_PROFITABILITY]->(prof)
            """)
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        logger.info("Creating indexes")
        
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX customer_name IF NOT EXISTS FOR (c:Customer) ON (c.name)",
                "CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name)",
                "CREATE INDEX team_name IF NOT EXISTS FOR (t:Team) ON (t.name)",
                "CREATE INDEX risk_id IF NOT EXISTS FOR (r:Risk) ON (r.riskId)",
                "CREATE INDEX roadmap_id IF NOT EXISTS FOR (ri:RoadmapItem) ON (ri.roadmapId)",
                "CREATE INDEX event_id IF NOT EXISTS FOR (e:Event) ON (e.eventId)",
                "CREATE FULLTEXT INDEX document_content IF NOT EXISTS FOR (d:Document) ON EACH [d.content]"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
    
    def verify_ingestion(self):
        """Verify data was loaded correctly"""
        logger.info("\nVerifying ingestion:")
        
        with self.driver.session() as session:
            # Count nodes
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\nNode counts:")
            for record in result:
                print(f"  {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print("\nTop 10 relationship types:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
            
            # Sample queries
            result = session.run("""
                MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
                WHERE css.score < 60
                RETURN c.name as customer, css.score as score
                ORDER BY score
            """)
            
            print("\nAt-risk customers (score < 60):")
            for record in result:
                print(f"  {record['customer']}: {record['score']}")


def main():
    """Main function"""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # Paths
    BASE_DIR = "/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/test_documents"
    CSV_DIR = os.path.join(BASE_DIR, "csv")
    TEXT_DIR = os.path.join(BASE_DIR, "text")
    
    logger.info("Starting document ingestion to Neo4j")
    logger.info("=" * 60)
    
    # Initialize ingestion
    ingestion = SimpleNeo4jIngestion(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Clear database
        ingestion.clear_database()
        
        # Process CSV files
        csv_files = {
            'customers.csv': ingestion.process_customers_csv,
            'products.csv': ingestion.process_products_csv,
            'subscriptions.csv': ingestion.process_subscriptions_csv,
            'teams.csv': ingestion.process_teams_csv,
            'risks.csv': ingestion.process_risks_csv,
            'roadmap_items.csv': ingestion.process_roadmap_csv,
            'events.csv': ingestion.process_events_csv,
            'sla_commitments.csv': ingestion.process_sla_csv,
            'customer_commitments.csv': ingestion.process_commitments_csv
        }
        
        for filename, processor in csv_files.items():
            filepath = os.path.join(CSV_DIR, filename)
            if os.path.exists(filepath):
                processor(filepath)
            else:
                logger.warning(f"File not found: {filename}")
        
        # Process text documents
        ingestion.process_text_documents(TEXT_DIR)
        
        # Create additional relationships
        ingestion.create_additional_relationships()
        
        # Create indexes
        ingestion.create_indexes()
        
        # Verify
        ingestion.verify_ingestion()
        
        logger.info("\n✅ Ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()