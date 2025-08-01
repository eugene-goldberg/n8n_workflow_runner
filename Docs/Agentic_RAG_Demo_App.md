# Agentic RAG Demo Web Application

## Overview

A visual demonstration web application for the SpyroSolutions Agentic RAG system, showcasing hybrid search capabilities with full tool transparency.

## Access URLs

- **Web Interface**: http://srv928466.hstgr.cloud:8082
- **Backend API**: http://srv928466.hstgr.cloud:8001
- **API Health**: http://srv928466.hstgr.cloud:8001/health

## Features

### Visual Interface
- Real-time chat interface with the Agentic RAG system
- Visual representation of tool usage (Vector, Graph, Hybrid search)
- Live updates via WebSocket during query processing
- Example queries for different search types
- Search type explanations and documentation

### Tool Transparency
- Shows exactly which tools were used for each query
- Displays the search queries sent to each tool
- Indicates search type (Vector, Graph, or Hybrid)
- Shows response metadata including tool count

### Interactive Elements
1. **Chat Interface**: Send queries and receive AI-powered responses
2. **Example Queries**: Pre-populated queries demonstrating different search types
3. **Real-time Updates**: WebSocket connection shows tools being used in real-time
4. **Session Management**: Maintains conversation history with session IDs

## Architecture

### Frontend (React + TypeScript)
- Location: `/var/www/agentic-rag-demo`
- Built with React 19 and TypeScript
- WebSocket client for real-time updates
- Responsive design with gradient UI

### Backend (FastAPI)
- Location: `/root/agentic-rag-demo/backend`
- Running as systemd service: `agentic-rag-backend.service`
- Port: 8001
- Connects to n8n webhook: `https://n8n.srv928466.hstgr.cloud/webhook/spyro-rag-advanced`

### Nginx Configuration
- Frontend served on port 8082
- API proxy on `/api/` path
- WebSocket support on `/ws` path
- CORS headers configured

## Example Queries

### Vector Search (Semantic)
- "What features does SpyroAnalytics include?"
- "Describe the SpyroSuite platform"
- "What is SpyroGuard used for?"

### Graph Search (Relationships)
- "Which products does Disney use?"
- "What risks does EA have?"
- "Show me customers using SpyroAnalytics"

### Hybrid Search (Combined)
- "Show me all Enterprise tier customers and their risk scores"
- "What are the main risks and mitigation strategies?"
- "Which customers have performance issues and what products could help?"

## API Endpoints

### POST /chat
Send a query to the Agentic RAG system
```json
{
  "query": "Your question here",
  "session_id": "optional-session-id"
}
```

### GET /sessions/{session_id}
Retrieve conversation history for a session

### WebSocket /ws
Real-time updates during query processing

### POST /analyze-tools
Predict which tools would be used for a query (without executing)

## Maintenance

### Restart Services
```bash
# Backend
systemctl restart agentic-rag-backend

# Check status
systemctl status agentic-rag-backend

# View logs
journalctl -u agentic-rag-backend -f
```

### Update Frontend
```bash
cd /root/agentic-rag-demo/frontend
npm run build
cp -r build/* /var/www/agentic-rag-demo/
chown -R www-data:www-data /var/www/agentic-rag-demo
```

### Update Backend
```bash
cd /root/agentic-rag-demo/backend
# Make changes to main.py
systemctl restart agentic-rag-backend
```

## Troubleshooting

### Frontend Not Loading
1. Check Nginx: `systemctl status nginx`
2. Check logs: `tail -f /var/log/nginx/agentic-rag-demo-error.log`
3. Verify files: `ls -la /var/www/agentic-rag-demo/`

### Backend Connection Issues
1. Check service: `systemctl status agentic-rag-backend`
2. Test health: `curl http://localhost:8001/health`
3. Check webhook: Verify n8n webhook is active

### WebSocket Connection Failed
1. Check CORS settings in Nginx
2. Verify WebSocket upgrade headers
3. Check browser console for errors

## Development

### Local Development Setup
```bash
# Backend
cd backend
source venv/bin/activate
python main.py

# Frontend
cd frontend
npm start
```

### Environment Variables
Frontend (.env):
```
REACT_APP_API_URL=http://srv928466.hstgr.cloud:8001
REACT_APP_WS_URL=ws://srv928466.hstgr.cloud:8001/ws
```

## Security Notes

- CORS is currently set to allow all origins (*)
- No authentication implemented (demo purposes)
- For production: Add API keys, restrict CORS, enable HTTPS

## Future Enhancements

1. **Authentication**: Add user login and API key management
2. **Visualization**: Add graph visualization for entity relationships
3. **Export**: Allow exporting conversation history
4. **Analytics**: Track query patterns and tool usage
5. **Mobile**: Optimize for mobile devices
6. **Dark Mode**: Add theme toggle