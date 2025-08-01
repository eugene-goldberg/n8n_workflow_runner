from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import httpx
import json
import logging
import asyncio
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SpyroSolutions RAG Web Interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - pointing to our SpyroSolutions API
SPYRO_API_URL = "http://localhost:8000"
SPYRO_API_KEY = "spyro-secret-key-123"

# Models
class ChatMessage(BaseModel):
    query: str
    session_id: Optional[str] = None
    use_cypher: bool = False

class RAGResponse(BaseModel):
    success: bool
    answer: str
    session_id: str
    timestamp: str
    metadata: Dict[str, Any]
    tools_used: List[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]] = []

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_json(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Session storage
sessions: Dict[str, List[Dict[str, Any]]] = {}

@app.get("/")
async def root():
    return {
        "message": "SpyroSolutions RAG Web Interface",
        "endpoints": {
            "/chat": "POST - Send a query to SpyroSolutions RAG",
            "/health": "GET - Check API health",
            "/sessions/{session_id}": "GET - Get session history",
            "/ws": "WebSocket - Real-time updates",
            "/stats": "GET - Get system statistics"
        }
    }

@app.get("/health")
async def health_check():
    """Check health of both this API and the SpyroSolutions API"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{SPYRO_API_URL}/health",
                headers={"X-API-Key": SPYRO_API_KEY}
            )
            spyro_health = response.json() if response.status_code == 200 else None
    except:
        spyro_health = None
    
    return {
        "status": "healthy",
        "spyro_api_connected": spyro_health is not None,
        "spyro_api_status": spyro_health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat")
async def chat(message: ChatMessage):
    """Send a query to the SpyroSolutions RAG system"""
    
    # Generate session ID if not provided
    if not message.session_id:
        message.session_id = str(uuid.uuid4())
    
    # Broadcast query start to WebSocket clients
    await manager.broadcast_json({
        "type": "query_start",
        "query": message.query,
        "use_cypher": message.use_cypher,
        "session_id": message.session_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Determine which search type is being used
    search_type = "text2cypher" if message.use_cypher else "hybrid"
    
    # Simulate tool usage for visualization
    tools_used = []
    
    if message.use_cypher:
        # Text2Cypher tool
        tools_used.append({
            "name": "text2cypher",
            "purpose": "Converting natural language to Cypher query for graph database",
            "query": message.query,
            "call_id": str(uuid.uuid4())
        })
        await manager.broadcast_json({
            "type": "tool_used",
            "tool": tools_used[-1],
            "session_id": message.session_id
        })
    else:
        # Hybrid search tools
        tools_used.extend([
            {
                "name": "vector_search",
                "purpose": "Searching for semantically similar content",
                "query": message.query,
                "call_id": str(uuid.uuid4())
            },
            {
                "name": "fulltext_search",
                "purpose": "Searching for keyword matches",
                "query": message.query,
                "call_id": str(uuid.uuid4())
            }
        ])
        for tool in tools_used:
            await manager.broadcast_json({
                "type": "tool_used",
                "tool": tool,
                "session_id": message.session_id
            })
            await asyncio.sleep(0.5)  # Small delay for visualization
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call SpyroSolutions API
            response = await client.post(
                f"{SPYRO_API_URL}/query",
                json={
                    "question": message.query,
                    "use_cypher": message.use_cypher,
                    "top_k": 5
                },
                headers={"X-API-Key": SPYRO_API_KEY}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"SpyroSolutions API error: {response.text}"
                )
            
            result = response.json()
            
            # Format the response
            formatted_response = {
                "success": True,
                "answer": result["answer"],
                "session_id": message.session_id,
                "timestamp": result["timestamp"],
                "metadata": {
                    "search_type": search_type,
                    "response_time_ms": result.get("processing_time_ms", 0),
                    "tools_used_count": len(tools_used),
                    "context_items": result.get("context_items", 0),
                    "retriever_type": result.get("retriever_type", search_type)
                },
                "tools_used": tools_used,
                "sources": []
            }
            
            # Store in session history
            if message.session_id not in sessions:
                sessions[message.session_id] = []
            
            sessions[message.session_id].append({
                "query": message.query,
                "response": formatted_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Broadcast complete response
            await manager.broadcast_json({
                "type": "response_complete",
                "response": formatted_response,
                "session_id": message.session_id
            })
            
            return formatted_response
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error calling SpyroSolutions API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get the conversation history for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": sessions[session_id],
        "message_count": len(sessions[session_id])
    }

@app.get("/stats")
async def get_stats():
    """Get statistics from SpyroSolutions API"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{SPYRO_API_URL}/stats",
                headers={"X-API-Key": SPYRO_API_KEY}
            )
            if response.status_code == 200:
                return response.json()
    except:
        pass
    
    return {"error": "Unable to fetch statistics"}

@app.get("/graph/stats")
async def get_graph_stats():
    """Get graph statistics from SpyroSolutions API"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{SPYRO_API_URL}/graph/stats",
                headers={"X-API-Key": SPYRO_API_KEY}
            )
            if response.status_code == 200:
                return response.json()
    except:
        pass
    
    return {"error": "Unable to fetch graph statistics"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates during RAG processing"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_json({"type": "pong"}, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/analyze-tools")
async def analyze_tools(query: str):
    """Analyze which tools would be used for a query"""
    
    # Keywords that suggest different search types
    keywords_graph = ["which", "who", "relationship", "connected", "customers", "products", "teams", "ARR", "subscription"]
    keywords_vector = ["explain", "describe", "what is", "tell me about", "features", "capabilities"]
    
    predicted_tools = []
    query_lower = query.lower()
    
    # Check for graph-oriented queries
    if any(kw in query_lower for kw in keywords_graph):
        predicted_tools.append({
            "tool": "text2cypher",
            "probability": 0.9,
            "reason": "Query asks about specific entities and relationships"
        })
    
    # Check for semantic queries
    if any(kw in query_lower for kw in keywords_vector):
        predicted_tools.append({
            "tool": "hybrid_search",
            "probability": 0.8,
            "reason": "Query seeks descriptive or conceptual information"
        })
    
    # Default to hybrid if unclear
    if not predicted_tools:
        predicted_tools.append({
            "tool": "hybrid_search",
            "probability": 0.7,
            "reason": "General query - using hybrid search for best coverage"
        })
    
    return {
        "query": query,
        "predicted_tools": predicted_tools,
        "recommendation": predicted_tools[0]["tool"],
        "explanation": "Tool prediction based on query pattern analysis"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)