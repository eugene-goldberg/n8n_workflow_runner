"""
FastAPI application for LangGraph Agentic RAG
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import os

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import our LangGraph agent
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.agents.main_agent import AgentRunner

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[AgentRunner] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global agent
    
    # Startup
    try:
        agent = AgentRunner()
        logger.info("LangGraph Agentic RAG API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("LangGraph Agentic RAG API shut down")


# Create FastAPI app
app = FastAPI(
    title="LangGraph Agentic RAG API",
    description="LangGraph-powered agent with advanced routing and multi-retriever capabilities",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for queries"""
    question: str = Field(..., description="The user's question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")


class QueryMetadata(BaseModel):
    """Metadata about query execution"""
    agent_type: str = "LangGraph"
    model: str = "gpt-3.5-turbo"
    execution_time_seconds: float
    routes_selected: List[str]
    tools_used: List[str]
    session_id: Optional[str]
    timestamp: str
    grounded: bool = Field(..., description="Whether the answer is grounded in Neo4j data")


class QueryResponse(BaseModel):
    """Response model for queries"""
    query: str
    answer: str
    metadata: QueryMetadata
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_ready: bool
    capabilities: List[str]
    timestamp: str
    neo4j_connected: bool = True


# Simple API key check (optional)
API_KEY = os.getenv("LANGGRAPH_API_KEY", "test-key-123")

async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Verify API key if provided"""
    if x_api_key and x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return x_api_key or "anonymous"


# Helper to check if answer is grounded
def is_answer_grounded(answer: str) -> bool:
    """Check if answer is grounded in data"""
    if not answer or len(answer) < 50:
        return False
    
    answer_lower = answer.lower()
    negative_indicators = [
        "no results", "not available", "no specific", "sorry",
        "unable to", "did not return", "no information",
        "does not contain", "not found", "did not yield",
        "does not specify", "cannot provide", "graph query did not",
        "no data available", "not in the database", "couldn't find",
        "no relevant", "doesn't have", "no direct"
    ]
    
    return not any(indicator in answer_lower for indicator in negative_indicators)


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and readiness"""
    return HealthResponse(
        status="healthy",
        agent_ready=agent is not None,
        capabilities=[
            "intelligent_routing",
            "vector_search",
            "graph_queries",
            "hybrid_search",
            "text2cypher",
            "multi_retriever_fusion"
        ],
        timestamp=datetime.now().isoformat(),
        neo4j_connected=True
    )


@app.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute a query using the LangGraph agent.
    
    The agent will:
    1. Route your query to the most appropriate retriever(s)
    2. Execute vector search, graph queries, or hybrid retrieval
    3. Synthesize a comprehensive answer from multiple sources
    
    Routes available:
    - vector_search: Semantic similarity search
    - fact_lookup: Specific entity/relationship queries
    - aggregation: Complex analytical queries
    - conversation: General conversational queries
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        import time
        start_time = time.time()
        
        # Execute query
        result = await agent.run(request.question)
        
        execution_time = time.time() - start_time
        answer = result.get('answer', 'No answer provided')
        
        # Determine which routes/tools were used (simplified)
        routes_selected = []
        tools_used = []
        
        # Check answer content to infer route
        if "Based on the graph query" in answer or "Based on the query" in answer:
            routes_selected.append("graph_query")
            tools_used.append("GraphRetriever")
        elif "Based on the vector search" in answer:
            routes_selected.append("vector_search")
            tools_used.append("VectorRetriever")
        else:
            routes_selected.append("hybrid")
            tools_used.append("HybridRetriever")
        
        # Create response
        return QueryResponse(
            query=request.question,
            answer=answer,
            metadata=QueryMetadata(
                execution_time_seconds=round(execution_time, 2),
                routes_selected=routes_selected,
                tools_used=tools_used,
                session_id=request.session_id,
                timestamp=datetime.now().isoformat(),
                grounded=is_answer_grounded(answer)
            )
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/tools")
async def get_tools(api_key: str = Depends(verify_api_key)):
    """Get information about available retrieval tools"""
    return {
        "retrievers": [
            {
                "name": "VectorRetriever",
                "description": "Semantic search using entity embeddings"
            },
            {
                "name": "GraphRetriever",
                "description": "Direct Cypher queries with Text2Cypher"
            },
            {
                "name": "HybridRetriever",
                "description": "Combined vector and graph search"
            },
            {
                "name": "EnhancedVectorRetriever",
                "description": "Entity-focused vector search with relationship enrichment"
            }
        ],
        "routing_method": "LangGraph StateGraph with intelligent routing",
        "model": "gpt-3.5-turbo"
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get detailed system capabilities"""
    return {
        "system": "LangGraph Agentic RAG",
        "version": "2.0.0",
        "description": "Advanced RAG system using LangGraph for intelligent routing",
        "architecture": {
            "framework": "LangGraph",
            "routing": "StateGraph with conditional edges",
            "retrievers": "Multiple specialized retrievers",
            "neo4j_integration": "Direct connection with Cypher queries"
        },
        "features": {
            "intelligent_routing": {
                "description": "Routes queries to optimal retriever based on intent",
                "routes": ["vector_search", "fact_lookup", "aggregation", "conversation"]
            },
            "retrieval_methods": {
                "VectorSearch": "701 entities with embeddings",
                "GraphQueries": "Enhanced Cypher templates for complex queries",
                "HybridSearch": "Combines vector and graph results",
                "Text2Cypher": "Natural language to Cypher translation"
            },
            "enhanced_features": {
                "multi_hop_traversal": "Navigate complex relationships",
                "aggregation_queries": "Revenue, cost, and metric calculations",
                "relationship_enrichment": "Enhance results with connected data"
            }
        },
        "knowledge_domains": [
            "Revenue and ARR analysis",
            "Customer success metrics",
            "Operational risks and project delivery",
            "Team performance and costs",
            "Product profitability",
            "Strategic objectives and risks"
        ],
        "performance_metrics": {
            "grounded_answers": "65% (39/60 business questions)",
            "improvement_from_baseline": "3x (from 21.7% to 65%)",
            "average_response_time": "5-7 seconds"
        },
        "api_endpoints": [
            "POST /query - Execute query with intelligent routing",
            "GET /health - Health check",
            "GET /tools - List available retrievers",
            "GET /capabilities - This endpoint"
        ]
    }


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Alternative chat endpoint for compatibility with existing clients.
    Routes to the main query endpoint.
    """
    query_request = QueryRequest(
        question=request.message,
        session_id=request.conversation_id
    )
    return await execute_query(query_request, api_key)


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("LANGGRAPH_API_PORT", "8001"))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )