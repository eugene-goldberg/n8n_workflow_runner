# FastAPI + React + n8n AI Chat Deployment Guide

This document details the complete setup and deployment process for the FastAPI + React application with AI chat functionality and asynchronous n8n workflow integration on Hostinger VPS.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Local Development Setup](#local-development-setup)
3. [Application Architecture](#application-architecture)
4. [Hostinger VPS Deployment](#hostinger-vps-deployment)
5. [WebSocket Configuration](#websocket-configuration)
6. [n8n Webhook Integration](#n8n-webhook-integration)
7. [AI Chat Setup](#ai-chat-setup)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance](#maintenance)

## Project Overview

This project consists of:
- **Backend**: FastAPI application with REST API and WebSocket support
- **Frontend**: React TypeScript application with todo management and AI chat
- **Integration**: Asynchronous n8n webhook integration with callback mechanism
- **Deployment**: Nginx reverse proxy with WebSocket support on Hostinger VPS (Ubuntu 24.04)

### Key Features
- Todo CRUD operations (Create, Read, Update, Delete)
- AI-powered chat interface with real-time WebSocket communication
- Asynchronous workflow execution without timeout issues
- Correlation ID tracking for multiple concurrent requests
- Auto-reconnection and error handling
- Production-ready deployment with systemd and nginx

## Local Development Setup

### Prerequisites
- Python 3.11+ 
- Node.js 18+
- npm 9+

### Backend Setup
```bash
cd fastapi-react-app/backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Frontend Setup
```bash
cd fastapi-react-app/frontend
npm install
npm start
```

Frontend runs at: http://localhost:3000

## Application Architecture

### Backend Structure
```
fastapi-react-app/backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
└── venv/               # Virtual environment
```

#### Key Endpoints
- `GET /` - Welcome message
- `GET /api/items` - Get all todo items
- `GET /api/items/{id}` - Get specific item
- `POST /api/items` - Create new item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item
- `POST /api/workflow/execute` - Trigger n8n workflow

### Frontend Structure
```
fastapi-react-app/frontend/
├── src/
│   ├── App.tsx         # Main React component
│   ├── App.css         # Styling
│   └── index.tsx       # Entry point
├── public/             # Static assets
├── build/              # Production build
├── package.json        # Dependencies
├── .env.production     # Production environment variables
└── .env.example        # Environment template
```

### Environment Variables
Frontend uses `REACT_APP_API_URL` to configure the backend URL:
- Development: `http://localhost:8000`
- Production: `http://srv928466.hstgr.cloud:8080`

## Hostinger VPS Deployment

### Server Information
- **URL**: http://srv928466.hstgr.cloud:8080
- **OS**: Ubuntu 24.04
- **User**: root
- **Python**: 3.12.3
- **Node.js**: 18.19.1

### Deployment Architecture
```
Internet → Nginx (port 8080) → FastAPI (port 8000)
              ↓                    ↓
         React Static Files    WebSocket
                                  ↓
                              n8n Webhook
                                  ↓
                              AI Service
                                  ↓
                              Callback to FastAPI
```

### Initial Server Setup

1. **Clone Repository**
```bash
cd /root
git clone https://github.com/eugene-goldberg/n8n_workflow_runner.git
cd n8n_workflow_runner
```

2. **Run Automated Setup**
```bash
./setup-hostinger.sh
```

This script automatically:
- Sets up Python virtual environment
- Installs backend dependencies
- Creates systemd service for FastAPI
- Builds React frontend
- Configures nginx
- Starts all services

### Manual Deployment Steps

#### 1. Backend Setup
```bash
cd /root/n8n_workflow_runner/fastapi-react-app/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Systemd Service Configuration
The FastAPI backend runs as a systemd service (`/etc/systemd/system/fastapi.service`):

```ini
[Unit]
Description=FastAPI app
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/n8n_workflow_runner/fastapi-react-app/backend
Environment="PATH=/root/n8n_workflow_runner/fastapi-react-app/backend/venv/bin"
ExecStart=/root/n8n_workflow_runner/fastapi-react-app/backend/venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

#### 3. Frontend Build
```bash
cd /root/n8n_workflow_runner/fastapi-react-app/frontend
npm install
npm run build
```

#### 4. Nginx Configuration
Nginx serves the React app and proxies API requests (`/etc/nginx/sites-available/fastapi-react-app`):

```nginx
server {
    listen 8080;
    server_name srv928466.hstgr.cloud;

    # Serve React frontend
    location / {
        root /var/www/fastapi-react-app;
        try_files $uri /index.html;
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

### Port Configuration
- **Port 80**: Used by Docker (existing service)
- **Port 8080**: Nginx serving our application
- **Port 8000**: FastAPI backend (internal only)

### File Permissions Fix
Frontend files are served from `/var/www/fastapi-react-app` to avoid nginx permission issues with `/root` directory:

```bash
./fix-nginx-permissions.sh
```

## WebSocket Configuration

### Nginx WebSocket Support
The application requires special nginx configuration for WebSocket connections:

```nginx
# WebSocket support for chat
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket specific settings
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    proxy_connect_timeout 60s;
    proxy_buffering off;
}
```

### Update Nginx
```bash
./update-nginx-websocket.sh
```

## n8n Webhook Integration

### Basic Webhook (Todo App)
The original webhook integration for the todo app:

1. **Backend Endpoint**: `/api/workflow/execute`
2. **Webhook Data**:
```json
{
    "timestamp": "2025-07-26T21:45:00.000Z",
    "source": "FastAPI Todo App",
    "action": "manual_trigger"
}
```

### AI Chat Webhook (Async)
The new asynchronous webhook integration for AI chat:

1. **Backend Endpoint**: Triggered via WebSocket
2. **Webhook Data with Callback**:
```json
{
    "correlation_id": "unique-request-id",
    "user_id": "user-identifier",
    "message": "user's chat message",
    "timestamp": "2025-07-26T21:45:00.000Z",
    "callback_url": "http://srv928466.hstgr.cloud:8080/api/n8n-callback"
}
```

3. **Callback Response**:
```json
{
    "correlation_id": "unique-request-id",
    "user_id": "user-identifier",
    "result": "AI generated response"
}
```

### n8n Workflow Setup

1. **For Basic Webhook**: Import `n8n-webhook-workflow.json`
2. **For AI Chat**: Import `n8n-ai-chat-workflow-working.json` (recommended)
3. **Configuration Steps**:
   - Import the appropriate workflow JSON into n8n
   - Add your AI service (OpenAI, Claude, etc.) to the workflow
   - Get the webhook URL from the trigger node
   - Update `N8N_WEBHOOK_URL` in backend `main_with_websocket.py`
   - Set `CALLBACK_BASE_URL = "http://172.17.0.1:8000"` (Docker bridge network)
   - Activate the workflow
   - Restart FastAPI service

### Important n8n Configuration Notes

1. **Data Access**: Webhook data is in `items[0].json.body`
2. **Callback URL**: Use Docker bridge network address `172.17.0.1:8000`
3. **JSON Body**: Use expression mode or prepare payload in Code node
4. **Template Evaluation**: Avoid `{{}}` syntax in JSON body strings

### Updating Configuration
```python
# In main_with_websocket.py
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/abc123/ai-chat"
CALLBACK_BASE_URL = "http://172.17.0.1:8000"  # Docker bridge network for n8n container
```

## AI Chat Setup

### Backend Components

1. **WebSocket Manager** (`websocket_manager.py`):
   - Manages multiple concurrent WebSocket connections
   - Maps user IDs to connection IDs
   - Handles message broadcasting and disconnections

2. **Request Tracker** (`request_tracker.py`):
   - Tracks requests with correlation IDs
   - Manages request lifecycle (pending, processing, completed, failed)
   - Implements timeout handling
   - Provides request cleanup

3. **WebSocket Endpoint** (`/ws/{user_id}`):
   - Accepts WebSocket connections
   - Handles chat messages
   - Manages connection lifecycle

4. **Callback Endpoint** (`/api/n8n-callback`):
   - Receives results from n8n workflows
   - Routes responses to correct users via WebSocket

### Frontend Components

1. **useWebSocket Hook**:
   - Manages WebSocket connection
   - Auto-reconnection logic
   - Message handling
   - Connection state management

2. **Chat Component**:
   - Real-time chat interface
   - Message history
   - Connection status indicator
   - Multiple message types

### Deployment Steps

1. **Backend Migration**:
```bash
cd /root/n8n_workflow_runner/fastapi-react-app/backend
./migrate_to_websocket.sh
```

2. **Frontend Migration**:
```bash
cd /root/n8n_workflow_runner/fastapi-react-app/frontend
./migrate_to_chat.sh
```

3. **Complete Deployment**:
```bash
cd /root/n8n_workflow_runner
sudo ./deploy-async-chat.sh
```

## Troubleshooting

### Check Service Status
```bash
./check-services.sh
```

### View Logs
```bash
# FastAPI logs
journalctl -u fastapi -f

# Nginx logs
journalctl -u nginx -f
tail -f /var/log/nginx/error.log
```

### Common Issues and Solutions

1. **CORS Errors**
   - Ensure frontend URL is in CORS allowed origins
   - Current allowed origins: `localhost:3000`, `srv928466.hstgr.cloud`, `srv928466.hstgr.cloud:8080`

2. **Nginx 500 Errors**
   - Usually permission issues with `/root` directory
   - Run `./fix-nginx-permissions.sh` to copy files to `/var/www`

3. **Port Conflicts**
   - Port 80 used by Docker
   - Solution: Use port 8080 for nginx

4. **Frontend Not Updating**
   - Clear browser cache
   - Rebuild frontend: `./rebuild-frontend.sh`

5. **WebSocket Connection Failed**
   - Check nginx WebSocket configuration
   - Verify WebSocket URL in frontend `.env.production`
   - Check FastAPI logs for connection errors
   - Ensure nginx has WebSocket headers configured

6. **AI Chat Not Responding**
   - Verify n8n workflow is active
   - Check callback URL is accessible
   - Monitor correlation IDs in logs
   - Check n8n execution history

7. **Timeout Issues**
   - Increase nginx timeout settings
   - Check n8n workflow timeout configuration
   - Monitor request tracker for timeout status

## Maintenance

### Update Application
```bash
cd /root/n8n_workflow_runner
git pull
./rebuild-frontend.sh
systemctl restart fastapi
```

### Restart Services
```bash
systemctl restart fastapi
systemctl restart nginx
```

### Monitor Services
```bash
systemctl status fastapi
systemctl status nginx
```

### Backup
Important files to backup:
- `/root/n8n_workflow_runner` (entire project)
- `/etc/systemd/system/fastapi.service`
- `/etc/nginx/sites-available/fastapi-react-app`

## Scripts Reference

### setup-hostinger.sh
Complete automated setup for fresh deployment

### check-services.sh
Health check for all services

### fix-nginx-permissions.sh
Fixes nginx permission issues by copying files to `/var/www`

### rebuild-frontend.sh
Rebuilds and redeploys frontend with latest changes

### update-nginx-port.sh
Updates nginx to use port 8080 (avoiding Docker conflict)

## Security Considerations

1. **CORS**: Configured to allow only specific origins
2. **Authentication**: Currently none - add authentication for production
3. **HTTPS**: Consider adding SSL certificate for production
4. **Firewall**: Ensure only necessary ports are open

## Future Enhancements

1. Add authentication to API endpoints
2. Implement SSL/HTTPS with Let's Encrypt
3. Add database persistence (currently in-memory)
4. Implement proper logging
5. Add monitoring and alerting
6. Create Docker deployment option