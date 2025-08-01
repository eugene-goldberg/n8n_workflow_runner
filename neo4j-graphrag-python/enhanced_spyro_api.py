#!/usr/bin/env python3
"""
Enhanced FastAPI implementation for SpyroSolutions Agentic RAG
Includes authentication, request validation, logging, and comprehensive endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import time
import os
from contextlib import asynccontextmanager

from spyro_semantic_model_implementation import SpyroSemanticRAG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global system instance
rag_system = None

# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="The question to ask")
    use_cypher: bool = Field(default=False, description="Use graph traversal for complex queries")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context items to retrieve")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Which customers are at risk?",
                "use_cypher": True,
                "top_k": 5
            }
        }

class QueryResponse(BaseModel):
    question: str
    answer: str
    context_items: int
    retriever_type: str
    processing_time_ms: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    model: str
    neo4j_connected: bool
    indexes_available: List[str]
    node_count: int
    timestamp: datetime

class SystemStats(BaseModel):
    total_queries: int
    average_response_time_ms: float
    queries_by_retriever: Dict[str, int]
    most_recent_queries: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime

# Tracking metrics
query_metrics = {
    "total_queries": 0,
    "total_response_time": 0,
    "queries_by_retriever": {"hybrid": 0, "hybrid_cypher": 0},
    "recent_queries": []
}

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global rag_system
    logger.info("Starting SpyroSolutions Agentic RAG API...")
    
    try:
        rag_system = SpyroSemanticRAG()
        await rag_system.build_knowledge_graph()
        rag_system.setup_retrievers()
        logger.info("System initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if rag_system:
        rag_system.close()

# Create FastAPI app
app = FastAPI(
    title="SpyroSolutions Agentic RAG API",
    description="Hybrid RAG system for SpyroSolutions business intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key authentication (for production, use proper auth)
API_KEY = os.getenv("SPYRO_API_KEY", "spyro-secret-key-123")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") else None,
            "timestamp": datetime.now().isoformat()
        }
    )

# Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SpyroSolutions Agentic RAG API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/query",
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Comprehensive health check"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Check Neo4j connection
        with rag_system.driver.session() as session:
            # Get node count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            
            # Get indexes
            indexes = []
            result = session.run("SHOW INDEXES")
            for record in result:
                if record['type'] in ['VECTOR', 'FULLTEXT']:
                    indexes.append(f"{record['name']} ({record['type']})")
        
        return HealthResponse(
            status="healthy",
            model="SpyroSolutions Semantic Model",
            neo4j_connected=True,
            indexes_available=indexes,
            node_count=node_count,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            model="SpyroSolutions Semantic Model",
            neo4j_connected=False,
            indexes_available=[],
            node_count=0,
            timestamp=datetime.now()
        )

@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def execute_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Execute a query against the knowledge graph"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    
    try:
        # Execute query
        result = await rag_system.query(
            request.question, 
            request.use_cypher
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Update metrics
        query_metrics["total_queries"] += 1
        query_metrics["total_response_time"] += processing_time
        query_metrics["queries_by_retriever"][result["retriever_type"]] += 1
        
        # Keep last 10 queries
        query_metrics["recent_queries"].append(request.question)
        if len(query_metrics["recent_queries"]) > 10:
            query_metrics["recent_queries"].pop(0)
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            context_items=result["context_items"],
            retriever_type=result["retriever_type"],
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=SystemStats, tags=["Statistics"])
async def get_statistics(api_key: str = Depends(verify_api_key)):
    """Get system usage statistics"""
    avg_response_time = 0
    if query_metrics["total_queries"] > 0:
        avg_response_time = query_metrics["total_response_time"] / query_metrics["total_queries"]
    
    return SystemStats(
        total_queries=query_metrics["total_queries"],
        average_response_time_ms=avg_response_time,
        queries_by_retriever=query_metrics["queries_by_retriever"],
        most_recent_queries=query_metrics["recent_queries"]
    )

@app.post("/batch_query", tags=["Query"])
async def batch_query(
    queries: List[QueryRequest],
    api_key: str = Depends(verify_api_key)
):
    """Execute multiple queries in batch"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if len(queries) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 queries per batch")
    
    results = []
    for query_request in queries:
        try:
            start_time = time.time()
            result = await rag_system.query(
                query_request.question,
                query_request.use_cypher
            )
            processing_time = (time.time() - start_time) * 1000
            
            results.append({
                "question": result["question"],
                "answer": result["answer"],
                "context_items": result["context_items"],
                "retriever_type": result["retriever_type"],
                "processing_time_ms": processing_time,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "question": query_request.question,
                "answer": None,
                "error": str(e),
                "status": "error"
            })
    
    return {"results": results, "timestamp": datetime.now()}

@app.get("/graph/stats", tags=["Graph"])
async def graph_statistics(api_key: str = Depends(verify_api_key)):
    """Get statistics about the knowledge graph"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    with rag_system.driver.session() as session:
        # Get entity counts
        entity_counts = {}
        result = session.run("""
            MATCH (n)
            WHERE n:Product OR n:Customer OR n:Project OR n:Team 
               OR n:Risk OR n:SaaSSubscription
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
        """)
        for record in result:
            entity_counts[record["label"]] = record["count"]
        
        # Get relationship counts
        relationship_counts = {}
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        for record in result:
            relationship_counts[record["type"]] = record["count"]
        
        return {
            "entity_counts": entity_counts,
            "relationship_counts": relationship_counts,
            "total_nodes": sum(entity_counts.values()),
            "total_relationships": sum(relationship_counts.values())
        }

# Example queries endpoint
@app.get("/examples", tags=["Examples"])
async def get_example_queries():
    """Get example queries for testing"""
    return {
        "examples": [
            {
                "category": "Product Information",
                "queries": [
                    {"question": "What products does SpyroSolutions offer?", "use_cypher": False},
                    {"question": "What are the SLAs for each product?", "use_cypher": True}
                ]
            },
            {
                "category": "Customer Analysis",
                "queries": [
                    {"question": "Which customers are at risk?", "use_cypher": True},
                    {"question": "What is the customer success score for each customer?", "use_cypher": False}
                ]
            },
            {
                "category": "Financial Metrics",
                "queries": [
                    {"question": "What is the total ARR?", "use_cypher": True},
                    {"question": "Which projects have the highest profitability impact?", "use_cypher": True}
                ]
            },
            {
                "category": "Risk Assessment",
                "queries": [
                    {"question": "What risks are affecting our customers?", "use_cypher": True},
                    {"question": "Which customers have high risk levels?", "use_cypher": True}
                ]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)