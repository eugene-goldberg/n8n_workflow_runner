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

app = FastAPI(title="Agentic RAG Demo - Visual Interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration - pointing to our n8n Agentic RAG webhook
AGENTIC_RAG_WEBHOOK = "https://n8n.srv928466.hstgr.cloud/webhook/spyro-rag-advanced"
DIRECT_API_URL = "http://localhost:8058"  # For direct API calls if needed

# Models
class ChatMessage(BaseModel):
    query: str
    session_id: Optional[str] = None

class RAGResponse(BaseModel):
    success: bool
    answer: str
    session_id: str
    timestamp: str
    metadata: Dict[str, Any]
    tools_used: List[Dict[str, Any]]
    sources: Optional[List[Dict[str, Any]]] = []

class SearchVisualization(BaseModel):
    type: str  # "vector", "graph", "hybrid"
    query: str
    results: List[Dict[str, Any]]
    score: Optional[float] = None

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
        "message": "Agentic RAG Demo API",
        "endpoints": {
            "/chat": "POST - Send a query to Agentic RAG",
            "/health": "GET - Check API health",
            "/sessions/{session_id}": "GET - Get session history",
            "/ws": "WebSocket - Real-time updates"
        }
    }

@app.get("/health")
async def health_check():
    # Check if we can reach the n8n webhook
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try a simple request to check connectivity
            response = await client.post(
                AGENTIC_RAG_WEBHOOK,
                json={"query": "test", "max_tokens": 1}
            )
            webhook_status = response.status_code < 500
    except:
        webhook_status = False
    
    return {
        "status": "healthy",
        "webhook_reachable": webhook_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat")
async def chat(message: ChatMessage):
    """Send a query to the Agentic RAG system via n8n webhook"""
    
    # Generate session ID if not provided
    if not message.session_id:
        message.session_id = str(uuid.uuid4())
    
    # Broadcast query start to WebSocket clients
    await manager.broadcast_json({
        "type": "query_start",
        "query": message.query,
        "session_id": message.session_id,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send to n8n webhook
            response = await client.post(
                AGENTIC_RAG_WEBHOOK,
                json={
                    "query": message.query,
                    "session_id": message.session_id,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Webhook returned error: {response.text}"
                )
            
            result = response.json()
            
            # Parse tools used for visualization
            tools_visualization = []
            for tool in result.get("tools_used", []):
                viz = {
                    "type": tool.get("name", "unknown"),
                    "query": tool.get("query", ""),
                    "purpose": tool.get("purpose", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                tools_visualization.append(viz)
                
                # Broadcast tool usage to WebSocket
                await manager.broadcast_json({
                    "type": "tool_used",
                    "tool": viz,
                    "session_id": message.session_id
                })
            
            # Store in session history
            if message.session_id not in sessions:
                sessions[message.session_id] = []
            
            sessions[message.session_id].append({
                "query": message.query,
                "response": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Broadcast complete response
            await manager.broadcast_json({
                "type": "response_complete",
                "response": result,
                "session_id": message.session_id,
                "tools_visualization": tools_visualization
            })
            
            return result
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error calling webhook: {str(e)}")
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
    """Analyze which tools would be used for a query without executing it"""
    # This is a mock endpoint - in a real implementation, you might have a separate
    # analysis endpoint that predicts tool usage
    
    keywords_vector = ["features", "description", "what is", "explain"]
    keywords_graph = ["relationship", "connected", "which", "uses", "has risk"]
    
    predicted_tools = []
    
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in keywords_vector):
        predicted_tools.append({
            "tool": "vector_search",
            "probability": 0.8,
            "reason": "Query contains semantic/descriptive terms"
        })
    
    if any(kw in query_lower for kw in keywords_graph):
        predicted_tools.append({
            "tool": "graph_search",
            "probability": 0.9,
            "reason": "Query asks about relationships or connections"
        })
    
    if not predicted_tools:
        predicted_tools.append({
            "tool": "hybrid_search",
            "probability": 0.7,
            "reason": "Query type unclear, using both methods"
        })
    
    return {
        "query": query,
        "predicted_tools": predicted_tools,
        "explanation": "Tool prediction based on query analysis"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)