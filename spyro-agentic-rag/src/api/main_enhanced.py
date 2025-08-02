"""
FastAPI application for SpyroSolutions Agentic RAG with schema source tracking
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..agents.spyro_agent_enhanced_fixed import create_agent, SpyroAgentEnhanced as SpyroAgent
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
        logger.info("SpyroSolutions Agentic RAG API (Enhanced) started successfully")
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
    title="SpyroSolutions Agentic RAG API (Enhanced)",
    description="LLM-powered agent with schema source tracking",
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
    agent_type: str
    model: str
    execution_time_seconds: float
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    tools_available: List[str]
    session_id: Optional[str]
    timestamp: str
    schema_support: str = "Dual (Spyro RAG + LlamaIndex)"


class EntitySource(BaseModel):
    """Information about an entity's source schema"""
    entity: str
    schema: str
    labels: List[str]


class SchemaSources(BaseModel):
    """Information about which schemas were accessed"""
    schemas_accessed: List[str] = Field(
        description="List of schemas that were queried (e.g., ['Spyro RAG', 'LlamaIndex'])"
    )
    entity_count_by_schema: Dict[str, int] = Field(
        description="Count of entities retrieved from each schema"
    )
    sample_entities: List[EntitySource] = Field(
        description="Sample entities showing their source schemas"
    )
    query_patterns: List[str] = Field(
        description="Types of queries executed (e.g., 'Graph Query', 'Vector Search')"
    )


class QueryResponse(BaseModel):
    """Enhanced response model with schema tracking"""
    query: str
    answer: str
    metadata: QueryMetadata
    schema_sources: Optional[SchemaSources] = Field(
        None,
        description="Information about which data sources were accessed"
    )
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_ready: bool
    capabilities: List[str]
    timestamp: str
    schema_support: str = "Dual (Spyro RAG + LlamaIndex)"


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
            "multi_tool_execution",
            "schema_source_tracking",
            "dual_schema_support"
        ],
        timestamp=datetime.now().isoformat()
    )


@app.post("/query", response_model=QueryResponse)
async def execute_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Execute an agentic query with schema source tracking.
    
    The agent will:
    1. Analyze your query to understand intent
    2. Autonomously select appropriate retrieval tools
    3. Execute selected tools (potentially multiple)
    4. Track which data sources (Spyro RAG vs LlamaIndex) were accessed
    5. Synthesize a comprehensive answer with source information
    
    The response includes:
    - answer: The synthesized response
    - schema_sources: Information about which data sources contributed to the answer
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
        
        # Create response with schema tracking
        response = QueryResponse(
            query=result["query"],
            answer=result["answer"],
            metadata=QueryMetadata(**result["metadata"])
        )
        
        # Add schema sources if available
        if "schema_sources" in result:
            response.schema_sources = SchemaSources(**result["schema_sources"])
            
        return response
        
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
        "selection_method": "autonomous (OpenAI Functions)",
        "schema_support": "Dual (Spyro RAG + LlamaIndex)"
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get detailed system capabilities"""
    return {
        "system": "SpyroSolutions Agentic RAG (Enhanced)",
        "version": "2.0.0",
        "description": "LLM-powered agent with autonomous tool selection and schema source tracking",
        "features": {
            "autonomous_tool_selection": {
                "description": "Agent analyzes queries and selects appropriate tools",
                "method": "LangChain with OpenAI Functions"
            },
            "schema_source_tracking": {
                "description": "Tracks which data sources (Spyro RAG vs LlamaIndex) contribute to answers",
                "provides": [
                    "schemas_accessed: List of schemas queried",
                    "entity_count_by_schema: Distribution of results",
                    "sample_entities: Examples with their source schemas",
                    "query_patterns: Types of searches performed"
                ]
            },
            "retrieval_tools": {
                "GraphQuery": "Direct graph queries for entities and relationships",
                "HybridSearch": "Combined vector and keyword search",
                "VectorSearch": "Semantic similarity search",
                "UnifiedSearch": "Automatic schema-aware search"
            },
            "conversation_memory": "Maintains context across multiple queries",
            "parallel_execution": "Can execute multiple tools for comprehensive results"
        },
        "data_sources": {
            "Spyro RAG": {
                "description": "Original data using labels like :Customer, :Product",
                "examples": ["TechCorp", "FinanceHub", "CloudFirst"]
            },
            "LlamaIndex": {
                "description": "Data from document ingestion using labels like :__Entity__:CUSTOMER",
                "examples": ["InnovateTech Solutions", "Global Manufacturing Corp"]
            }
        },
        "knowledge_domains": [
            "Products (SpyroCloud, SpyroAI, SpyroSecure)",
            "Customer subscriptions and success metrics",
            "Financial data (ARR, costs, profitability)",
            "Teams, projects, and operations",
            "Risks, objectives, and business metrics"
        ],
        "api_endpoints": [
            "POST /query - Execute query with source tracking",
            "GET /health - Health check",
            "GET /conversation - Get conversation history",
            "POST /conversation/clear - Clear memory",
            "GET /tools - List available tools",
            "GET /capabilities - This endpoint"
        ]
    }


@app.get("/schema/stats")
async def get_schema_stats(api_key: str = Depends(verify_api_key)):
    """Get statistics about data in each schema"""
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent not initialized"
        )
    
    try:
        with agent.driver.session() as session:
            # Count entities in each schema
            stats = {}
            
            # Spyro RAG counts
            result = session.run("""
                MATCH (n)
                WHERE 'Customer' IN labels(n) 
                   OR 'Product' IN labels(n) 
                   OR 'Team' IN labels(n)
                   OR 'Risk' IN labels(n)
                RETURN 'Spyro RAG' as schema, count(n) as total
            """)
            for r in result:
                stats[r['schema']] = {"total_entities": r['total']}
            
            # LlamaIndex counts
            result = session.run("""
                MATCH (n:__Entity__)
                RETURN 'LlamaIndex' as schema, count(n) as total
            """)
            for r in result:
                stats[r['schema']] = {"total_entities": r['total']}
            
            # Get entity type breakdown
            for schema_name in stats:
                if schema_name == "Spyro RAG":
                    result = session.run("""
                        MATCH (n)
                        WHERE 'Customer' IN labels(n) 
                           OR 'Product' IN labels(n) 
                           OR 'Team' IN labels(n)
                           OR 'Risk' IN labels(n)
                        UNWIND labels(n) as label
                        WHERE label IN ['Customer', 'Product', 'Team', 'Risk']
                        RETURN label, count(*) as count
                    """)
                else:  # LlamaIndex
                    result = session.run("""
                        MATCH (n:__Entity__)
                        UNWIND [l IN labels(n) WHERE l NOT IN ['__Entity__', '__Node__']] as label
                        RETURN label, count(*) as count
                    """)
                
                breakdown = {}
                for r in result:
                    breakdown[r['label']] = r['count']
                stats[schema_name]["entity_breakdown"] = breakdown
            
            return {
                "schema_statistics": stats,
                "total_entities": sum(s["total_entities"] for s in stats.values()),
                "schemas_available": list(stats.keys())
            }
            
    except Exception as e:
        logger.error(f"Schema stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving schema statistics: {str(e)}"
        )


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