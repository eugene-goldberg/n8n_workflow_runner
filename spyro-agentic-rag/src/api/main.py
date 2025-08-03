"""
FastAPI application for SpyroSolutions Agentic RAG
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..agents.spyro_agent_enhanced_v3 import SpyroAgentEnhanced as SpyroAgent, create_agent
from ..utils.config import Config
from ..utils.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)

# Global agent instance
agent: Optional[SpyroAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global agent
    
    # Startup
    try:
        config = Config.from_env()
        agent = create_agent(config)
        logger.info("SpyroSolutions Agentic RAG API started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise
    
    yield
    
    # Shutdown
    if agent:
        agent.close()
        logger.info("SpyroSolutions Agentic RAG API shut down")


# Create FastAPI app
app = FastAPI(
    title="SpyroSolutions Agentic RAG API",
    description="LLM-powered agent using LlamaIndex knowledge graph integration",
    version="1.0.0",
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
    agent_type: str
    model: str
    execution_time_seconds: float
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    tools_available: List[str]
    session_id: Optional[str]
    timestamp: str


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


class ConversationMessage(BaseModel):
    """Conversation history message"""
    role: str
    content: str


class ConversationResponse(BaseModel):
    """Conversation history response"""
    session_id: Optional[str]
    messages: List[ConversationMessage]
    message_count: int


# Authentication
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key"""
    config = Config()
    if x_api_key != config.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return x_api_key


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and readiness"""
    return HealthResponse(
        status="healthy",
        agent_ready=agent is not None,
        capabilities=[
            "autonomous_tool_selection",
            "vector_search",
            "hybrid_search",
            "graph_queries",
            "conversation_memory",
            "multi_tool_execution"
        ],
        timestamp=datetime.now().isoformat()
    )


@app.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute an agentic query.
    
    The agent will:
    1. Analyze your query to understand intent
    2. Autonomously select appropriate retrieval tools
    3. Execute selected tools (potentially multiple)
    4. Synthesize a comprehensive answer
    
    No manual tool selection needed!
    """
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        # Execute query
        result = agent.query(
            user_query=request.question,
            session_id=request.session_id
        )
        
        # Create response
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            metadata=QueryMetadata(**result["metadata"])
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/conversation", response_model=ConversationResponse)
async def get_conversation(
    session_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get conversation history"""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        history = agent.get_conversation_history()
        
        return ConversationResponse(
            session_id=session_id,
            messages=[
                ConversationMessage(role=msg["role"], content=msg["content"])
                for msg in history
            ],
            message_count=len(history)
        )
        
    except Exception as e:
        logger.error(f"Conversation retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation: {str(e)}"
        )


@app.post("/conversation/clear")
async def clear_conversation(api_key: str = Depends(verify_api_key)):
    """Clear conversation memory"""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        agent.clear_memory()
        return {"message": "Conversation memory cleared successfully"}
        
    except Exception as e:
        logger.error(f"Memory clear error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing memory: {str(e)}"
        )


@app.get("/tools")
async def get_tools(api_key: str = Depends(verify_api_key)):
    """Get information about available tools"""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    tools_info = []
    for tool in agent.tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description
        })
    
    return {
        "tools": tools_info,
        "agent_model": agent.config.agent_model,
        "selection_method": "autonomous (OpenAI Functions)"
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get detailed system capabilities"""
    return {
        "system": "SpyroSolutions Agentic RAG",
        "version": "1.0.0",
        "description": "LLM-powered agent using LlamaIndex knowledge graph integration",
        "schema": {
            "format": "LlamaIndex",
            "pattern": ":__Entity__:TYPE (e.g., :__Entity__:CUSTOMER)",
            "description": "All entities use LlamaIndex labeling convention"
        },
        "features": {
            "autonomous_tool_selection": {
                "description": "Agent analyzes queries and selects appropriate tools",
                "method": "LangChain with OpenAI Functions"
            },
            "retrieval_tools": {
                "GraphQuery": "Direct graph queries using LlamaIndex schema",
                "HybridSearch": "Combined vector and keyword search",
                "VectorSearch": "Semantic similarity search"
            },
            "conversation_memory": "Maintains context across multiple queries",
            "llamaindex_integration": "Native support for LlamaIndex document ingestion"
        },
        "knowledge_domains": [
            "Products (SpyroCloud, SpyroAI, SpyroSecure)",
            "Customer subscriptions and success metrics",
            "Financial data (ARR, costs, profitability)",
            "Teams, projects, and operations",
            "Risks, objectives, and business metrics"
        ],
        "api_endpoints": [
            "POST /query - Execute agentic query",
            "GET /health - Health check",
            "GET /conversation - Get conversation history",
            "POST /conversation/clear - Clear memory",
            "GET /tools - List available tools",
            "GET /capabilities - This endpoint"
        ]
    }


# Run the application
if __name__ == "__main__":
    import uvicorn
    
    config = Config()
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level=config.log_level.lower()
    )