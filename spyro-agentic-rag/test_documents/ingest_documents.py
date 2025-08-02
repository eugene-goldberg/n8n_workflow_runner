#!/usr/bin/env python3
"""
Comprehensive Document Ingestion Pipeline using Agentic RAG Solution
This script ingests test documents into Neo4j using our developed components
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path

# Add implementation paths
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase1_infrastructure/feature_1_1_document_processor/src')
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase1_infrastructure/feature_1_2_embedding_generator/src')
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase1_infrastructure/feature_1_3_schema_mapper/src')
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase1_infrastructure/feature_1_4_change_detector/src')
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase2_processing/feature_2_1_entity_extractor/src')
sys.path.append('/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/implementation/phase2_processing/feature_2_2_relationship_builder/src')

# Import our components
from document_processor import DocumentProcessor, ProcessingConfig
from embedding_generator import EmbeddingGenerator, EmbeddingConfig
from schema_mapper import SchemaMapper, MappingConfig
from change_detector import ChangeDetector
from entity_extractor import EntityExtractor
from models import Entity as ExtractorEntity, MappingRule
from relationship_builder import RelationshipBuilder
from multi_hop_discoverer import MultiHopRelationshipDiscoverer
from semantic_miner import SemanticRelationshipMiner

# Neo4j imports
from neo4j import GraphDatabase
import openai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AgenticRAGIngestionPipeline:
    """Complete ingestion pipeline using our agentic RAG components"""
    
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, openai_api_key):
        """Initialize the ingestion pipeline"""
        # Neo4j connection
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # OpenAI setup
        openai.api_key = openai_api_key
        
        # Initialize components
        self.doc_processor = DocumentProcessor(ProcessingConfig())
        self.embedding_gen = EmbeddingGenerator(EmbeddingConfig(
            model_name="text-embedding-ada-002",
            api_key=openai_api_key
        ))
        self.schema_mapper = SchemaMapper(MappingConfig())
        self.entity_extractor = EntityExtractor()
        self.relationship_builder = RelationshipBuilder()
        self.semantic_miner = SemanticRelationshipMiner()
        
        # Document storage
        self.processed_documents = []
        self.extracted_entities = []
        self.discovered_relationships = []
        
    async def process_csv_files(self, csv_dir):
        """Process CSV files and extract structured data"""
        logger.info(f"Processing CSV files from {csv_dir}")
        
        csv_files = list(Path(csv_dir).glob("*.csv"))
        
        for csv_file in csv_files:
            logger.info(f"Processing {csv_file.name}")
            
            # Read CSV
            df = pd.read_csv(csv_file)
            
            # Process based on file type
            if "customers" in csv_file.name:
                await self._process_customer_data(df)
            elif "products" in csv_file.name:
                await self._process_product_data(df)
            elif "subscriptions" in csv_file.name:
                await self._process_subscription_data(df)
            elif "teams" in csv_file.name:
                await self._process_team_data(df)
            elif "risks" in csv_file.name:
                await self._process_risk_data(df)
            elif "roadmap" in csv_file.name:
                await self._process_roadmap_data(df)
            elif "events" in csv_file.name:
                await self._process_event_data(df)
            elif "sla" in csv_file.name:
                await self._process_sla_data(df)
            elif "commitments" in csv_file.name:
                await self._process_commitment_data(df)
    
    async def _process_customer_data(self, df):
        """Process customer data from CSV"""
        for _, row in df.iterrows():
            # Create customer entity
            customer = ExtractorEntity(
                id=f"cust_{row['customer_name'].lower().replace(' ', '_')}",
                type="Customer",
                attributes={
                    "name": row['customer_name'],
                    "industry": row['industry'],
                    "size": row['size'],
                    "region": row['region'],
                    "arr_value": row['arr_value']
                }
            )
            self.extracted_entities.append(customer)
            
            # Create success score entity
            success_score = ExtractorEntity(
                id=f"css_{row['customer_name'].lower().replace(' ', '_')}",
                type="CustomerSuccessScore",
                attributes={
                    "score": row['success_score'],
                    "trend": row['trend'],
                    "customer_id": customer.id
                }
            )
            self.extracted_entities.append(success_score)
    
    async def _process_product_data(self, df):
        """Process product data from CSV"""
        for _, row in df.iterrows():
            product = ExtractorEntity(
                id=f"prod_{row['product_name'].lower().replace(' ', '_')}",
                type="Product",
                attributes={
                    "name": row['product_name'],
                    "type": row['type'],
                    "market_focus": row['market_focus'],
                    "features": row['features'].split(';'),
                    "sla_uptime_target": row['sla_uptime_target'],
                    "adoption_rate": row['adoption_rate']
                }
            )
            self.extracted_entities.append(product)
            
            # Create operational cost entity
            cost = ExtractorEntity(
                id=f"cost_{row['product_name'].lower().replace(' ', '_')}",
                type="OperationalCost",
                attributes={
                    "amount": row['monthly_operational_cost'],
                    "period": "monthly",
                    "product_id": product.id
                }
            )
            self.extracted_entities.append(cost)
    
    async def _process_subscription_data(self, df):
        """Process subscription data from CSV"""
        for _, row in df.iterrows():
            subscription = ExtractorEntity(
                id=row['subscription_id'],
                type="SaaSSubscription",
                attributes={
                    "customer_name": row['customer_name'],
                    "product_name": row['product_name'],
                    "value": row['value'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "status": row['status'],
                    "renewal_probability": row['renewal_probability']
                }
            )
            self.extracted_entities.append(subscription)
    
    async def _process_team_data(self, df):
        """Process team data from CSV"""
        for _, row in df.iterrows():
            team = ExtractorEntity(
                id=f"team_{row['team_name'].lower().replace(' ', '_')}",
                type="Team",
                attributes={
                    "name": row['team_name'],
                    "department": row['department'],
                    "size": row['size'],
                    "focus_area": row['focus_area'],
                    "supporting_product": row['supporting_product']
                }
            )
            self.extracted_entities.append(team)
    
    async def _process_risk_data(self, df):
        """Process risk data from CSV"""
        for _, row in df.iterrows():
            risk = ExtractorEntity(
                id=row['risk_id'],
                type="Risk",
                attributes={
                    "type": row['type'],
                    "severity": row['severity'],
                    "description": row['description'],
                    "probability": row['probability'],
                    "impact_amount": row['impact_amount'],
                    "status": row['status'],
                    "related_entity": row['related_entity_name']
                }
            )
            self.extracted_entities.append(risk)
    
    async def _process_roadmap_data(self, df):
        """Process roadmap data from CSV"""
        for _, row in df.iterrows():
            roadmap_item = ExtractorEntity(
                id=row['roadmap_id'],
                type="RoadmapItem",
                attributes={
                    "product_name": row['product_name'],
                    "title": row['title'],
                    "status": row['status'],
                    "estimated_completion": row['estimated_completion'],
                    "priority": row['priority'],
                    "responsible_team": row['responsible_team']
                }
            )
            self.extracted_entities.append(roadmap_item)
    
    async def _process_event_data(self, df):
        """Process event data from CSV"""
        for _, row in df.iterrows():
            event = ExtractorEntity(
                id=row['event_id'],
                type="Event",
                attributes={
                    "customer_name": row['customer_name'],
                    "event_type": row['event_type'],
                    "impact": row['impact'],
                    "severity": row['severity'],
                    "description": row['description'],
                    "timestamp": row['timestamp']
                }
            )
            self.extracted_entities.append(event)
    
    async def _process_sla_data(self, df):
        """Process SLA data from CSV"""
        for _, row in df.iterrows():
            sla = ExtractorEntity(
                id=row['sla_id'],
                type="SLA",
                attributes={
                    "customer_name": row['customer_name'],
                    "metric": row['metric'],
                    "target": row['target'],
                    "current_performance": row['current_performance'],
                    "penalty_percentage": row['penalty_percentage'],
                    "status": row['status']
                }
            )
            self.extracted_entities.append(sla)
    
    async def _process_commitment_data(self, df):
        """Process commitment data from CSV"""
        for _, row in df.iterrows():
            commitment = ExtractorEntity(
                id=row['commitment_id'],
                type="Commitment",
                attributes={
                    "customer_name": row['customer_name'],
                    "description": row['description'],
                    "due_date": row['due_date'],
                    "status": row['status'],
                    "dependent_roadmap_item": row.get('dependent_roadmap_item')
                }
            )
            self.extracted_entities.append(commitment)
    
    async def process_text_documents(self, text_dir):
        """Process text documents and extract relationships"""
        logger.info(f"Processing text documents from {text_dir}")
        
        text_files = list(Path(text_dir).glob("*.txt"))
        
        for text_file in text_files:
            logger.info(f"Processing {text_file.name}")
            
            # Read document
            with open(text_file, 'r') as f:
                content = f.read()
            
            # Process document
            processed_doc = await self.doc_processor.process_document(
                content=content,
                doc_type="text",
                metadata={"filename": text_file.name}
            )
            
            # Generate embeddings for chunks
            for chunk in processed_doc.chunks:
                embedding = await self.embedding_gen.generate_embedding(chunk.text)
                chunk.embedding = embedding.vector
            
            self.processed_documents.append(processed_doc)
            
            # Extract semantic relationships from text
            if self.extracted_entities:
                relationships = await self.semantic_miner.mine_from_text(
                    content, 
                    self.extracted_entities
                )
                self.discovered_relationships.extend(relationships)
    
    async def build_relationships(self):
        """Build all relationships between entities"""
        logger.info("Building relationships between entities")
        
        # Build explicit relationships
        explicit_rels = await self.relationship_builder.build_relationships(
            self.extracted_entities
        )
        self.discovered_relationships.extend(explicit_rels)
        
        # Discover multi-hop relationships
        if len(self.discovered_relationships) > 0:
            multi_hop_discoverer = MultiHopRelationshipDiscoverer()
            multi_hop_rels = await multi_hop_discoverer.discover_multi_hop(
                self.extracted_entities,
                self.discovered_relationships,
                max_hops=3
            )
            self.discovered_relationships.extend(multi_hop_rels)
    
    def write_to_neo4j(self):
        """Write all data to Neo4j"""
        logger.info("Writing data to Neo4j")
        
        with self.driver.session() as session:
            # Clear existing data
            session.run("MATCH (n) DETACH DELETE n")
            
            # Create entities
            for entity in self.extracted_entities:
                self._create_entity_node(session, entity)
            
            # Create relationships
            for rel in self.discovered_relationships:
                self._create_relationship(session, rel)
            
            # Create document nodes
            for doc in self.processed_documents:
                self._create_document_nodes(session, doc)
            
            # Create indexes
            self._create_indexes(session)
    
    def _create_entity_node(self, session, entity):
        """Create entity node in Neo4j"""
        query = f"""
        CREATE (n:{entity.type} {{
            id: $id,
            {', '.join([f'{k}: ${k}' for k in entity.attributes.keys()])}
        }})
        """
        params = {"id": entity.id}
        params.update(entity.attributes)
        session.run(query, params)
    
    def _create_relationship(self, session, rel):
        """Create relationship in Neo4j"""
        if rel.source and rel.target:
            query = f"""
            MATCH (s {{id: $source_id}})
            MATCH (t {{id: $target_id}})
            CREATE (s)-[r:{rel.relationship_type.value} {{
                confidence: $confidence,
                evidence: $evidence
            }}]->(t)
            """
            session.run(query, {
                "source_id": rel.source.id,
                "target_id": rel.target.id,
                "confidence": rel.confidence,
                "evidence": rel.evidence
            })
    
    def _create_document_nodes(self, session, doc):
        """Create document and chunk nodes in Neo4j"""
        # Create document node
        doc_query = """
        CREATE (d:Document {
            id: $id,
            filename: $filename,
            doc_type: $doc_type,
            chunk_count: $chunk_count
        })
        """
        session.run(doc_query, {
            "id": doc.doc_id,
            "filename": doc.metadata.get("filename", "unknown"),
            "doc_type": doc.doc_type,
            "chunk_count": len(doc.chunks)
        })
        
        # Create chunk nodes
        for chunk in doc.chunks:
            chunk_query = """
            MATCH (d:Document {id: $doc_id})
            CREATE (c:Chunk {
                text: $text,
                chunk_index: $index,
                embedding: $embedding
            })
            CREATE (d)-[:HAS_CHUNK]->(c)
            """
            session.run(chunk_query, {
                "doc_id": doc.doc_id,
                "text": chunk.text,
                "index": chunk.metadata.get("chunk_index", 0),
                "embedding": chunk.embedding if hasattr(chunk, 'embedding') else None
            })
    
    def _create_indexes(self, session):
        """Create necessary indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Customer) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Product) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Team) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Risk) ON (n.type)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.id)",
            "CREATE FULLTEXT INDEX document_text IF NOT EXISTS FOR (n:Chunk) ON EACH [n.text]"
        ]
        
        for index in indexes:
            try:
                session.run(index)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    def verify_ingestion(self):
        """Verify the ingestion was successful"""
        logger.info("Verifying ingestion")
        
        with self.driver.session() as session:
            # Count nodes by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            logger.info("Node counts:")
            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            
            logger.info("Relationship counts:")
            for record in result:
                logger.info(f"  {record['type']}: {record['count']}")
    
    def close(self):
        """Close connections"""
        self.driver.close()


