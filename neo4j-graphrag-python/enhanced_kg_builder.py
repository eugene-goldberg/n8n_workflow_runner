#!/usr/bin/env python3
"""
Enhanced Knowledge Graph Builder for SpyroSolutions
Addresses issues with SimpleKGPipeline by adding:
1. Entity resolution to prevent duplicates
2. Consistent property extraction
3. Schema validation
4. Post-processing cleanup
"""

from typing import List, Dict, Any, Optional
import logging
from neo4j import GraphDatabase
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define schema based on SpyroSolutions model - Updated to match semantic model
ENTITY_TYPES = [
    {"label": "Customer", "description": "Customer organization with name and industry"},
    {"label": "Product", "description": "Product or service with name and description"},
    {"label": "Project", "description": "Development project with name and status"},
    {"label": "Team", "description": "Internal team with name and size"},
    {"label": "SaaSSubscription", "description": "SaaS subscription with plan and period"},
    {"label": "AnnualRecurringRevenue", "description": "Annual Recurring Revenue with amount and year"},
    {"label": "Risk", "description": "Risk with level, type and description"},
    {"label": "OperationalCost", "description": "Cost with amount and category"},
    {"label": "CustomerSuccessScore", "description": "Score 0-100 with health status"},
    {"label": "Event", "description": "Event with type, date and impact"},
    {"label": "SLA", "description": "Service Level Agreement with metric and guarantee"},
    {"label": "OperationalStatistics", "description": "Operational metrics with value"},
    {"label": "Profitability", "description": "Financial profitability with impact and margin"},
    {"label": "CompanyObjective", "description": "Strategic objective with target"},
    {"label": "Feature", "description": "Product feature with priority"},
    {"label": "Roadmap", "description": "Product roadmap with quarter"}
]

RELATION_TYPES = [
    "SUBSCRIBES_TO",
    "HAS_RISK", 
    "USES",
    "USED_BY",
    "ASSIGNED_TO_TEAM",
    "HAS_OPERATIONAL_COST",
    "HAS_SUCCESS_SCORE",
    "CONTRIBUTES_TO_PROFITABILITY",
    "AFFECTED_BY_EVENT",
    "INFLUENCED_BY",
    "GENERATES",
    "DELIVERS_FEATURE",
    "PART_OF",
    "COMMITTED_TO",
    "HAS_FEATURE",
    "AFFECTS",
    "SUPPORTS",
    "IMPACTS",
    "HAS_SLA",
    "HAS_OPERATIONAL_STATS",
    "HAS_ROADMAP"
]


