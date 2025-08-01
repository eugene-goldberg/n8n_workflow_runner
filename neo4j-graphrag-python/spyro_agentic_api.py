#!/usr/bin/env python3
"""
SpyroSolutions Agentic RAG API
Uses neo4j-graphrag-python's tool calling for true agent-based retrieval
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

from spyro_agentic_rag import SpyroAgenticRAG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agent
    agent = SpyroAgenticRAG()
    logger.info("SpyroSolutions Agentic RAG initialized")
    yield
    # Shutdown
    if agent:
        agent.close()

# Create FastAPI app
app = FastAPI(
    title="SpyroSolutions Agentic RAG API",
    description="True agent-based RAG using neo4j-graphrag-python",
    version="4.0.0",
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

# Models
class QueryRequest(BaseModel):
    question: str
    # No more use_cypher flag - the agent decides everything!

class QueryResponse(BaseModel):
    question: str
    answer: str
    agent_reasoning: str
    tools_used: List[str]
    retrieval_summary: Dict[str, int]
    execution_time_seconds: float
    timestamp: datetime

# API key authentication
API_KEY = os.getenv("SPYRO_API_KEY", "spyro-secret-key-123")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Endpoints
@app.get("/health")
async def health_check():
    """Check API health"""
    return {
        "status": "healthy",
        "system": "neo4j-graphrag-agentic",
        "capabilities": [
            "autonomous_tool_selection",
            "vector_search",
            "hybrid_search",
            "text2cypher",
            "multi_tool_execution",
            "intelligent_synthesis"
        ],
        "timestamp": datetime.now()
    }

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """
    Execute an agentic query.
    
    The LLM agent will:
    1. Analyze your query
    2. Autonomously select appropriate retrieval tools
    3. Execute tools (potentially multiple in parallel)
    4. Synthesize a comprehensive answer
    
    No manual tool selection needed - the agent handles everything!
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Let the agent handle everything
        result = await agent.query(request.question)
        
        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            agent_reasoning=result["agent_reasoning"],
            tools_used=result["tools_used"],
            retrieval_summary=result["retrieval_summary"],
            execution_time_seconds=result["execution_time_seconds"],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities(api_key: str = Depends(verify_api_key)):
    """Get detailed information about the agentic system"""
    return {
        "description": "SpyroSolutions Agentic RAG powered by neo4j-graphrag-python",
        "agent_behavior": {
            "analysis": "LLM agent analyzes each query to understand intent",
            "tool_selection": "Agent autonomously selects appropriate retrieval tools",
            "multi_tool": "Agent can use multiple tools for comprehensive results",
            "synthesis": "Agent synthesizes results from all tools into coherent answer"
        },
        "available_tools": {
            "vector_search": {
                "description": "Semantic similarity search using embeddings",
                "best_for": ["conceptual questions", "finding similar content", "understanding context"]
            },
            "hybrid_search": {
                "description": "Combines vector and keyword search",
                "best_for": ["balanced queries", "semantic + specific terms"]
            },
            "text2cypher": {
                "description": "Natural language to Cypher graph queries",
                "best_for": ["specific entities", "relationships", "aggregations", "structured data"]
            }
        },
        "knowledge_graph_schema": {
            "entities": [
                "Product", "Customer", "SaaSSubscription", "AnnualRecurringRevenue",
                "Feature", "RoadmapItem", "Team", "Project", "Risk", "Objective",
                "CustomerSuccessScore", "Event", "OperationalCost", "Profitability"
            ],
            "relationships": [
                "SUBSCRIBES_TO", "HAS_FEATURE", "SUPPORTS", "AT_RISK", "USES",
                "GENERATES", "HAS_ROADMAP", "WORKS_ON", "HAS_SUCCESS_SCORE",
                "INFLUENCED_BY", "AFFECTS", "IMPACTS"
            ]
        },
        "powered_by": "neo4j-graphrag-python with OpenAI tool calling"
    }

@app.post("/debug")
async def debug_query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """
    Debug endpoint to see detailed agent decision-making process.
    Shows exactly how the agent analyzes and responds to queries.
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Execute query with detailed logging
        result = await agent.query(request.question)
        
        return {
            "query": request.question,
            "agent_analysis": {
                "reasoning": result["agent_reasoning"],
                "tools_selected": result["tools_used"],
                "execution_flow": "analyze → select tools → execute → synthesize"
            },
            "retrieval_details": result["retrieval_summary"],
            "final_answer": result["answer"],
            "execution_time": f"{result['execution_time_seconds']:.2f}s"
        }
    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)