from typing import Dict, List, Optional
from fastapi import WebSocket
import uuid
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Store active connections by connection_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Map user_id to connection_id for quick lookups
        self.user_sessions: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept WebSocket connection and return connection ID"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        # Store the connection
        self.active_connections[connection_id] = websocket
        self.user_sessions[user_id] = connection_id
        
        logger.info(f"User {user_id} connected with connection {connection_id}")
        return connection_id
        
    def disconnect(self, connection_id: str):
        """Remove connection when client disconnects"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            
            # Remove from user_sessions
            for user_id, conn_id in list(self.user_sessions.items()):
                if conn_id == connection_id:
                    del self.user_sessions[user_id]
                    logger.info(f"User {user_id} disconnected")
                    break
                    
    async def send_personal_message(self, message: str, user_id: str) -> bool:
        """Send message to specific user"""
        connection_id = self.user_sessions.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Clean up broken connection
                self.disconnect(connection_id)
                return False
        return False
        
    async def send_json_to_user(self, data: dict, user_id: str) -> bool:
        """Send JSON data to specific user"""
        return await self.send_personal_message(json.dumps(data), user_id)
            
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection {connection_id}: {e}")
                disconnected.append(connection_id)
                
        # Clean up broken connections
        for conn_id in disconnected:
            self.disconnect(conn_id)
            
    def get_active_users(self) -> List[str]:
        """Get list of currently connected user IDs"""
        return list(self.user_sessions.keys())
        
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is currently connected"""
        return user_id in self.user_sessions