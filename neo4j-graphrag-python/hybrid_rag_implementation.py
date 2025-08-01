#!/usr/bin/env python3
"""
Complete Hybrid Agentic RAG Implementation using neo4j-graphrag-python

This implementation demonstrates:
1. Building a knowledge graph from text
2. Creating vector and fulltext indexes
3. Using HybridRetriever for combined search
4. GraphRAG for question answering
"""

import asyncio
import logging
import os
from typing import List, Optional
from dotenv import load_dotenv

import neo4j
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import HybridRetriever, HybridCypherRetriever, Text2CypherRetriever
from neo4j_graphrag.types import RetrieverResult
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
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# Index names
VECTOR_INDEX_NAME = "business_vector_index"
FULLTEXT_INDEX_NAME = "business_fulltext_index"

# Sample business data
BUSINESS_DATA = """
TechCorp is a leading technology company founded in 2010 by Sarah Johnson and Michael Chen. 
The company specializes in cloud computing solutions and artificial intelligence services.
TechCorp has an annual revenue of $450 million with 15% year-over-year growth.

Major customers include:
- Acme Corporation: $50 million annual contract for cloud infrastructure
- Globex Industries: $30 million for AI-powered analytics platform
- Initech Solutions: $25 million for hybrid cloud deployment

Key Projects:
1. Project Apollo: AI-driven customer analytics platform
   - Status: In development
   - Expected delivery: Q2 2024
   - Revenue impact: $75 million
   - Risk level: Medium (technical complexity)

2. Project Zeus: Next-gen cloud infrastructure
   - Status: Production
   - Monthly recurring revenue: $12 million
   - Customer: Acme Corporation
   - SLA compliance: 99.99%

Revenue at Risk:
- TechCorp has $125 million in revenue at risk due to:
  - Project Apollo delays could impact Q2 targets
  - Acme Corporation considering competitive solutions
  - SLA penalties if uptime drops below 99.9%

Customer Relationships:
- Acme Corporation is TechCorp's largest customer, accounting for 20% of total revenue
- Globex Industries has been a customer since 2015 with high satisfaction scores
- Initech Solutions is exploring expansion of services, potential $15 million opportunity

Team Structure:
- Engineering: 250 employees led by Director of Engineering Lisa Wang
- Sales: 80 employees led by VP of Sales Robert Taylor
- Customer Success: 45 employees led by Director CS Amanda Martinez

Competitive Landscape:
- Main competitors: CloudFirst, AIVentures, and DataSync
- TechCorp holds 15% market share in enterprise cloud solutions
- Unique differentiator: Integrated AI capabilities with cloud infrastructure
"""

# Schema for knowledge graph
ENTITY_TYPES = [
    {"label": "Company", "description": "Business organization or corporation"},
    {"label": "Person", "description": "Individual person, employee, or founder"},
    {"label": "Project", "description": "Business project or initiative", 
     "properties": [
         {"name": "status", "type": "STRING"},
         {"name": "revenue_impact", "type": "STRING"},
         {"name": "risk_level", "type": "STRING"}
     ]},
    {"label": "Customer", "description": "Client company or customer organization"},
    {"label": "Product", "description": "Product or service offering"},
    {"label": "Department", "description": "Organizational department or team"}
]

RELATIONSHIP_TYPES = [
    {"label": "FOUNDED_BY", "description": "Founder relationship"},
    {"label": "HAS_CUSTOMER", "description": "Customer relationship"},
    {"label": "WORKS_ON", "description": "Working on project"},
    {"label": "MANAGES", "description": "Management relationship"},
    {"label": "COMPETES_WITH", "description": "Competitive relationship"},
    {"label": "HAS_CONTRACT", "description": "Contract relationship",
     "properties": [{"name": "value", "type": "STRING"}]}
]

PATTERNS = [
    ("Company", "FOUNDED_BY", "Person"),
    ("Company", "HAS_CUSTOMER", "Customer"),
    ("Company", "WORKS_ON", "Project"),
    ("Person", "MANAGES", "Department"),
    ("Company", "COMPETES_WITH", "Company"),
    ("Customer", "HAS_CONTRACT", "Company")
]


class QueryRequest(BaseModel):
    query: str
    retriever_type: Optional[str] = "hybrid"  # hybrid, text2cypher, hybrid_cypher
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    answer: str
    context_items: int
    retriever_type: str


