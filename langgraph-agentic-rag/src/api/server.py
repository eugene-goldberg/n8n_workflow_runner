"""FastAPI server for the agentic RAG system."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agents.main_agent import AgentRunner
from config.settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.app.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangGraph Agentic RAG API",
    description="Production-grade agentic RAG system with LangGraph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent runner
agent_runner = AgentRunner()


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for queries."""
    query: str
    session_id: Optional[str] = None
    thread_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for queries."""
    answer: str
    session_id: str
    thread_id: str
    metadata: Dict[str, Any]
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: str


# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a query through the agentic RAG system.
    
    Args:
        request: Query request containing the question and optional IDs
        
    Returns:
        Query response with answer and metadata
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        # Run the agent
        result = await agent_runner.run(
            query=request.query,
            session_id=request.session_id,
            thread_id=request.thread_id
        )
        
        # Build response
        response = QueryResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            thread_id=result["thread_id"],
            metadata=result["metadata"],
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Query processed successfully. Thread: {response.thread_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/continue", response_model=QueryResponse)
async def continue_conversation(request: QueryRequest):
    """Continue an existing conversation.
    
    Args:
        request: Query request with thread_id for continuity
        
    Returns:
        Query response continuing the conversation
    """
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required for continuing conversation")
    
    try:
        logger.info(f"Continuing conversation {request.thread_id}: {request.query[:100]}...")
        
        # Continue the conversation
        result = await agent_runner.continue_conversation(
            query=request.query,
            thread_id=request.thread_id,
            session_id=request.session_id
        )
        
        # Build response
        response = QueryResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            thread_id=result["thread_id"],
            metadata=result["metadata"],
            timestamp=datetime.utcnow().isoformat()
        )
        
        logger.info(f"Conversation continued successfully. Thread: {response.thread_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error continuing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting LangGraph Agentic RAG API...")
    # Validate settings
    settings.validate()
    logger.info("API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down API...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.environment == "development"
    )