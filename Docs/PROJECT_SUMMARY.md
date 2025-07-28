# FastAPI + React + n8n AI Chat Project Summary

## Quick Start Guide

### Access the Application
- **Live URL**: http://srv928466.hstgr.cloud:8080
- **API Docs**: http://srv928466.hstgr.cloud:8080/api/docs
- **WebSocket**: ws://srv928466.hstgr.cloud:8080/ws/{user_id}

### What Was Built

1. **Full-Stack Todo Application**
   - FastAPI backend with REST API
   - React TypeScript frontend
   - Real-time CRUD operations

2. **AI Chat System** ✨ NEW
   - WebSocket-based real-time chat
   - Asynchronous n8n workflow integration
   - Correlation ID tracking for requests
   - Multiple message types (user, bot, system)
   - Auto-reconnection on disconnect

3. **n8n Workflow Integration**
   - HTTP webhook triggers
   - Callback mechanism for async responses
   - Support for long-running AI workflows
   - No timeout issues

4. **Production Deployment**
   - Ubuntu 24.04 VPS on Hostinger
   - Nginx with WebSocket support
   - Systemd service management
   - Automated deployment scripts

## Project Structure
```
n8n_workflow_runner/
├── fastapi-react-app/
│   ├── backend/
│   │   ├── main.py           # FastAPI application
│   │   └── requirements.txt  # Python dependencies
│   └── frontend/
│       ├── src/              # React source code
│       ├── build/            # Production build
│       └── package.json      # Node dependencies
├── setup-hostinger.sh        # Automated setup script
├── check-services.sh         # Service health check
├── rebuild-frontend.sh       # Frontend rebuild script
├── fix-nginx-permissions.sh  # Permission fix script
├── n8n-webhook-workflow.json # n8n workflow template
└── DEPLOYMENT_GUIDE.md       # Detailed documentation
```

## Key Commands

### On Hostinger Server

**Deploy Async Chat Update**
```bash
git pull
sudo ./deploy-async-chat.sh
```

**Check Status**
```bash
./check-services.sh
```

**Update Application**
```bash
git pull
./rebuild-frontend.sh
systemctl restart fastapi
```

**View Logs**
```bash
journalctl -u fastapi -f    # Backend logs
journalctl -u nginx -f      # Nginx logs
# Watch WebSocket connections
journalctl -u fastapi -f | grep -i websocket
```

**Restart Services**
```bash
systemctl restart fastapi
systemctl restart nginx
```

### Local Development

**Backend**
```bash
cd fastapi-react-app/backend
source venv/bin/activate
python3 main.py
```

**Frontend**
```bash
cd fastapi-react-app/frontend
npm start
```

## Configuration Files

### Backend API Endpoints
- `POST /api/workflow/execute` - Triggers n8n workflow
- `GET/POST/PUT/DELETE /api/items` - Todo CRUD operations

### Environment Variables
- Frontend: `REACT_APP_API_URL` in `.env.production`
- Update webhook URL in `backend/main.py`

### Service Locations
- Nginx config: `/etc/nginx/sites-available/fastapi-react-app`
- Systemd service: `/etc/systemd/system/fastapi.service`
- Frontend files: `/var/www/fastapi-react-app`

## Workflow Integration

### Available n8n Workflows

1. **Basic Chat Workflow** (`n8n-ai-chat-workflow-working.json`)
   - Testing workflow with simulated responses
   - No AI service required

2. **AI Integration Workflow** (`n8n-ai-chat-workflow-with-agent.json`)
   - Real AI responses via OpenAI
   - Requires API credentials

3. **Intent Evaluation** (`n8n-intent-evaluation-fixed.json`)
   - LangChain-based intent analysis
   - Returns structured JSON

4. **Intent-Based Routing** (`n8n-intent-routing-workflow.json`) ✨ NEW
   - AI classifies user intent
   - Routes to 6 specialized handlers
   - Priority escalation for urgent issues

### Webhook Setup
1. **Import workflow** into n8n
2. **Configure AI service** (if needed)
3. **Get webhook URL** from trigger node
4. **Update backend**:
   ```python
   N8N_WEBHOOK_URL = "your-webhook-url"
   CALLBACK_BASE_URL = "http://172.17.0.1:8000"  # Docker bridge
   ```

2. **Chat Webhook Payload**
```json
{
    "correlation_id": "unique-id",
    "user_id": "user-identifier",
    "message": "user's message",
    "timestamp": "ISO date string",
    "callback_url": "http://your-server/api/n8n-callback"
}
```

3. **Callback Response**
```json
{
    "correlation_id": "unique-id",
    "user_id": "user-identifier",
    "result": "AI response text"
}
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| CORS errors | Check allowed origins in `main.py` |
| Nginx 500 error | Run `./fix-nginx-permissions.sh` |
| Frontend not updating | Clear cache, run `./rebuild-frontend.sh` |
| Service not running | Check with `systemctl status [service]` |
| Port conflict | Using port 8080 (Docker uses 80) |

## Next Steps

1. **Add Authentication**
   - Implement JWT tokens
   - Secure API endpoints

2. **Enable HTTPS**
   - Install SSL certificate
   - Update nginx config

3. **Add Database**
   - Replace in-memory storage
   - Use PostgreSQL or SQLite

4. **Enhance n8n Integration**
   - Pass todo items to workflow
   - Handle workflow responses
   - Add more trigger options

## Repository
https://github.com/eugene-goldberg/n8n_workflow_runner