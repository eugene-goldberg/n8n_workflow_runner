# Agentic RAG Demo Application

A visual demonstration web application for the SpyroSolutions Agentic RAG system, showcasing hybrid search capabilities with full tool transparency.

## Overview

This application provides a user-friendly interface to interact with the Agentic RAG system, visualizing how different search tools (Vector, Graph, and Hybrid) are used to answer queries.

## Project Structure

```
agentic-rag-demo/
├── backend/
│   └── main.py          # FastAPI backend that connects to n8n webhook
├── frontend/
│   ├── public/          # Static assets
│   ├── src/
│   │   ├── App.tsx      # Main React component with chat interface
│   │   ├── App.css      # Styling with gradient UI
│   │   └── index.tsx    # React entry point
│   ├── package.json     # Frontend dependencies
│   ├── tsconfig.json    # TypeScript configuration
│   └── .env            # Environment variables
└── README.md           # This file
```

## Features

- **Real-time Chat Interface**: Interactive chat with the Agentic RAG system
- **Tool Visualization**: Shows which search tools are being used (Vector 🔍, Graph 🕸️, Hybrid 🔄)
- **WebSocket Support**: Live updates during query processing
- **Example Queries**: Pre-populated queries demonstrating different search types
- **Session Management**: Maintains conversation history

## Backend

The FastAPI backend (`backend/main.py`) provides:

- `/chat` - Send queries to the Agentic RAG system via n8n webhook
- `/health` - Check API and webhook connectivity
- `/sessions/{session_id}` - Retrieve conversation history
- `/ws` - WebSocket endpoint for real-time updates
- `/analyze-tools` - Predict which tools would be used for a query

## Frontend

The React TypeScript frontend provides:

- Beautiful gradient UI with animations
- Real-time tool usage visualization
- Example query buttons
- Search type explanations
- Responsive design

## Deployment

The application is deployed on the server at:
- Frontend: http://srv928466.hstgr.cloud:8082
- Backend API: http://srv928466.hstgr.cloud:8001

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn httpx websockets
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Environment Variables

### Frontend (.env)
```
REACT_APP_API_URL=http://srv928466.hstgr.cloud:8001
REACT_APP_WS_URL=ws://srv928466.hstgr.cloud:8001/ws
```

## Example Queries

### Vector Search (Semantic)
- "What features does SpyroAnalytics include?"
- "Describe the SpyroSuite platform"

### Graph Search (Relationships)
- "Which products does Disney use?"
- "What risks does EA have?"

### Hybrid Search (Combined)
- "Show me all Enterprise tier customers and their risk scores"
- "What are the main risks and mitigation strategies?"

## Technologies Used

- **Backend**: FastAPI, Python 3.12, WebSockets
- **Frontend**: React 19, TypeScript, WebSocket API
- **Deployment**: Nginx, systemd
- **Integration**: n8n webhooks, Agentic RAG API