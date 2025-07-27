# Asynchronous Chat Implementation Plan
## FastAPI + React + n8n with WebSocket Communication

### Executive Summary
Transform the current synchronous HTTP-based workflow trigger into an asynchronous chat application using WebSockets for real-time communication. This will handle long-running n8n workflows (several minutes) without timeout issues.

### Architecture Overview

```
┌─────────────┐     WebSocket      ┌──────────────┐     HTTP POST     ┌─────────────┐
│   React     │ ←─────────────────→ │   FastAPI    │ ─────────────────→ │     n8n     │
│   Chat UI   │                     │   Backend    │                     │  Workflow   │
└─────────────┘                     └──────────────┘                     └─────────────┘
                                           ↑                                     │
                                           │         HTTP POST (callback)        │
                                           └─────────────────────────────────────┘
```

### Implementation Phases

## Phase 1: Backend WebSocket Infrastructure

### 1.1 Update FastAPI Dependencies
```python
# requirements.txt additions
websockets==12.0
python-socketio==5.11.0
python-multipart==0.0.9
redis==5.0.1  # For scaling WebSocket connections
```

### 1.2 Create WebSocket Manager
```python
# backend/websocket_manager.py
from typing import Dict, List
from fastapi import WebSocket
import uuid
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> connection_id
        
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.user_sessions[user_id] = connection_id
        return connection_id
        
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            # Remove from user_sessions
            for user_id, conn_id in list(self.user_sessions.items()):
                if conn_id == connection_id:
                    del self.user_sessions[user_id]
                    
    async def send_personal_message(self, message: str, user_id: str):
        connection_id = self.user_sessions.get(user_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await websocket.send_text(message)
            
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
```

### 1.3 Create Request Tracking System
```python
# backend/request_tracker.py
from typing import Dict, Optional
from datetime import datetime
import uuid

class RequestTracker:
    def __init__(self):
        self.pending_requests: Dict[str, dict] = {}
        
    def create_request(self, user_id: str, message: str) -> str:
        correlation_id = str(uuid.uuid4())
        self.pending_requests[correlation_id] = {
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        return correlation_id
        
    def get_request(self, correlation_id: str) -> Optional[dict]:
        return self.pending_requests.get(correlation_id)
        
    def complete_request(self, correlation_id: str, result: str):
        if correlation_id in self.pending_requests:
            self.pending_requests[correlation_id]["status"] = "completed"
            self.pending_requests[correlation_id]["result"] = result
            self.pending_requests[correlation_id]["completed_at"] = datetime.now().isoformat()
```

### 1.4 Update main.py with WebSocket Endpoints
```python
# Add to backend/main.py
from fastapi import WebSocket, WebSocketDisconnect
from websocket_manager import ConnectionManager
from request_tracker import RequestTracker

manager = ConnectionManager()
tracker = RequestTracker()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle chat message
            if message_data.get("type") == "chat_message":
                # Create correlation ID
                correlation_id = tracker.create_request(user_id, message_data["message"])
                
                # Send acknowledgment
                await manager.send_personal_message(
                    json.dumps({
                        "type": "acknowledgment",
                        "message": "Processing your request...",
                        "correlation_id": correlation_id
                    }),
                    user_id
                )
                
                # Trigger n8n workflow
                await trigger_n8n_workflow(
                    message=message_data["message"],
                    correlation_id=correlation_id,
                    user_id=user_id
                )
    except WebSocketDisconnect:
        manager.disconnect(connection_id)

async def trigger_n8n_workflow(message: str, correlation_id: str, user_id: str):
    """Trigger n8n workflow with correlation ID"""
    workflow_data = {
        "correlation_id": correlation_id,
        "user_id": user_id,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "callback_url": f"http://srv928466.hstgr.cloud:8080/api/n8n-callback"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            N8N_WEBHOOK_URL,
            json=workflow_data,
            timeout=30.0
        )
        return response

@app.post("/api/n8n-callback")
async def n8n_callback(data: dict):
    """Receive results from n8n workflow"""
    correlation_id = data.get("correlation_id")
    result = data.get("result")
    
    if not correlation_id:
        raise HTTPException(status_code=400, detail="Missing correlation_id")
        
    request_info = tracker.get_request(correlation_id)
    if not request_info:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Complete the request
    tracker.complete_request(correlation_id, result)
    
    # Send result to user via WebSocket
    await manager.send_personal_message(
        json.dumps({
            "type": "chat_response",
            "correlation_id": correlation_id,
            "message": result,
            "timestamp": datetime.now().isoformat()
        }),
        request_info["user_id"]
    )
    
    return {"status": "success"}
```

## Phase 2: Frontend Chat Interface

