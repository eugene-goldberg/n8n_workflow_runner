#!/usr/bin/env python3
"""
Updated SpyroSolutions Semantic Model Implementation v2
Addresses all gaps identified when comparing with the semantic model diagram
"""

import asyncio
import logging
import os
from typing import List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

import neo4j
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import HybridRetriever, HybridCypherRetriever

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Updated Schema Definition based on the Semantic Model
ENTITY_TYPES = [
    # Core Business Entities
    {"label": "Product", "description": "Product or service offering"},
    {"label": "Customer", "description": "Customer organization"},
    {"label": "Project", "description": "Development project or initiative"},
    {"label": "Team", "description": "Internal team or department"},
    {"label": "SaaSSubscription", "description": "Software as a Service subscription"},
    {"label": "Risk", "description": "Business or operational risk"},
    
    # Metrics and Measurements
    {"label": "SLA", "description": "Service Level Agreement"},
    {"label": "OperationalStatistics", "description": "Operational metrics and KPIs"},
    {"label": "Roadmap", "description": "Product or project roadmap"},
    {"label": "Feature", "description": "Product feature or capability"},
    {"label": "AnnualRecurringRevenue", "description": "Annual Recurring Revenue metric"},  # Now a separate entity
    {"label": "CustomerSuccessScore", "description": "Customer satisfaction metric"},
    
    # Financial and Strategic
    {"label": "OperationalCost", "description": "Cost of operations"},
    {"label": "Profitability", "description": "Financial profitability metric"},
    {"label": "CompanyObjective", "description": "Strategic company goal"},
    {"label": "Event", "description": "Events affecting customer success"}
]

RELATIONSHIP_TYPES = [
    # Product relationships
    {"label": "HAS_SLA", "description": "Product has SLA commitment"},
    {"label": "HAS_OPERATIONAL_STATS", "description": "Product has operational statistics"},
    {"label": "HAS_ROADMAP", "description": "Product has development roadmap"},
    {"label": "ASSIGNED_TO_TEAM", "description": "Product assigned to team"},
    {"label": "USED_BY", "description": "Product used by customer"},
    
    # Customer relationships
    {"label": "SUBSCRIBES_TO", "description": "Customer has SaaS subscription"},
    {"label": "HAS_SUCCESS_SCORE", "description": "Customer has success score"},
    {"label": "AFFECTED_BY_EVENT", "description": "Customer affected by event"},
    {"label": "HAS_RISK", "description": "Customer has associated risk"},
    
    # Project relationships
    {"label": "DELIVERS_FEATURE", "description": "Project delivers feature"},
    {"label": "HAS_OPERATIONAL_COST", "description": "Project has operational cost"},
    {"label": "CONTRIBUTES_TO_PROFITABILITY", "description": "Project contributes to profitability"},
    {"label": "SUPPORTS_OBJECTIVE", "description": "Project supports company objective"},
    
    # Financial relationships (UPDATED)
    {"label": "GENERATES", "description": "Subscription generates ARR"},  # Changed from GENERATES_ARR
    {"label": "AFFECTS", "description": "Cost affects profitability"},  # NEW
    {"label": "SUPPORTS", "description": "Profitability supports objective"},  # NEW
    {"label": "IMPACTS", "description": "Risk impacts objective or customer"},  # UPDATED
    
    # Feature relationships
    {"label": "COMMITTED_TO", "description": "Feature committed to customer"},  # Simplified
    {"label": "PART_OF", "description": "Feature part of project or roadmap"},  # NEW/UPDATED
    {"label": "HAS_FEATURE", "description": "Roadmap has feature"},
    
    # Score relationships (NEW)
    {"label": "INFLUENCED_BY", "description": "Score influenced by events"}  # NEW
]