class HybridRAGSystem:
    """Complete Hybrid RAG system using neo4j-graphrag-python"""
    
    def __init__(self):
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")
        self.llm = OpenAILLM(
            model_name="gpt-4",
            model_params={"temperature": 0.7}
        )
        self.retrievers = {}
        self.rag_pipelines = {}
        
    async def initialize(self):
        """Initialize the system: build KG, create indexes, setup retrievers"""
        logger.info("Initializing Hybrid RAG System...")
        
        # Step 1: Build Knowledge Graph
        await self._build_knowledge_graph()
        
        # Step 2: Create Indexes
        self._create_indexes()
        
        # Step 3: Setup Retrievers
        self._setup_retrievers()
        
        logger.info("Hybrid RAG System initialized successfully!")
    
    async def _build_knowledge_graph(self):
        """Build knowledge graph from business data"""
        logger.info("Building knowledge graph...")
        
        kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            schema={
                "node_types": ENTITY_TYPES,
                "relationship_types": RELATIONSHIP_TYPES,
                "patterns": PATTERNS
            },
            from_pdf=False,
            neo4j_database=NEO4J_DATABASE
        )
        
        # Run the pipeline
        result = await kg_builder.run_async(text=BUSINESS_DATA)
        logger.info(f"Knowledge graph built: {result}")
        
    def _create_indexes(self):
        """Create vector and fulltext indexes"""
        logger.info("Creating indexes...")
        
        # Create vector index for embeddings
        try:
            create_vector_index(
                self.driver,
                VECTOR_INDEX_NAME,
                label="__Chunk__",
                embedding_property="embedding",
                dimensions=1536,  # OpenAI embedding dimension
                similarity_fn="cosine"
            )
            logger.info(f"Created vector index: {VECTOR_INDEX_NAME}")
        except Exception as e:
            logger.warning(f"Vector index might already exist: {e}")
        
        # Create fulltext index for text search
        try:
            create_fulltext_index(
                self.driver,
                FULLTEXT_INDEX_NAME,
                label="__Chunk__",
                node_properties=["text"]
            )
            logger.info(f"Created fulltext index: {FULLTEXT_INDEX_NAME}")
        except Exception as e:
            logger.warning(f"Fulltext index might already exist: {e}")
    
    def _setup_retrievers(self):
        """Setup different retriever types"""
        logger.info("Setting up retrievers...")
        
        # 1. Hybrid Retriever - combines vector and fulltext search
        self.retrievers["hybrid"] = HybridRetriever(
            driver=self.driver,
            vector_index_name=VECTOR_INDEX_NAME,
            fulltext_index_name=FULLTEXT_INDEX_NAME,
            embedder=self.embedder,
            neo4j_database=NEO4J_DATABASE
        )
        
        # 2. Hybrid Cypher Retriever - adds graph traversal
        retrieval_query = """
        // Find related entities through graph traversal
        MATCH (node)-[r]-(related)
        WHERE related:Company OR related:Customer OR related:Project
        RETURN node.text as text, 
               collect(DISTINCT related.name) as related_entities,
               collect(DISTINCT type(r)) as relationship_types
        """
        
        self.retrievers["hybrid_cypher"] = HybridCypherRetriever(
            driver=self.driver,
            vector_index_name=VECTOR_INDEX_NAME,
            fulltext_index_name=FULLTEXT_INDEX_NAME,
            retrieval_query=retrieval_query,
            embedder=self.embedder,
            neo4j_database=NEO4J_DATABASE
        )
        
        # 3. Text2Cypher Retriever - natural language to Cypher
        self.retrievers["text2cypher"] = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_database=NEO4J_DATABASE
        )
        
        # Create GraphRAG pipelines for each retriever
        for name, retriever in self.retrievers.items():
            self.rag_pipelines[name] = GraphRAG(
                retriever=retriever,
                llm=self.llm
            )
            
        logger.info(f"Setup {len(self.retrievers)} retrievers")
    
    async def query(self, query: str, retriever_type: str = "hybrid", top_k: int = 5) -> dict:
        """Execute a query using specified retriever"""
        if retriever_type not in self.rag_pipelines:
            raise ValueError(f"Unknown retriever type: {retriever_type}")
        
        logger.info(f"Executing query with {retriever_type} retriever: {query}")
        
        # Execute query
        result = self.rag_pipelines[retriever_type].search(
            query_text=query,
            return_context=True,
            retriever_config={"top_k": top_k}
        )
        
        # Extract context count
        context_count = 0
        if hasattr(result, 'retriever_result') and result.retriever_result:
            context_count = len(result.retriever_result.items)
        
        return {
            "answer": result.answer,
            "context_items": context_count,
            "retriever_type": retriever_type
        }
    
    def close(self):
        """Close driver connection"""
        self.driver.close()


# FastAPI Application
app = FastAPI(title="Hybrid Agentic RAG API")
rag_system = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    rag_system = HybridRAGSystem()
    await rag_system.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if rag_system:
        rag_system.close()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Hybrid Agentic RAG"}


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a query against the knowledge graph"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        result = await rag_system.query(
            query=request.query,
            retriever_type=request.retriever_type,
            top_k=request.top_k
        )
        
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# CLI Testing Function
async def test_queries():
    """Test the system with sample queries"""
    system = HybridRAGSystem()
    await system.initialize()
    
    test_cases = [
        # Business queries that should use hybrid search
        ("What is the revenue at risk for TechCorp?", "hybrid"),
        ("Which customers have contracts with TechCorp?", "hybrid"),
        ("Tell me about Project Apollo status and risks", "hybrid"),
        
        # Graph traversal queries
        ("Show me all projects and their related customers", "hybrid_cypher"),
        ("What are the relationships between TechCorp and its customers?", "hybrid_cypher"),
        
        # Natural language to Cypher
        ("Find all companies founded by Sarah Johnson", "text2cypher"),
        ("List all projects with their status", "text2cypher"),
    ]
    
    print("\n" + "="*80)
    print("HYBRID AGENTIC RAG TEST RESULTS")
    print("="*80 + "\n")
    
    for query, retriever_type in test_cases:
        print(f"Query: {query}")
        print(f"Retriever: {retriever_type}")
        
        result = await system.query(query, retriever_type)
        
        print(f"Answer: {result['answer']}")
        print(f"Context items: {result['context_items']}")
        print("-"*80 + "\n")
    
    system.close()


if __name__ == "__main__":
    # For testing, run the test queries
    # asyncio.run(test_queries())
    
    # For production, run the FastAPI server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)