### 2.1 Install WebSocket Dependencies
```bash
cd fastapi-react-app/frontend
npm install socket.io-client react-markdown uuid
```

### 2.2 Create WebSocket Hook
```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useState, useCallback, useRef } from 'react';

interface Message {
  id: string;
  type: 'user' | 'bot' | 'system';
  content: string;
  timestamp: string;
  correlationId?: string;
}

export const useWebSocket = (userId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const websocketUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8080/ws';
    ws.current = new WebSocket(`${websocketUrl}/${userId}`);

    ws.current.onopen = () => {
      setIsConnected(true);
      addSystemMessage('Connected to chat server');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'acknowledgment':
          addSystemMessage(data.message);
          break;
        case 'chat_response':
          addBotMessage(data.message, data.correlation_id);
          break;
      }
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      addSystemMessage('Disconnected from chat server');
    };

    return () => {
      ws.current?.close();
    };
  }, [userId]);

  const sendMessage = useCallback((message: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      // Add user message to chat
      addUserMessage(message);
      
      // Send to server
      ws.current.send(JSON.stringify({
        type: 'chat_message',
        message: message
      }));
    }
  }, []);

  const addUserMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date().toISOString()
    }]);
  };

  const addBotMessage = (content: string, correlationId?: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'bot',
      content,
      timestamp: new Date().toISOString(),
      correlationId
    }]);
  };

  const addSystemMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'system',
      content,
      timestamp: new Date().toISOString()
    }]);
  };

  return {
    messages,
    sendMessage,
    isConnected
  };
};
```

### 2.3 Create Chat Component
```typescript
// frontend/src/components/Chat.tsx
import React, { useState, useRef, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import ReactMarkdown from 'react-markdown';
import './Chat.css';

interface ChatProps {
  userId: string;
}

export const Chat: React.FC<ChatProps> = ({ userId }) => {
  const [inputMessage, setInputMessage] = useState('');
  const { messages, sendMessage, isConnected } = useWebSocket(userId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (inputMessage.trim() && isConnected) {
      sendMessage(inputMessage);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>AI Assistant</h2>
        <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Connected' : '● Disconnected'}
        </span>
      </div>
      
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            {message.type === 'user' && <div className="message-sender">You</div>}
            {message.type === 'bot' && <div className="message-sender">AI Assistant</div>}
            {message.type === 'system' && <div className="message-sender">System</div>}
            
            <div className="message-content">
              {message.type === 'bot' ? (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              ) : (
                message.content
              )}
            </div>
            
            <div className="message-timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-container">
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={!isConnected}
          rows={3}
        />
        <button 
          onClick={handleSend} 
          disabled={!isConnected || !inputMessage.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
};
```

### 2.4 Add Chat Styles
```css
/* frontend/src/components/Chat.css */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 600px;
  max-width: 800px;
  margin: 0 auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #2c3e50;
  color: white;
}

.connection-status {
  font-size: 14px;
}

.connection-status.connected {
  color: #2ecc71;
}

.connection-status.disconnected {
  color: #e74c3c;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
}

.message {
  margin-bottom: 15px;
  padding: 10px 15px;
  border-radius: 8px;
  max-width: 70%;
}

.message.user {
  background-color: #3498db;
  color: white;
  margin-left: auto;
}

.message.bot {
  background-color: white;
  border: 1px solid #ddd;
}

.message.system {
  background-color: #ecf0f1;
  text-align: center;
  margin: 10px auto;
  font-size: 14px;
  font-style: italic;
}

.message-sender {
  font-weight: bold;
  margin-bottom: 5px;
  font-size: 14px;
}

.message-content {
  line-height: 1.5;
}

.message-timestamp {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 5px;
}

.input-container {
  display: flex;
  padding: 20px;
  background-color: white;
  border-top: 1px solid #ddd;
}

.input-container textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
}

.input-container button {
  margin-left: 10px;
  padding: 10px 20px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.input-container button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.input-container button:hover:not(:disabled) {
  background-color: #2980b9;
}
```

## Phase 3: Update n8n Workflow