class SpyroRAGSystemV2:
    """Updated SpyroSolutions RAG System with complete semantic model"""
    
    def __init__(self):
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={"temperature": 0}
        )
        self.embedder = OpenAIEmbeddings()
        
    async def clean_database(self):
        """Clean existing data from Neo4j"""
        with self.driver.session() as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleaned")
            
    async def create_schema_and_data(self):
        """Create the complete schema with all entities and relationships"""
        with self.driver.session() as session:
            # Create Products
            session.run("""
                CREATE (p1:Product {name: 'SpyroCloud Platform', description: 'Enterprise cloud infrastructure'})
                CREATE (p2:Product {name: 'SpyroAI Analytics', description: 'AI-powered business intelligence'})
                CREATE (p3:Product {name: 'SpyroSecure', description: 'Enterprise security suite'})
            """)
            
            # Create Teams
            session.run("""
                CREATE (t1:Team {name: 'Platform Engineering Team', size: 45})
                CREATE (t2:Team {name: 'AI/ML Team', size: 30})
                CREATE (t3:Team {name: 'Security Team', size: 25})
            """)
            
            # Create SLAs
            session.run("""
                CREATE (sla1:SLA {metric: 'Uptime', guarantee: '99.99%'})
                CREATE (sla2:SLA {metric: 'Query Response', guarantee: '<2 seconds'})
                CREATE (sla3:SLA {metric: 'Threat Detection', guarantee: '99.99%'})
            """)
            
            # Create Operational Statistics
            session.run("""
                CREATE (os1:OperationalStatistics {metric: 'Actual Uptime', value: '99.96%'})
                CREATE (os2:OperationalStatistics {metric: 'Avg Query Time', value: '1.8s'})
                CREATE (os3:OperationalStatistics {metric: 'Detection Rate', value: '99.97%'})
            """)
            
            # Create Customers
            session.run("""
                CREATE (c1:Customer {name: 'TechCorp Industries', industry: 'Technology'})
                CREATE (c2:Customer {name: 'GlobalBank Financial', industry: 'Finance'})
                CREATE (c3:Customer {name: 'RetailMax Corporation', industry: 'Retail'})
            """)
            
            # Create SaaS Subscriptions
            session.run("""
                CREATE (s1:SaaSSubscription {plan: 'Enterprise Plus', period: 'Annual'})
                CREATE (s2:SaaSSubscription {plan: 'Premium Security', period: 'Annual'})
                CREATE (s3:SaaSSubscription {plan: 'Analytics Pro', period: 'Annual'})
            """)
            
            # Create Annual Recurring Revenue (NEW - as separate entities)
            session.run("""
                CREATE (arr1:AnnualRecurringRevenue {amount: '$5M', year: 2024})
                CREATE (arr2:AnnualRecurringRevenue {amount: '$8M', year: 2024})
                CREATE (arr3:AnnualRecurringRevenue {amount: '$3M', year: 2024})
            """)
            
            # Create Customer Success Scores
            session.run("""
                CREATE (css1:CustomerSuccessScore {score: 92, health_status: 'Healthy'})
                CREATE (css2:CustomerSuccessScore {score: 95, health_status: 'Very Healthy'})
                CREATE (css3:CustomerSuccessScore {score: 78, health_status: 'At Risk'})
            """)
            
            # Create Risks
            session.run("""
                CREATE (r1:Risk {level: 'Medium', type: 'Churn Risk', description: 'Considering competitive solutions'})
                CREATE (r2:Risk {level: 'Low', type: 'Expansion Risk', description: 'Very satisfied, expanding usage'})
                CREATE (r3:Risk {level: 'High', type: 'Satisfaction Risk', description: 'Feature gaps affecting satisfaction'})
            """)
            
            # Create Events
            session.run("""
                CREATE (e1:Event {type: 'Outage', date: '2023-Q4', impact: 'Major operations affected'})
                CREATE (e2:Event {type: 'Migration', date: '2023-Q3', impact: 'Successfully migrated 500TB'})
                CREATE (e3:Event {type: 'Delayed Delivery', date: '2024-Q1', impact: 'Feature delivery delayed'})
            """)
            
            # Create Projects
            session.run("""
                CREATE (proj1:Project {name: 'Project Titan', status: 'Active'})
                CREATE (proj2:Project {name: 'Project Mercury', status: 'Active'})
                CREATE (proj3:Project {name: 'Project Apollo', status: 'Planning'})
            """)
            
            # Create Features
            session.run("""
                CREATE (f1:Feature {name: 'Multi-region deployment', priority: 'High'})
                CREATE (f2:Feature {name: 'Enhanced security features', priority: 'High'})
                CREATE (f3:Feature {name: 'Natural language queries', priority: 'Medium'})
                CREATE (f4:Feature {name: 'Custom dashboards', priority: 'Medium'})
                CREATE (f5:Feature {name: 'Edge computing capabilities', priority: 'High'})
            """)
            
            # Create Roadmaps
            session.run("""
                CREATE (rm1:Roadmap {name: 'SpyroCloud 2024 Roadmap', quarter: 'Q1-Q2 2024'})
                CREATE (rm2:Roadmap {name: 'SpyroAI 2024 Roadmap', quarter: 'Q1-Q2 2024'})
            """)
            
            # Create Operational Costs
            session.run("""
                CREATE (oc1:OperationalCost {cost: '$2.5M', category: 'Development'})
                CREATE (oc2:OperationalCost {cost: '$1.8M', category: 'Development'})
                CREATE (oc3:OperationalCost {cost: '$3.2M', category: 'Innovation'})
            """)
            
            # Create Profitability
            session.run("""
                CREATE (p1:Profitability {impact: '+$15M ARR', margin: '60%'})
                CREATE (p2:Profitability {impact: '+$8M ARR', margin: '55%'})
                CREATE (p3:Profitability {impact: '+$20M ARR', margin: '65%'})
            """)
            
            # Create Company Objectives
            session.run("""
                CREATE (co1:CompanyObjective {name: 'Global Expansion', target: '50% international revenue by 2025'})
                CREATE (co2:CompanyObjective {name: 'AI Leadership', target: '#1 in AI-powered business analytics'})
                CREATE (co3:CompanyObjective {name: 'Innovation Excellence', target: '40% revenue from new products'})
            """)
            
            logger.info("All entities created")
            
    async def create_relationships(self):
        """Create all relationships according to the semantic model"""
        with self.driver.session() as session:
            # Product relationships
            session.run("""
                MATCH (p:Product {name: 'SpyroCloud Platform'}), (t:Team {name: 'Platform Engineering Team'})
                CREATE (p)-[:ASSIGNED_TO_TEAM]->(t)
            """)
            
            session.run("""
                MATCH (p:Product {name: 'SpyroAI Analytics'}), (t:Team {name: 'AI/ML Team'})
                CREATE (p)-[:ASSIGNED_TO_TEAM]->(t)
            """)
            
            session.run("""
                MATCH (p:Product {name: 'SpyroSecure'}), (t:Team {name: 'Security Team'})
                CREATE (p)-[:ASSIGNED_TO_TEAM]->(t)
            """)
            
            # Product-SLA relationships
            session.run("""
                MATCH (p:Product {name: 'SpyroCloud Platform'}), (sla:SLA {metric: 'Uptime'})
                CREATE (p)-[:HAS_SLA]->(sla)
            """)
            
            # Product-Operational Stats relationships
            session.run("""
                MATCH (p:Product {name: 'SpyroCloud Platform'}), (os:OperationalStatistics {metric: 'Actual Uptime'})
                CREATE (p)-[:HAS_OPERATIONAL_STATS]->(os)
            """)
            
            # Product-Roadmap relationships
            session.run("""
                MATCH (p:Product {name: 'SpyroCloud Platform'}), (rm:Roadmap {name: 'SpyroCloud 2024 Roadmap'})
                CREATE (p)-[:HAS_ROADMAP]->(rm)
            """)
            
            session.run("""
                MATCH (p:Product {name: 'SpyroAI Analytics'}), (rm:Roadmap {name: 'SpyroAI 2024 Roadmap'})
                CREATE (p)-[:HAS_ROADMAP]->(rm)
            """)
            
            # Roadmap-Feature relationships
            session.run("""
                MATCH (rm:Roadmap {name: 'SpyroCloud 2024 Roadmap'}), (f:Feature {name: 'Multi-region deployment'})
                CREATE (rm)-[:HAS_FEATURE]->(f)
            """)
            
            session.run("""
                MATCH (rm:Roadmap {name: 'SpyroCloud 2024 Roadmap'}), (f:Feature {name: 'Edge computing capabilities'})
                CREATE (rm)-[:HAS_FEATURE]->(f)
            """)
            
            # Customer-Product relationships
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (p:Product {name: 'SpyroCloud Platform'})
                CREATE (p)-[:USED_BY]->(c)
            """)
            
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (p:Product {name: 'SpyroAI Analytics'})
                CREATE (p)-[:USED_BY]->(c)
            """)
            
            # Customer-Subscription relationships
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (s:SaaSSubscription {plan: 'Enterprise Plus'})
                CREATE (c)-[:SUBSCRIBES_TO]->(s)
            """)
            
            session.run("""
                MATCH (c:Customer {name: 'GlobalBank Financial'}), (s:SaaSSubscription {plan: 'Premium Security'})
                CREATE (c)-[:SUBSCRIBES_TO]->(s)
            """)
            
            # Subscription-ARR relationships (NEW)
            session.run("""
                MATCH (s:SaaSSubscription {plan: 'Enterprise Plus'}), (arr:AnnualRecurringRevenue {amount: '$5M'})
                CREATE (s)-[:GENERATES]->(arr)
            """)
            
            session.run("""
                MATCH (s:SaaSSubscription {plan: 'Premium Security'}), (arr:AnnualRecurringRevenue {amount: '$8M'})
                CREATE (s)-[:GENERATES]->(arr)
            """)
            
            # Customer-Success Score relationships
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (css:CustomerSuccessScore {score: 92})
                CREATE (c)-[:HAS_SUCCESS_SCORE]->(css)
            """)
            
            # Customer-Risk relationships
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (r:Risk {level: 'Medium'})
                CREATE (c)-[:HAS_RISK]->(r)
            """)
            
            # Customer-Event relationships
            session.run("""
                MATCH (c:Customer {name: 'TechCorp Industries'}), (e:Event {type: 'Outage'})
                CREATE (c)-[:AFFECTED_BY_EVENT]->(e)
            """)
            
            # Success Score-Event relationships (NEW)
            session.run("""
                MATCH (css:CustomerSuccessScore {score: 92}), (e:Event {type: 'Outage'})
                CREATE (css)-[:INFLUENCED_BY]->(e)
            """)
            
            session.run("""
                MATCH (css:CustomerSuccessScore {score: 78}), (e:Event {type: 'Delayed Delivery'})
                CREATE (css)-[:INFLUENCED_BY]->(e)
            """)
            
            # Project-Feature relationships
            session.run("""
                MATCH (proj:Project {name: 'Project Titan'}), (f:Feature {name: 'Multi-region deployment'})
                CREATE (proj)-[:DELIVERS_FEATURE]->(f)
            """)
            
            session.run("""
                MATCH (proj:Project {name: 'Project Titan'}), (f:Feature {name: 'Enhanced security features'})
                CREATE (proj)-[:DELIVERS_FEATURE]->(f)
            """)
            
            # Feature-Project relationships (NEW)
            session.run("""
                MATCH (f:Feature {name: 'Multi-region deployment'}), (proj:Project {name: 'Project Titan'})
                CREATE (f)-[:PART_OF]->(proj)
            """)
            
            # Feature-Customer relationships
            session.run("""
                MATCH (f:Feature {name: 'Multi-region deployment'}), (c:Customer {name: 'GlobalBank Financial'})
                CREATE (f)-[:COMMITTED_TO]->(c)
            """)
            
            session.run("""
                MATCH (f:Feature {name: 'Natural language queries'}), (c:Customer {name: 'RetailMax Corporation'})
                CREATE (f)-[:COMMITTED_TO]->(c)
            """)
            
            # Project-Cost relationships
            session.run("""
                MATCH (proj:Project {name: 'Project Titan'}), (oc:OperationalCost {cost: '$2.5M'})
                CREATE (proj)-[:HAS_OPERATIONAL_COST]->(oc)
            """)
            
            # Project-Profitability relationships
            session.run("""
                MATCH (proj:Project {name: 'Project Titan'}), (p:Profitability {impact: '+$15M ARR'})
                CREATE (proj)-[:CONTRIBUTES_TO_PROFITABILITY]->(p)
            """)
            
            # Cost-Profitability relationships (NEW)
            session.run("""
                MATCH (oc:OperationalCost {cost: '$2.5M'}), (p:Profitability {impact: '+$15M ARR'})
                CREATE (oc)-[:AFFECTS]->(p)
            """)
            
            session.run("""
                MATCH (oc:OperationalCost {cost: '$1.8M'}), (p:Profitability {impact: '+$8M ARR'})
                CREATE (oc)-[:AFFECTS]->(p)
            """)
            
            # Profitability-Objective relationships (NEW)
            session.run("""
                MATCH (p:Profitability {impact: '+$15M ARR'}), (co:CompanyObjective {name: 'Global Expansion'})
                CREATE (p)-[:SUPPORTS]->(co)
            """)
            
            session.run("""
                MATCH (p:Profitability {impact: '+$8M ARR'}), (co:CompanyObjective {name: 'AI Leadership'})
                CREATE (p)-[:SUPPORTS]->(co)
            """)
            
            # Risk-Objective relationships (NEW)
            session.run("""
                MATCH (r:Risk {type: 'Churn Risk'}), (co:CompanyObjective {name: 'Global Expansion'})
                CREATE (r)-[:IMPACTS]->(co)
            """)
            
            session.run("""
                MATCH (r:Risk {type: 'Satisfaction Risk'}), (co:CompanyObjective {name: 'AI Leadership'})
                CREATE (r)-[:IMPACTS]->(co)
            """)
            
            logger.info("All relationships created according to semantic model")
            
    async def create_indexes(self):
        """Create indexes for better performance"""
        with self.driver.session() as session:
            # Create indexes for frequently queried properties
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (proj:Project) ON (proj.name)",
                "CREATE INDEX IF NOT EXISTS FOR (t:Team) ON (t.name)",
                "CREATE INDEX IF NOT EXISTS FOR (f:Feature) ON (f.name)",
                "CREATE INDEX IF NOT EXISTS FOR (s:SaaSSubscription) ON (s.plan)",
                "CREATE INDEX IF NOT EXISTS FOR (r:Risk) ON (r.level)",
                "CREATE INDEX IF NOT EXISTS FOR (co:CompanyObjective) ON (co.name)"
            ]
            
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation: {e}")
            
            logger.info("Indexes created")
            
    async def create_vector_indexes(self):
        """Create vector and fulltext indexes for RAG"""
        try:
            # Create vector index
            create_vector_index(
                driver=self.driver,
                index_name="spyro_vector_index_v2",
                label="__Chunk__",
                embedding_property="embedding",
                dimensions=1536,
                similarity_fn="cosine"
            )
            
            # Create fulltext index
            create_fulltext_index(
                driver=self.driver,
                index_name="spyro_fulltext_index_v2",
                label="__Chunk__",
                node_properties=["text"]
            )
            
            logger.info("Vector and fulltext indexes created")
        except Exception as e:
            logger.warning(f"Index creation: {e}")
            
    async def initialize(self):
        """Initialize the complete semantic model"""
        await self.clean_database()
        await self.create_schema_and_data()
        await self.create_relationships()
        await self.create_indexes()
        await self.create_vector_indexes()
        logger.info("SpyroRAG System V2 initialized with complete semantic model")
        
    def close(self):
        """Close database connection"""
        self.driver.close()


# Updated Text2Cypher Schema
SPYRO_SCHEMA_V2 = """
Node properties:
Customer {name: STRING, industry: STRING}
Product {name: STRING, description: STRING}
Project {name: STRING, status: STRING}
Team {name: STRING, size: INTEGER}
SaaSSubscription {plan: STRING, period: STRING}
AnnualRecurringRevenue {amount: STRING, year: INTEGER}
CustomerSuccessScore {score: FLOAT, health_status: STRING}
Risk {level: STRING, type: STRING, description: STRING}
Event {type: STRING, date: STRING, impact: STRING}
SLA {metric: STRING, guarantee: STRING}
OperationalStatistics {metric: STRING, value: STRING}
OperationalCost {cost: STRING, category: STRING}
Profitability {impact: STRING, margin: STRING}
CompanyObjective {name: STRING, target: STRING}
Feature {name: STRING, priority: STRING}
Roadmap {name: STRING, quarter: STRING}

