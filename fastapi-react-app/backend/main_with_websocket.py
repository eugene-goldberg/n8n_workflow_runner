from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import httpx
import json
import logging
import asyncio

# Import our custom managers
from websocket_manager import ConnectionManager
from request_tracker import RequestTracker, RequestStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI Chat App with n8n Integration")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://srv928466.hstgr.cloud", "http://srv928466.hstgr.cloud:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
manager = ConnectionManager()
tracker = RequestTracker()

# Configuration
N8N_WEBHOOK_URL = "https://myhost.com/workflows/workflow1/"  # Update with your n8n webhook URL
CALLBACK_BASE_URL = "http://172.17.0.1:8000"  # Docker bridge network address for n8n container

# Existing models
class Item(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    completed: bool = False
    created_at: Optional[datetime] = None

# New models for chat and callbacks
class ChatMessage(BaseModel):
    type: str
    message: str

class CallbackData(BaseModel):
    correlation_id: str
    result: str
    user_id: Optional[str] = None
    error: Optional[str] = None

# Existing todo endpoints remain the same
items_db = []
item_counter = 1

@app.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Chat App!"}

@app.get("/api/items", response_model=List[Item])
def get_items():
    return items_db

@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    item = next((item for item in items_db if item.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/api/items", response_model=Item)
def create_item(item: Item):
    global item_counter
    item.id = item_counter
    item.created_at = datetime.now()
    item_counter += 1
    items_db.append(item)
    return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    for index, item in enumerate(items_db):
        if item.id == item_id:
            updated_item.id = item_id
            updated_item.created_at = item.created_at
            items_db[index] = updated_item
            return updated_item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    global items_db
    items_db = [item for item in items_db if item.id != item_id]
    return {"message": "Item deleted successfully"}

# WebSocket endpoint for chat
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = await manager.connect(websocket, user_id)
    
    # Send welcome message
    await manager.send_json_to_user({
        "type": "system",
        "message": "Connected to AI chat server",
        "timestamp": datetime.now().isoformat()
    }, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "chat_message":
                await handle_chat_message(user_id, message_data["message"])
            elif message_data.get("type") == "ping":
                # Respond to ping to keep connection alive
                await manager.send_json_to_user({"type": "pong"}, user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(connection_id)

async def handle_chat_message(user_id: str, message: str):
    """Handle incoming chat message from user"""
    try:
        # Create request with correlation ID
        correlation_id = tracker.create_request(user_id, message)
        
        # Send acknowledgment to user
        await manager.send_json_to_user({
            "type": "acknowledgment",
            "message": "I received your message and I'm processing it...",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat()
        }, user_id)
        
        # Trigger n8n workflow
        await trigger_n8n_workflow(
            message=message,
            correlation_id=correlation_id,
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        await manager.send_json_to_user({
            "type": "error",
            "message": "Sorry, I encountered an error processing your message.",
            "timestamp": datetime.now().isoformat()
        }, user_id)

async def trigger_n8n_workflow(message: str, correlation_id: str, user_id: str):
    """Trigger n8n workflow with correlation ID and callback URL"""
    try:
        # Update request status
        tracker.update_status(correlation_id, RequestStatus.PROCESSING)
        
        # Prepare workflow data
        workflow_data = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "callback_url": f"{CALLBACK_BASE_URL}/api/n8n-callback"
        }
        
        # Send to n8n webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=workflow_data,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Workflow returned status {response.status_code}")
                
            logger.info(f"Triggered n8n workflow for correlation_id: {correlation_id}")
            
    except Exception as e:
        logger.error(f"Failed to trigger n8n workflow: {e}")
        tracker.fail_request(correlation_id, str(e))
        
        # Notify user of failure
        await manager.send_json_to_user({
            "type": "error",
            "correlation_id": correlation_id,
            "message": "Failed to process your request. Please try again.",
            "timestamp": datetime.now().isoformat()
        }, user_id)

@app.post("/api/n8n-callback")
async def n8n_callback(data: CallbackData):
    """Receive results from n8n workflow"""
    try:
        # Get request info
        request_info = tracker.get_request(data.correlation_id)
        if not request_info:
            logger.error(f"Unknown correlation_id: {data.correlation_id}")
            raise HTTPException(status_code=404, detail="Request not found")
        
        user_id = data.user_id or request_info["user_id"]
        
        if data.error:
            # Handle error case
            tracker.fail_request(data.correlation_id, data.error)
            await manager.send_json_to_user({
                "type": "error",
                "correlation_id": data.correlation_id,
                "message": f"Error processing request: {data.error}",
                "timestamp": datetime.now().isoformat()
            }, user_id)
        else:
            # Success case
            tracker.complete_request(data.correlation_id, data.result)
            
            # Send result to user via WebSocket
            await manager.send_json_to_user({
                "type": "chat_response",
                "correlation_id": data.correlation_id,
                "message": data.result,
                "timestamp": datetime.now().isoformat()
            }, user_id)
            
        return {"status": "success", "correlation_id": data.correlation_id}
        
    except Exception as e:
        logger.error(f"Error in n8n callback: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": len(manager.get_active_users()),
        "pending_requests": tracker.get_pending_count(),
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Run cleanup task periodically"""
    async def cleanup_task():
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            tracker.cleanup_old_requests()
            logger.info("Performed request cleanup")
            
    asyncio.create_task(cleanup_task())
    logger.info("FastAPI Chat App started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("FastAPI Chat App shutting down")

# Keep the old workflow endpoint for backward compatibility
@app.post("/api/workflow/execute")
async def execute_workflow():
    try:
        workflow_data = {
            "timestamp": datetime.now().isoformat(),
            "source": "FastAPI Todo App",
            "action": "manual_trigger"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=workflow_data,
                timeout=30.0
            )
            return {
                "status": "success",
                "workflow_response": {
                    "status_code": response.status_code,
                    "body": response.text
                }
            }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Workflow execution timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to execute workflow: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)