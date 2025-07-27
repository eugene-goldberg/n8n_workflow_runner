# FastAPI + React + n8n AI Chat Application

A full-stack application featuring todo management and AI-powered chat with asynchronous n8n workflow integration using WebSockets.

## 🚀 Key Features

- **Todo Management**: Create, read, update, and delete todo items
- **AI Chat Interface**: Real-time chat with AI assistant powered by n8n workflows
- **WebSocket Communication**: Asynchronous messaging without timeout issues
- **n8n Integration**: Trigger complex workflows that can run for minutes
- **Correlation ID Tracking**: Handle multiple concurrent users and requests
- **Production Ready**: Deployed on Ubuntu VPS with nginx and systemd

## 🏗️ Architecture

```
┌─────────────┐     WebSocket      ┌──────────────┐     HTTP POST     ┌─────────────┐
│   React     │ ←─────────────────→ │   FastAPI    │ ─────────────────→ │     n8n     │
│   Chat UI   │                     │   Backend    │                     │  Workflow   │
└─────────────┘                     └──────────────┘                     └─────────────┘
                                           ↑                                     │
                                           │         HTTP POST (callback)        │
                                           └─────────────────────────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- n8n instance (cloud or self-hosted)
- nginx (for production)

## 🛠️ Local Development Setup

### Backend (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd fastapi-react-app/backend
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the migration script (for WebSocket support):
   ```bash
   ./migrate_to_websocket.sh
   ```

5. Start the FastAPI server:
   ```bash
   python3 main.py
   ```

The API will be available at:
- HTTP: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/{user_id}
- API docs: http://localhost:8000/docs

### Frontend (React)

1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd fastapi-react-app/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the migration script (for chat UI):
   ```bash
   ./migrate_to_chat.sh
   ```

4. Start the React development server:
   ```bash
   npm start
   ```

The app will open at http://localhost:3000

## 🌐 Production Deployment

### Quick Deploy

For Hostinger or similar Ubuntu VPS:

```bash
cd /root/n8n_workflow_runner
git pull
sudo ./deploy-async-chat.sh
```

### Manual Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📡 API Endpoints

### Todo Endpoints
- `GET /api/items` - Get all items
- `GET /api/items/{id}` - Get specific item
- `POST /api/items` - Create new item
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

### Chat & Workflow Endpoints
- `WS /ws/{user_id}` - WebSocket connection for chat
- `POST /api/workflow/execute` - Legacy workflow trigger
- `POST /api/n8n-callback` - Callback endpoint for n8n
- `GET /api/health` - Health check with connection stats

## 🔄 n8n Workflow Setup

1. Import the workflow:
   - Open n8n
   - Import `n8n-ai-chat-workflow-working.json`
   
2. Configure the workflow:
   - Add your AI service (OpenAI, Claude, etc.) if needed
   - Note the webhook URL from the Webhook Trigger node
   
3. Update the backend:
   - Edit `backend/main_with_websocket.py`
   - Set `N8N_WEBHOOK_URL` to your webhook URL
   - Set `CALLBACK_BASE_URL = "http://172.17.0.1:8000"` (Docker bridge)
   
4. Activate the workflow in n8n

**Important**: The workflow uses `items[0].json.body` to access webhook data and prepares the callback payload in the Process Message node.

## 💬 Chat Features

- **Real-time messaging**: Instant message delivery via WebSocket
- **Message types**: User, bot, system, acknowledgment, and error messages
- **Connection status**: Visual indicator of WebSocket connection
- **Auto-reconnect**: Automatic reconnection on connection loss
- **Message history**: Persistent chat history during session
- **Correlation tracking**: Each request tracked with unique ID

## 🔧 Configuration

### Environment Variables

#### Frontend (.env.production)
```
REACT_APP_API_URL=http://your-server:8080
REACT_APP_WS_URL=ws://your-server:8080/ws
```

#### Backend
Update in `main.py`:
- `N8N_WEBHOOK_URL`: Your n8n webhook URL
- `CALLBACK_BASE_URL`: Your server's public URL

### nginx Configuration
WebSocket support is configured in `nginx-websocket.conf`

## 📊 Monitoring

### Check Service Status
```bash
./check-services.sh
```

### View Logs
```bash
# FastAPI logs
journalctl -u fastapi -f

# nginx logs
journalctl -u nginx -f
```

## 🔒 Security Considerations

- Add authentication to WebSocket connections
- Implement rate limiting for chat messages
- Use HTTPS/WSS in production
- Validate and sanitize all user inputs
- Keep correlation IDs private

## 🚀 Next Steps

1. **Add Authentication**: Implement JWT tokens for secure chat
2. **Enable HTTPS**: Set up SSL certificates
3. **Add Persistence**: Store chat history in database
4. **Enhance AI**: Integrate more sophisticated AI models
5. **Add Features**: File uploads, voice messages, etc.

## 📚 Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed deployment instructions
- [ASYNC_CHAT_IMPLEMENTATION_PLAN.md](ASYNC_CHAT_IMPLEMENTATION_PLAN.md) - Technical implementation details
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Quick reference guide

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is open source and available under the MIT License.