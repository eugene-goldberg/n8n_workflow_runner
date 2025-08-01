#!/usr/bin/env python3
"""
Complete SpyroSolutions Semantic Model Implementation using neo4j-graphrag-python

Based on the semantic model diagram showing:
- Core entities: Product, Customer, Project, Team, SaaS Subscription, Risk
- Business metrics: SLAs, Operational Statistics, Roadmap, Features, ARR, Customer Success Score
- Financial: Operational Cost, Profitability, Company Objective
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
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Schema Definition based on the Semantic Model
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
    {"label": "ARR", "description": "Annual Recurring Revenue"},
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
    
    # Financial relationships
    {"label": "GENERATES_ARR", "description": "Subscription generates ARR"},
    {"label": "IMPACTS_RISK", "description": "Risk impacts customer or revenue"},
    
    # Feature relationships
    {"label": "COMMITTED_TO_CUSTOMER", "description": "Feature committed to customer"},
    {"label": "PART_OF_ROADMAP", "description": "Feature part of roadmap"},
    {"label": "HAS_FEATURE", "description": "Roadmap has feature"}
]

# Sample business data following the semantic model
SPYRO_BUSINESS_DATA = """
SpyroSolutions Product Portfolio and Customer Success Management

Products:
1. SpyroCloud Platform
   - Enterprise cloud infrastructure solution
   - SLA: 99.99% uptime guarantee
   - Operational Statistics: 99.96% actual uptime, 150ms average response time
   - Assigned to: Platform Engineering Team (45 engineers)
   - Roadmap: Q1 2024 - Multi-region deployment, Q2 2024 - Edge computing capabilities

2. SpyroAI Analytics
   - AI-powered business intelligence platform
   - SLA: 99.9% uptime, <2 second query response
   - Operational Statistics: 99.92% uptime, 1.8s average query time
   - Assigned to: AI/ML Team (30 engineers)
   - Roadmap: Q1 2024 - Natural language queries, Q2 2024 - Predictive analytics

3. SpyroSecure
   - Enterprise security suite
   - SLA: 99.99% threat detection rate
   - Operational Statistics: 99.97% detection rate, 0 critical breaches
   - Assigned to: Security Team (25 engineers)

Key Customers:

1. TechCorp Industries
   - Products: SpyroCloud Platform, SpyroAI Analytics
   - SaaS Subscription: Enterprise Plus - $5M ARR
   - Customer Success Score: 92/100
   - Risk: Medium - Considering competitive solutions
   - Events: Q4 2023 - Major outage affected operations (resolved)

2. GlobalBank Financial
   - Products: SpyroCloud Platform, SpyroSecure
   - SaaS Subscription: Premium Security - $8M ARR
   - Customer Success Score: 95/100
   - Risk: Low - Very satisfied, expanding usage
   - Events: Successfully migrated 500TB data in Q3 2023

3. RetailMax Corporation
   - Products: SpyroAI Analytics
   - SaaS Subscription: Analytics Pro - $3M ARR
   - Customer Success Score: 78/100
   - Risk: High - Feature gaps affecting satisfaction
   - Events: Delayed feature delivery impacting Q1 2024 goals

Active Projects:

1. Project Titan
   - Delivering: Multi-region deployment, Enhanced security features
   - Operational Cost: $2.5M
   - Expected Profitability Impact: +$15M ARR
   - Supports: Global expansion objective
   - Committed to: GlobalBank Financial, TechCorp Industries

2. Project Mercury
   - Delivering: Natural language query interface, Custom dashboards
   - Operational Cost: $1.8M
   - Expected Profitability Impact: +$8M ARR
   - Supports: AI leadership objective
   - Committed to: RetailMax Corporation

3. Project Apollo
   - Delivering: Edge computing capabilities, IoT integration
   - Operational Cost: $3.2M
   - Expected Profitability Impact: +$20M ARR
   - Supports: Innovation objective
   - Risk: Technical complexity may delay delivery

Company Objectives:

1. Global Expansion
   - Target: 50% international revenue by 2025
   - Current: 30% international revenue

2. AI Leadership
   - Target: #1 in AI-powered business analytics
   - Current: #3 in market

3. Innovation Excellence
   - Target: 40% revenue from products <2 years old
   - Current: 25%

Risk Assessment:

1. Customer Churn Risk - TechCorp
   - Impact: $5M ARR at risk
   - Mitigation: Executive engagement, feature acceleration

