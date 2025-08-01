# SpyroSolutions RAG Web Interface

A web interface for interacting with the SpyroSolutions neo4j-graphrag-python implementation.

## Features

- **Hybrid Search**: Combines vector and fulltext search for finding relevant content
- **Text2Cypher**: Converts natural language queries to Cypher for direct graph queries
- **Real-time Updates**: WebSocket connection shows which tools are being used
- **Session History**: Maintains conversation context
- **Visual Feedback**: See exactly how your queries are processed

## Setup

### Prerequisites

1. Make sure the SpyroSolutions API is running on port 8000:
   ```bash
   cd /Users/eugene/dev/apps/n8n_workflow_runner/neo4j-graphrag-python
   python3 enhanced_spyro_api.py
   ```

2. Ensure Neo4j is running with the SpyroSolutions data loaded

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd web-ui/backend
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

4. Run the backend server:
   ```bash
   python main.py
   ```

   The backend will start on http://localhost:8001

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd web-ui/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

   The frontend will start on http://localhost:3000

## Usage

### Hybrid Search (Default)
Best for finding information based on concepts and descriptions:
- "What products does SpyroSolutions offer?"
- "Tell me about the security features"
- "Explain the cloud platform capabilities"

### Text2Cypher (Graph Queries)
Enable by checking "Use Graph Query" - best for specific data queries:
- "Which customers have which subscription plans and ARR?"
- "Show me all teams and their product responsibilities"
- "List customers at risk with their revenue"

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   React UI  │────▶│ FastAPI     │────▶│ SpyroSolutions   │
│  (Port 3000)│     │ (Port 8001) │     │ API (Port 8000)  │
└─────────────┘     └─────────────┘     └──────────────────┘
                            │                      │
                            ▼                      ▼
                      WebSocket              Neo4j Database
                    (Real-time)              (Port 7687)
```

## API Endpoints

### Backend (Port 8001)
- `POST /chat` - Send a query to the RAG system
- `GET /health` - Check system health
- `GET /stats` - Get usage statistics
- `GET /graph/stats` - Get graph database statistics
- `WS /ws` - WebSocket for real-time updates

### SpyroSolutions API (Port 8000)
- `POST /query` - Execute RAG query
- `GET /health` - Check API health
- `GET /stats` - System statistics
- `GET /graph/stats` - Graph statistics

## Example Queries

### Products & Features
- "What are the key products and their SLA guarantees?"
- "Describe SpyroCloud Platform features"
- "What security capabilities does SpyroSecure offer?"

### Customer Analysis
- "Which customers are at risk and their subscription values?"
- "Show me all Enterprise Plus customers"
- "What is TechCorp's subscription and risk profile?"

### Operational Insights
- "How are engineering teams organized?"
- "What are the operational costs by project?"
- "Which teams manage which products?"

## Troubleshooting

1. **Connection refused on port 8000**: Make sure the SpyroSolutions API is running
2. **No graph data returned**: Ensure Neo4j is running and data is loaded
3. **WebSocket errors**: Check that both frontend and backend are running
4. **CORS errors**: The backend is configured to allow all origins for development