async def main():
    """Main ingestion function"""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Document directories
    BASE_DIR = "/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/test_documents"
    CSV_DIR = os.path.join(BASE_DIR, "csv")
    TEXT_DIR = os.path.join(BASE_DIR, "text")
    
    logger.info("Starting Agentic RAG Ingestion Pipeline")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = AgenticRAGIngestionPipeline(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASSWORD,
        OPENAI_API_KEY
    )
    
    try:
        # Process CSV files
        logger.info("Phase 1: Processing CSV files")
        await pipeline.process_csv_files(CSV_DIR)
        logger.info(f"Extracted {len(pipeline.extracted_entities)} entities from CSV files")
        
        # Process text documents
        logger.info("\nPhase 2: Processing text documents")
        await pipeline.process_text_documents(TEXT_DIR)
        logger.info(f"Processed {len(pipeline.processed_documents)} documents")
        
        # Build relationships
        logger.info("\nPhase 3: Building relationships")
        await pipeline.build_relationships()
        logger.info(f"Discovered {len(pipeline.discovered_relationships)} relationships")
        
        # Write to Neo4j
        logger.info("\nPhase 4: Writing to Neo4j")
        pipeline.write_to_neo4j()
        
        # Verify
        logger.info("\nPhase 5: Verification")
        pipeline.verify_ingestion()
        
        logger.info("\n✅ Ingestion completed successfully!")
        logger.info("The Neo4j database is now populated with:")
        logger.info("- Customer data with success scores and risk profiles")
        logger.info("- Product information with operational costs")
        logger.info("- Team structures and responsibilities")
        logger.info("- Roadmap items and commitments")
        logger.info("- SLA tracking and events")
        logger.info("- Complex relationships discovered through our agentic system")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
    finally:
        pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())