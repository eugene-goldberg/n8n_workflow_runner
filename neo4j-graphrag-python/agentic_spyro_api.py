#!/usr/bin/env python3
"""
Agentic SpyroSolutions RAG API
Implements true agent-based tool selection and execution
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

from agentic_rag_system import AgenticRAG

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agentic system instance
agentic_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global agentic_system
    agentic_system = AgenticRAG()
    logger.info("Agentic RAG System initialized")
    yield
    # Shutdown
    if agentic_system:
        agentic_system.close()

# Create FastAPI app
app = FastAPI(
    title="SpyroSolutions Agentic RAG API",
    description="True agent-based RAG with intelligent tool selection",
    version="3.0.0",
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
    # No more use_cypher flag - the agent decides!

class ToolUsage(BaseModel):
    tool: str
    query: str
    items_retrieved: int
    execution_time_ms: float

class AgentDecision(BaseModel):
    tools_selected: List[str]
    reasoning: str
    specific_queries: Dict[str, str]

class QueryResponse(BaseModel):
    question: str
    answer: str
    agent_decision: AgentDecision
    tools_used: List[ToolUsage]
    total_execution_time_ms: float
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
        "system": "agentic",
        "capabilities": [
            "vector_search",
            "hybrid_search", 
            "text2cypher",
            "fulltext_search",
            "autonomous_tool_selection"
        ],
        "timestamp": datetime.now()
    }

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """
    Execute an agentic query
    The system will autonomously:
    1. Analyze the query
    2. Select appropriate tools
    3. Execute tools in parallel
    4. Synthesize comprehensive answer
    """
    if not agentic_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Let the agent handle everything
        result = await agentic_system.query(request.question)
        
        # Format tool usage information
        tools_used = []
        tool_start_time = datetime.now()
        
        for tool_name, summary in result['tool_results_summary'].items():
            tools_used.append(ToolUsage(
                tool=tool_name,
                query=result['agent_decision']['specific_queries'].get(
                    tool_name.lower().replace(' ', '_'), 
                    request.question
                ),
                items_retrieved=summary['items_retrieved'],
                execution_time_ms=result['execution_time_seconds'] * 1000 / len(result['tool_results_summary'])
            ))
        
        return QueryResponse(
            question=request.question,
            answer=result['answer'],
            agent_decision=AgentDecision(
                tools_selected=result['agent_decision']['tools_used'],
                reasoning=result['agent_decision']['reasoning'],
                specific_queries=result['agent_decision']['specific_queries']
            ),
            tools_used=tools_used,
            total_execution_time_ms=result['execution_time_seconds'] * 1000,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capabilities")
async def get_capabilities(api_key: str = Depends(verify_api_key)):
    """Get detailed information about system capabilities"""
    return {
        "description": "SpyroSolutions Agentic RAG System",
        "features": {
            "autonomous_tool_selection": "LLM agent analyzes queries and selects appropriate tools",
            "parallel_execution": "Multiple tools can be executed concurrently",
            "intelligent_synthesis": "Results from multiple tools are synthesized into comprehensive answers",
            "tool_optimization": "Agent creates tool-specific queries for better results"
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
                "description": "Natural language to graph queries", 
                "best_for": ["specific entities", "relationships", "aggregations", "structured data"]
            },
            "fulltext_search": {
                "description": "Keyword-based search",
                "best_for": ["exact terms", "names", "specific phrases"]
            }
        },
        "knowledge_graph_contains": [
            "Products (SpyroCloud, SpyroAI, SpyroSecure)",
            "Customers and subscriptions",
            "Teams and projects", 
            "Financial data (ARR, costs, profitability)",
            "Risks and objectives",
            "Features and roadmaps"
        ]
    }

@app.post("/explain")
async def explain_decision(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """
    Explain how the agent would handle a query without executing it
    Useful for understanding agent behavior
    """
    if not agentic_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Get agent's decision without executing tools
        decision = await agentic_system._decide_tools(request.question)
        
        return {
            "question": request.question,
            "agent_would": {
                "use_tools": [t.value for t in decision.tools],
                "reasoning": decision.reasoning,
                "specific_queries": decision.specific_queries
            },
            "explanation": f"For this query, the agent would use {len(decision.tools)} tool(s) because: {decision.reasoning}"
        }
    except Exception as e:
        logger.error(f"Explain error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)