2. Technical Debt Risk - SpyroCloud
   - Impact: Potential SLA violations
   - Mitigation: Refactoring initiative Q2 2024

3. Competitive Risk - Analytics Market
   - Impact: Market share erosion
   - Mitigation: Accelerate AI feature development
"""


class SpyroSemanticRAG:
    """Complete implementation of SpyroSolutions RAG using the semantic model"""
    
    def __init__(self):
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = OpenAILLM(
            model_name="gpt-4",
            model_params={"temperature": 0}
        )
        
    async def build_knowledge_graph(self):
        """Build the knowledge graph following the semantic model"""
        logger.info("Building SpyroSolutions knowledge graph...")
        
        # Create the knowledge graph using SimpleKGPipeline
        kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            schema={
                "node_types": ENTITY_TYPES,
                "relationship_types": RELATIONSHIP_TYPES,
                "patterns": [
                    # Product relationships
                    ("Product", "HAS_SLA", "SLA"),
                    ("Product", "HAS_OPERATIONAL_STATS", "OperationalStatistics"),
                    ("Product", "HAS_ROADMAP", "Roadmap"),
                    ("Product", "ASSIGNED_TO_TEAM", "Team"),
                    ("Product", "USED_BY", "Customer"),
                    
                    # Customer relationships
                    ("Customer", "SUBSCRIBES_TO", "SaaSSubscription"),
                    ("Customer", "HAS_SUCCESS_SCORE", "CustomerSuccessScore"),
                    ("Customer", "AFFECTED_BY_EVENT", "Event"),
                    ("Customer", "HAS_RISK", "Risk"),
                    
                    # Project relationships
                    ("Project", "DELIVERS_FEATURE", "Feature"),
                    ("Project", "HAS_OPERATIONAL_COST", "OperationalCost"),
                    ("Project", "CONTRIBUTES_TO_PROFITABILITY", "Profitability"),
                    ("Project", "SUPPORTS_OBJECTIVE", "CompanyObjective"),
                    
                    # Financial relationships
                    ("SaaSSubscription", "GENERATES_ARR", "ARR"),
                    ("Risk", "IMPACTS_RISK", "Customer"),
                    ("Risk", "IMPACTS_RISK", "ARR"),
                    
                    # Feature relationships
                    ("Feature", "COMMITTED_TO_CUSTOMER", "Customer"),
                    ("Feature", "PART_OF_ROADMAP", "Roadmap"),
                    ("Roadmap", "HAS_FEATURE", "Feature")
                ]
            },
            from_pdf=False
        )
        
        # Run the pipeline
        result = await kg_builder.run_async(text=SPYRO_BUSINESS_DATA)
        logger.info(f"Knowledge graph built: {result}")
        
        # Create indexes
        await self._create_indexes()
        
    async def _create_indexes(self):
        """Create necessary indexes for retrieval"""
        logger.info("Creating indexes...")
        
        # Wait for chunks to be created
        await asyncio.sleep(2)
        
        try:
            # Create vector index
            create_vector_index(
                self.driver,
                "spyro_vector_index",
                label="__Chunk__",
                embedding_property="embedding",
                dimensions=1536,
                similarity_fn="cosine"
            )
            logger.info("Created vector index")
        except Exception as e:
            logger.warning(f"Vector index might exist: {e}")
        
        try:
            # Create fulltext index
            create_fulltext_index(
                self.driver,
                "spyro_fulltext_index",
                label="__Chunk__",
                node_properties=["text"]
            )
            logger.info("Created fulltext index")
        except Exception as e:
            logger.warning(f"Fulltext index might exist: {e}")
    
    def setup_retrievers(self):
        """Setup different types of retrievers"""
        logger.info("Setting up retrievers...")
        
        # Hybrid Retriever - combines vector and fulltext
        self.hybrid_retriever = HybridRetriever(
            driver=self.driver,
            vector_index_name="spyro_vector_index",
            fulltext_index_name="spyro_fulltext_index",
            embedder=self.embedder
        )
        
        # Hybrid Cypher Retriever - adds graph traversal
        cypher_query = """
        // Find related business entities
        MATCH (chunk)-[:PART_OF]->(doc)
        OPTIONAL MATCH (chunk)-[:MENTIONS]->(entity)
        WHERE entity:Product OR entity:Customer OR entity:Project 
           OR entity:Risk OR entity:SaaSSubscription
        WITH chunk, collect(DISTINCT entity.name) as entities
        
        // Find relationships
        OPTIONAL MATCH (chunk)-[:MENTIONS]->(e1)-[r]-(e2)
        WHERE e1 <> e2
        WITH chunk, entities, collect(DISTINCT type(r)) as relationships
        
        RETURN chunk.text as text,
               entities,
               relationships,
               chunk.embedding as embedding
        """
        
        self.hybrid_cypher_retriever = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name="spyro_vector_index",
            fulltext_index_name="spyro_fulltext_index",
            retrieval_query=cypher_query,
            embedder=self.embedder
        )
        
        # Create GraphRAG instances
        self.rag = GraphRAG(
            retriever=self.hybrid_retriever,
            llm=self.llm
        )
        
        self.rag_with_cypher = GraphRAG(
            retriever=self.hybrid_cypher_retriever,
            llm=self.llm
        )
        
        logger.info("Retrievers configured successfully")
    
    async def query(self, question: str, use_cypher: bool = False) -> dict:
        """Execute a query against the knowledge graph"""
        logger.info(f"Executing query: {question}")
        
        rag_instance = self.rag_with_cypher if use_cypher else self.rag
        
        result = rag_instance.search(
            query_text=question,
            return_context=True,
            retriever_config={"top_k": 5}
        )
        
        context_count = 0
        if hasattr(result, 'retriever_result') and result.retriever_result:
            context_count = len(result.retriever_result.items)
        
        return {
            "question": question,
            "answer": result.answer,
            "context_items": context_count,
            "retriever_type": "hybrid_cypher" if use_cypher else "hybrid"
        }
    
    def close(self):
        """Close database connection"""
        self.driver.close()


# Test queries specific to the semantic model
TEST_QUERIES = [
    # Product queries
    ("What products does SpyroSolutions offer?", False),
    ("What are the SLAs for SpyroCloud Platform?", False),
    ("Which team is responsible for SpyroAI Analytics?", True),
    
    # Customer queries
    ("Which customers are at risk?", True),
    ("What is GlobalBank's customer success score?", False),
    ("What events affected TechCorp?", True),
    
    # Financial queries
    ("What is the total ARR from all customers?", True),
    ("Which projects have the highest profitability impact?", True),
    ("What are the operational costs for Project Titan?", False),
    
    # Risk queries
    ("What risks are associated with customer churn?", True),
    ("Which customers have high risk levels?", True),
    
    # Strategic queries
    ("What are SpyroSolutions' company objectives?", False),
    ("Which projects support the global expansion objective?", True),
    
    # Complex queries
    ("Show me all customers, their subscriptions, and associated risks", True),
    ("What features are committed to RetailMax Corporation?", True),
    ("Which products have the best operational statistics?", False)
]


async def main():
    """Main execution function"""
    logger.info("Starting SpyroSolutions Semantic Model Implementation")
    logger.info("=" * 60)
    
    # Initialize the system
    system = SpyroSemanticRAG()
    
    try:
        # Build the knowledge graph
        await system.build_knowledge_graph()
        
        # Setup retrievers
        system.setup_retrievers()
        
        # Test queries
        logger.info("\nTesting queries against the semantic model...")
        logger.info("=" * 60)
        
        for query, use_cypher in TEST_QUERIES:
            result = await system.query(query, use_cypher)
            
            print(f"\nQuestion: {result['question']}")
            print(f"Retriever: {result['retriever_type']}")
            print(f"Context items: {result['context_items']}")
            print(f"Answer: {result['answer']}")
            print("-" * 60)
            
    finally:
        system.close()


# FastAPI Application
app = FastAPI(title="SpyroSolutions Semantic RAG API")

class QueryRequest(BaseModel):
    question: str
    use_cypher: bool = False

class QueryResponse(BaseModel):
    question: str
    answer: str
    context_items: int
    retriever_type: str

# Global system instance
rag_system = None

@app.on_event("startup")
async def startup_event():
    global rag_system
    rag_system = SpyroSemanticRAG()
    await rag_system.build_knowledge_graph()
    rag_system.setup_retrievers()

@app.on_event("shutdown")
def shutdown_event():
    if rag_system:
        rag_system.close()

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    result = await rag_system.query(request.question, request.use_cypher)
    return QueryResponse(**result)

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": "SpyroSolutions Semantic Model"}


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
    
    # Or run as API:
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)