### 3.1 Enhanced n8n Workflow Structure
```json
{
  "name": "AI Chat Workflow with Callback",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "ai-chat-webhook",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook-node",
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "values": {
          "string": [
            {
              "name": "correlation_id",
              "value": "={{$json.correlation_id}}"
            },
            {
              "name": "user_id",
              "value": "={{$json.user_id}}"
            },
            {
              "name": "message",
              "value": "={{$json.message}}"
            },
            {
              "name": "callback_url",
              "value": "={{$json.callback_url}}"
            }
          ]
        }
      },
      "id": "extract-data",
      "name": "Extract Request Data",
      "type": "n8n-nodes-base.set",
      "position": [450, 300]
    },
    {
      "parameters": {
        "resource": "chatCompletion",
        "model": "gpt-4",
        "messages": {
          "values": [
            {
              "role": "user",
              "content": "={{$node[\"Extract Request Data\"].json.message}}"
            }
          ]
        }
      },
      "id": "openai-node",
      "name": "OpenAI",
      "type": "n8n-nodes-base.openAi",
      "position": [650, 300]
    },
    {
      "parameters": {
        "url": "={{$node[\"Extract Request Data\"].json.callback_url}}",
        "method": "POST",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "correlation_id",
              "value": "={{$node[\"Extract Request Data\"].json.correlation_id}}"
            },
            {
              "name": "result",
              "value": "={{$json.choices[0].message.content}}"
            },
            {
              "name": "user_id",
              "value": "={{$node[\"Extract Request Data\"].json.user_id}}"
            }
          ]
        },
        "options": {}
      },
      "id": "callback-node",
      "name": "Send Result to Callback",
      "type": "n8n-nodes-base.httpRequest",
      "position": [850, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": {
          "success": true,
          "correlation_id": "={{$node[\"Extract Request Data\"].json.correlation_id}}"
        }
      },
      "id": "respond-webhook",
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [1050, 300]
    }
  ],
  "connections": {
    "Webhook Trigger": {
      "main": [[{ "node": "Extract Request Data", "type": "main", "index": 0 }]]
    },
    "Extract Request Data": {
      "main": [[{ "node": "OpenAI", "type": "main", "index": 0 }]]
    },
    "OpenAI": {
      "main": [[{ "node": "Send Result to Callback", "type": "main", "index": 0 }]]
    },
    "Send Result to Callback": {
      "main": [[{ "node": "Respond to Webhook", "type": "main", "index": 0 }]]
    }
  }
}
```

## Phase 4: Nginx WebSocket Configuration

### 4.1 Update Nginx Config
```nginx
# Update /etc/nginx/sites-available/fastapi-react-app
server {
    listen 8080;
    server_name srv928466.hstgr.cloud;

    # Serve React frontend
    location / {
        root /var/www/fastapi-react-app;
        try_files $uri /index.html;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Proxy API requests to FastAPI backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Phase 5: Environment Configuration

### 5.1 Update Frontend Environment
```bash
# frontend/.env.production
REACT_APP_API_URL=http://srv928466.hstgr.cloud:8080
REACT_APP_WS_URL=ws://srv928466.hstgr.cloud:8080/ws
```

### 5.2 Update App Integration
```typescript
// Update frontend/src/App.tsx
import { Chat } from './components/Chat';

function App() {
  const [showChat, setShowChat] = useState(false);
  const userId = localStorage.getItem('userId') || generateUserId();

  return (
    <div className="App">
      <header className="App-header">
        <h1>FastAPI + React Todo App with AI Chat</h1>
        
        <button 
          className="chat-toggle-button"
          onClick={() => setShowChat(!showChat)}
        >
          {showChat ? 'Hide Chat' : 'Open AI Chat'}
        </button>

        {showChat && <Chat userId={userId} />}
        
        {/* Existing todo functionality */}
      </header>
    </div>
  );
}
```

## Implementation Steps

### Step 1: Backend Updates
1. Add WebSocket dependencies to requirements.txt
2. Create websocket_manager.py
3. Create request_tracker.py
4. Update main.py with WebSocket endpoints and callback endpoint
5. Test WebSocket connections locally

### Step 2: Frontend Updates
1. Install WebSocket and chat dependencies
2. Create useWebSocket hook
3. Create Chat component with styles
4. Integrate Chat into main App
5. Test chat interface locally

### Step 3: n8n Workflow
1. Import new workflow JSON
2. Configure OpenAI or other AI service credentials
3. Update webhook URL in backend
4. Test workflow with callback

### Step 4: Deployment
1. Update nginx configuration for WebSocket support
2. Deploy backend changes
3. Build and deploy frontend
4. Test end-to-end flow

### Step 5: Testing & Monitoring
1. Test WebSocket reconnection logic
2. Test long-running workflows (>2 minutes)
3. Monitor for memory leaks in WebSocket connections
4. Add logging for debugging

## Key Benefits
- Real-time bidirectional communication
- No timeout issues for long-running workflows
- Better user experience with immediate acknowledgment
- Scalable architecture for multiple concurrent users
- Clean separation of concerns

## Security Considerations
1. Add authentication to WebSocket connections
2. Validate all incoming messages
3. Rate limit chat requests
4. Sanitize user input before sending to n8n
5. Use HTTPS/WSS in production

## Scaling Considerations
1. Use Redis for WebSocket session management across multiple servers
2. Implement connection pooling
3. Add load balancing for WebSocket connections
4. Monitor WebSocket connection limits