The relationships:
(:Product)-[:ASSIGNED_TO_TEAM]->(:Team)
(:Product)-[:HAS_SLA]->(:SLA)
(:Product)-[:HAS_OPERATIONAL_STATS]->(:OperationalStatistics)
(:Product)-[:HAS_ROADMAP]->(:Roadmap)
(:Product)-[:USED_BY]->(:Customer)
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:Customer)-[:HAS_RISK]->(:Risk)
(:Customer)-[:AFFECTED_BY_EVENT]->(:Event)
(:CustomerSuccessScore)-[:INFLUENCED_BY]->(:Event)
(:SaaSSubscription)-[:GENERATES]->(:AnnualRecurringRevenue)
(:Project)-[:DELIVERS_FEATURE]->(:Feature)
(:Project)-[:HAS_OPERATIONAL_COST]->(:OperationalCost)
(:Project)-[:CONTRIBUTES_TO_PROFITABILITY]->(:Profitability)
(:Feature)-[:PART_OF]->(:Project)
(:Feature)-[:COMMITTED_TO]->(:Customer)
(:Roadmap)-[:HAS_FEATURE]->(:Feature)
(:OperationalCost)-[:AFFECTS]->(:Profitability)
(:Profitability)-[:SUPPORTS]->(:CompanyObjective)
(:Risk)-[:IMPACTS]->(:CompanyObjective)
"""

# Updated Cypher Examples
CYPHER_EXAMPLES_V2 = [
    "USER INPUT: 'Show customer subscriptions and revenue' QUERY: MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue) RETURN c.name as customer, s.plan as plan, arr.amount as revenue",
    "USER INPUT: 'Which features are committed to customers?' QUERY: MATCH (f:Feature)-[:COMMITTED_TO]->(c:Customer) RETURN f.name as feature, c.name as customer, f.priority as priority",
    "USER INPUT: 'Show project costs and profitability' QUERY: MATCH (p:Project)-[:HAS_OPERATIONAL_COST]->(oc:OperationalCost), (p)-[:CONTRIBUTES_TO_PROFITABILITY]->(prof:Profitability) RETURN p.name as project, oc.cost as cost, prof.impact as profit_impact",
    "USER INPUT: 'What events affected customer success scores?' QUERY: MATCH (css:CustomerSuccessScore)-[:INFLUENCED_BY]->(e:Event)<-[:AFFECTED_BY_EVENT]-(c:Customer) RETURN c.name as customer, css.score as score, e.type as event_type, e.impact as impact",
    "USER INPUT: 'Show risks impacting company objectives' QUERY: MATCH (r:Risk)-[:IMPACTS]->(co:CompanyObjective) RETURN r.type as risk_type, r.level as risk_level, co.name as objective, co.target as target",
    "USER INPUT: 'How does profitability support objectives?' QUERY: MATCH (p:Profitability)-[:SUPPORTS]->(co:CompanyObjective) RETURN p.impact as profit_impact, co.name as objective, co.target as target"
]


async def main():
    """Test the updated implementation"""
    system = SpyroRAGSystemV2()
    
    try:
        # Initialize the system with complete semantic model
        await system.initialize()
        
        # Verify the implementation
        with system.driver.session() as session:
            # Test query 1: Customer -> Subscription -> ARR flow
            result = session.run("""
                MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue)
                RETURN c.name as customer, s.plan as plan, arr.amount as revenue
                ORDER BY customer
            """)
            
            print("\n=== Customer Revenue Flow ===")
            for record in result:
                print(f"{record['customer']}: {record['plan']} -> {record['revenue']}")
            
            # Test query 2: Cost -> Profitability -> Objective flow
            result = session.run("""
                MATCH (oc:OperationalCost)-[:AFFECTS]->(p:Profitability)-[:SUPPORTS]->(co:CompanyObjective)
                RETURN oc.cost as cost, p.impact as profit, co.name as objective
            """)
            
            print("\n=== Financial Impact Flow ===")
            for record in result:
                print(f"Cost: {record['cost']} -> Profit: {record['profit']} -> Objective: {record['objective']}")
            
            # Test query 3: Event -> Success Score relationship
            result = session.run("""
                MATCH (css:CustomerSuccessScore)-[:INFLUENCED_BY]->(e:Event)
                RETURN css.score as score, e.type as event_type, e.impact as impact
            """)
            
            print("\n=== Events Influencing Success Scores ===")
            for record in result:
                print(f"Score: {record['score']} influenced by {record['event_type']}: {record['impact']}")
            
            # Test query 4: Risk -> Objective impact
            result = session.run("""
                MATCH (r:Risk)-[:IMPACTS]->(co:CompanyObjective)
                RETURN r.type as risk_type, r.level as level, co.name as objective
            """)
            
            print("\n=== Risks Impacting Objectives ===")
            for record in result:
                print(f"{record['risk_type']} ({record['level']}) impacts {record['objective']}")
                
    finally:
        system.close()


if __name__ == "__main__":
    asyncio.run(main())