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
from neo4j_graphrag.experimental.components.kg_writer import Neo4jWriter
from neo4j_graphrag.experimental.components.schema import (
    SchemaBuilder,
    SchemaEntity,
    SchemaRelation,
    SchemaProperty
)
from neo4j_graphrag.experimental.components.entity_relation_extractor import (
    LLMEntityRelationExtractor,
    OnError
)
from neo4j_graphrag.experimental.pipeline import Pipeline
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpyroSchemaBuilder:
    """Build a strict schema for SpyroSolutions entities"""
    
    @staticmethod
    def build_schema():
        # Define entities with required properties
        entities = [
            SchemaEntity(
                label="Customer",
                properties=[
                    SchemaProperty(name="name", type="STRING", required=True),
                    SchemaProperty(name="industry", type="STRING", required=False)
                ]
            ),
            SchemaEntity(
                label="Product",
                properties=[
                    SchemaProperty(name="name", type="STRING", required=True),
                    SchemaProperty(name="description", type="STRING", required=False)
                ]
            ),
            SchemaEntity(
                label="Project",
                properties=[
                    SchemaProperty(name="name", type="STRING", required=True),
                    SchemaProperty(name="status", type="STRING", required=False)
                ]
            ),
            SchemaEntity(
                label="Team",
                properties=[
                    SchemaProperty(name="name", type="STRING", required=True),
                    SchemaProperty(name="size", type="INTEGER", required=False)
                ]
            ),
            SchemaEntity(
                label="SaaSSubscription",
                properties=[
                    SchemaProperty(name="plan", type="STRING", required=True),
                    SchemaProperty(name="ARR", type="STRING", required=True)
                ]
            ),
            SchemaEntity(
                label="Risk",
                properties=[
                    SchemaProperty(name="level", type="STRING", required=True),
                    SchemaProperty(name="type", type="STRING", required=False),
                    SchemaProperty(name="description", type="STRING", required=False)
                ]
            ),
            SchemaEntity(
                label="OperationalCost",
                properties=[
                    SchemaProperty(name="amount", type="STRING", required=True)
                ]
            ),
            SchemaEntity(
                label="CustomerSuccessScore",
                properties=[
                    SchemaProperty(name="score", type="FLOAT", required=True),
                    SchemaProperty(name="health_status", type="STRING", required=False)
                ]
            )
        ]
        
        # Define relationships
        relations = [
            SchemaRelation(
                label="SUBSCRIBES_TO",
                source="Customer",
                target="SaaSSubscription"
            ),
            SchemaRelation(
                label="HAS_RISK",
                source="Customer", 
                target="Risk"
            ),
            SchemaRelation(
                label="USES",
                source="Customer",
                target="Product"
            ),
            SchemaRelation(
                label="ASSIGNED_TO_TEAM",
                source="Product",
                target="Team"
            ),
            SchemaRelation(
                label="HAS_OPERATIONAL_COST",
                source="Project",
                target="OperationalCost"
            ),
            SchemaRelation(
                label="HAS_SUCCESS_SCORE",
                source="Customer",
                target="CustomerSuccessScore"
            )
        ]
        
        return SchemaBuilder(entities=entities, relations=relations)


class EntityResolutionWriter(Neo4jWriter):
    """Custom writer that performs entity resolution before writing"""
    
    def __init__(self, driver, neo4j_database: Optional[str] = None):
        super().__init__(driver, neo4j_database)
        
    async def run(self, graph: Any) -> Any:
        """Override run to add entity resolution"""
        # First, write the graph normally
        result = await super().run(graph)
        
        # Then perform entity resolution
        with self.driver.session(database=self.neo4j_database) as session:
            # Merge duplicate entities based on name
            merge_queries = [
                # Merge Customers
                """
                MATCH (c:Customer)
                WITH c.name as name, collect(c) as customers
                WHERE size(customers) > 1
                WITH head(customers) as main, tail(customers) as duplicates
                UNWIND duplicates as dup
                MATCH (dup)-[r]->(n)
                MERGE (main)-[r2:SUBSCRIBES_TO|HAS_RISK|USES|HAS_SUCCESS_SCORE]->(n)
                DELETE r, dup
                """,
                
                # Merge Products
                """
                MATCH (p:Product)
                WITH p.name as name, collect(p) as products
                WHERE size(products) > 1
                WITH head(products) as main, tail(products) as duplicates
                UNWIND duplicates as dup
                MATCH (dup)-[r]->(n)
                MERGE (main)-[:ASSIGNED_TO_TEAM|HAS_SLA|HAS_OPERATIONAL_STATS]->(n)
                DELETE r, dup
                """,
                
                # Merge duplicate Risk nodes for same customer
                """
                MATCH (c:Customer)-[:HAS_RISK]->(r:Risk)
                WITH c, r.level as level, collect(r) as risks
                WHERE size(risks) > 1
                WITH c, level, head(risks) as main, tail(risks) as duplicates
                UNWIND duplicates as dup
                DELETE dup
                """
            ]
            
            for query in merge_queries:
                try:
                    session.run(query)
                    logger.info(f"Executed merge query successfully")
                except Exception as e:
                    logger.warning(f"Merge query failed: {e}")
        
        return result


class EnhancedKGBuilder:
    """Enhanced KG Builder with better entity extraction and resolution"""
    
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
        )
        self.embedder = OpenAIEmbeddings()
        
    def create_pipeline(self):
        """Create an enhanced pipeline with entity resolution"""
        
        # Create schema
        schema_builder = SpyroSchemaBuilder.build_schema()
        
        # Create custom prompt for better extraction
        extraction_prompt = """
        Extract entities and relationships from the text following this schema strictly:
        
        Entities:
        - Customer: Must have 'name' property
        - Product: Must have 'name' property  
        - Project: Must have 'name' property
        - Team: Must have 'name' and 'size' (integer) properties
        - SaaSSubscription: Must have 'plan' and 'ARR' properties
        - Risk: Must have 'level' (High/Medium/Low) property
        - OperationalCost: Must have 'amount' property (use $ format)
        - CustomerSuccessScore: Must have 'score' (float 0-100) property
        
        Important:
        - Extract exact values from the text
        - For costs/revenue, preserve the $ format (e.g., "$5M")
        - For scores, extract numeric values
        - Avoid creating duplicate entities with the same name
        """
        
        # Create entity extractor with custom prompt
        entity_extractor = LLMEntityRelationExtractor(
            llm=self.llm,
            prompt_template=extraction_prompt,
            on_error=OnError.RAISE
        )
        
        # Create writer with entity resolution
        writer = EntityResolutionWriter(
            driver=self.driver,
            neo4j_database=None
        )
        
        # Build pipeline
        pipeline = Pipeline()
        pipeline.add_component(schema_builder, "schema")
        pipeline.add_component(entity_extractor, "extractor") 
        pipeline.add_component(writer, "writer")
        
        # Connect components
        pipeline.connect("schema", "extractor", {"schema": "schema"})
        pipeline.connect("extractor", "writer", {"graph": "graph"})
        
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
    
    def build_from_text(self, text: str):
        """Build knowledge graph from text with enhanced processing"""
        pipeline = self.create_pipeline()
        
        # Run pipeline
        logger.info("Running enhanced KG pipeline...")
        result = pipeline.run({"text": text})
        
        # Post-process
        logger.info("Post-processing graph...")
        self.post_process_graph()
        
        # Create indexes
        self._create_indexes()
        
        return result
    
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


def main():
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
    result = builder.build_from_text(text)
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


if __name__ == "__main__":
    main()