class EntityResolution:
    """Handles entity resolution and deduplication after KG creation"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def merge_duplicate_entities(self):
        """Merge entities with the same name"""
        with self.driver.session() as session:
            # Merge duplicate Customers - simpler approach
            result = session.run("""
                MATCH (c:Customer)
                WITH c.name as name, collect(c) as customers
                WHERE size(customers) > 1
                WITH name, head(customers) as keep, tail(customers) as remove_list
                UNWIND remove_list as remove
                // Transfer outgoing relationships
                OPTIONAL MATCH (remove)-[r:SUBSCRIBES_TO]->(target)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[:SUBSCRIBES_TO]->(target)
                )
                WITH name, keep, remove, collect(r) as rels1
                OPTIONAL MATCH (remove)-[r:HAS_RISK]->(target)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[:HAS_RISK]->(target)
                )
                WITH name, keep, remove, rels1, collect(r) as rels2
                OPTIONAL MATCH (remove)-[r:USES]->(target)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[:USES]->(target)
                )
                WITH name, keep, remove, rels1, rels2, collect(r) as rels3
                OPTIONAL MATCH (remove)-[r:HAS_SUCCESS_SCORE]->(target)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[:HAS_SUCCESS_SCORE]->(target)
                )
                WITH name, keep, remove
                DETACH DELETE remove
                RETURN name, count(remove) as removed_count
            """)
            
            for record in result:
                if record['removed_count'] > 0:
                    logger.info(f"Removed {record['removed_count']} duplicate customers named '{record['name']}'")
            
            # Merge duplicate Products - simpler approach
            result = session.run("""
                MATCH (p:Product)
                WITH p.name as name, collect(p) as products
                WHERE size(products) > 1
                WITH name, head(products) as keep, tail(products) as remove_list
                UNWIND remove_list as remove
                // Transfer outgoing relationships
                OPTIONAL MATCH (remove)-[r:ASSIGNED_TO_TEAM]->(target)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (keep)-[:ASSIGNED_TO_TEAM]->(target)
                )
                WITH name, keep, remove
                // Transfer incoming relationships
                OPTIONAL MATCH (source)-[r:USES]->(remove)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (source)-[:USES]->(keep)
                )
                WITH name, keep, remove
                DETACH DELETE remove
                RETURN name, count(remove) as removed_count
            """)
            
            for record in result:
                if record['removed_count'] > 0:
                    logger.info(f"Removed {record['removed_count']} duplicate products named '{record['name']}'")
            
            # Merge duplicate Teams - simpler approach
            result = session.run("""
                MATCH (t:Team)
                WITH t.name as name, collect(t) as teams
                WHERE size(teams) > 1
                // Keep the team with the highest size or the first one
                WITH name, 
                     head([t IN teams WHERE t.size IS NOT NULL | t] + teams) as keep,
                     tail(teams) as remove_list
                UNWIND remove_list as remove
                // Skip if remove is the same as keep
                WITH name, keep, remove WHERE remove <> keep
                // Transfer incoming relationships
                OPTIONAL MATCH (source)-[r:ASSIGNED_TO_TEAM]->(remove)
                FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (source)-[:ASSIGNED_TO_TEAM]->(keep)
                )
                WITH name, keep, remove
                DETACH DELETE remove
                RETURN name, count(remove) as removed_count
            """)
            
            for record in result:
                if record['removed_count'] > 0:
                    logger.info(f"Removed {record['removed_count']} duplicate teams named '{record['name']}'")
    
    def remove_duplicate_relationships(self):
        """Remove duplicate relationships between the same nodes"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a)-[r]->(b)
                WITH a, b, type(r) AS rel_type, collect(r) AS rels
                WHERE size(rels) > 1
                FOREACH (r IN tail(rels) | DELETE r)
                RETURN count(*) as removed_count
            """)
            
            removed = result.single()['removed_count']
            logger.info(f"Removed {removed} duplicate relationships")


class EnhancedKGBuilder:
    """Enhanced KG Builder with better entity extraction and resolution"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={"temperature": 0}
        )
        self.embedder = OpenAIEmbeddings()
        self.entity_resolution = EntityResolution(self.driver)
        
    def create_pipeline(self):
        """Create SimpleKGPipeline with custom configuration"""
        
        # Create text splitter
        text_splitter = FixedSizeSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        # Create pipeline with explicit entity and relation types
        pipeline = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            entities=ENTITY_TYPES,
            relations=RELATION_TYPES,
            from_pdf=False,
            text_splitter=text_splitter
        )
        
        return pipeline
    
    def post_process_graph(self):
        """Clean up the graph after initial creation"""
        with self.driver.session() as session:
            # Remove __Entity__ labels
            session.run("""
                MATCH (n)
                WHERE '__Entity__' IN labels(n)
                REMOVE n:__Entity__
            """)
            
            # Ensure consistent property names
            session.run("""
                MATCH (oc:OperationalCost)
                WHERE oc.cost IS NOT NULL AND oc.amount IS NULL
                SET oc.amount = oc.cost
                REMOVE oc.cost
            """)
            
            # Add missing property values where possible
            session.run("""
                MATCH (r:Risk)
                WHERE r.type IS NULL
                SET r.type = CASE 
                    WHEN r.level = 'High' THEN 'Churn Risk'
                    WHEN r.level = 'Medium' THEN 'Adoption Risk'
                    ELSE 'Low Risk'
                END
            """)
            
            logger.info("Post-processing completed")
    
    async def build_from_text(self, text: str):
        """Build knowledge graph from text with enhanced processing"""
        pipeline = self.create_pipeline()
        
        # Run pipeline
        logger.info("Running enhanced KG pipeline...")
        try:
            # SimpleKGPipeline uses run_async
            result = await pipeline.run_async(text=text)
            logger.info(f"Pipeline result: {result}")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            raise
        
        # Post-process
        logger.info("Post-processing graph...")
        self.post_process_graph()
        
        # Entity resolution
        logger.info("Performing entity resolution...")
        self.entity_resolution.merge_duplicate_entities()
        self.entity_resolution.remove_duplicate_relationships()
        
        # Create indexes
        self._create_indexes()
        
        return {"status": "completed", "result": result}
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        with self.driver.session() as session:
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.name)",
                "CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.name)",
                "CREATE INDEX IF NOT EXISTS FOR (pr:Project) ON (pr.name)",
                "CREATE INDEX IF NOT EXISTS FOR (t:Team) ON (t.name)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.warning(f"Index creation: {e}")


async def main():
    """Example usage"""
    
    # Sample text
    text = """
    SpyroSolutions Customer Information:
    
    TechCorp Industries is a major customer using SpyroCloud Platform with an 
    Enterprise Plus subscription worth $5M ARR. They have a medium risk level 
    due to considering competitive solutions.
    
    GlobalBank Financial subscribes to our Premium Security plan for $8M ARR 
    and uses both SpyroCloud Platform and SpyroSecure products. They have a 
    low risk profile.
    
    Project Apollo has operational costs of $3.2M and is managed by the AI/ML Team 
    which has 30 engineers.
    """
    
    # Initialize builder
    builder = EnhancedKGBuilder(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password123"
    )
    
    # Build graph
    result = await builder.build_from_text(text)
    logger.info("Enhanced KG building completed")
    
    # Verify results
    with builder.driver.session() as session:
        result = session.run("""
            MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)
            RETURN c.name as customer, s.plan as plan, s.ARR as arr
        """)
        
        print("\nCustomer Subscriptions:")
        for record in result:
            print(f"  {record['customer']}: {record['plan']} - {record['arr']}")
    
    # Close driver
    builder.driver.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())