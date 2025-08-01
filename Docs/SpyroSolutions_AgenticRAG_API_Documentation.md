# SpyroSolutions Agentic RAG API Documentation

## Overview
The SpyroSolutions Agentic RAG system provides intelligent query processing with full tool transparency, combining vector search, graph traversal, and LLM reasoning.

## Base URLs
- **Direct API**: `http://148.230.84.166:8058`
- **n8n Webhooks**: `https://n8n.srv928466.hstgr.cloud/webhook/[endpoint]`

## Authentication
Currently, the API does not require authentication. In production, implement API key authentication.

## Endpoints

### 1. Health Check
**Endpoint**: `GET /health`  
**Description**: Check system health and connectivity

**Response Example**:
```json
{
  "status": "healthy",
  "database": true,
  "graph_database": true,
  "llm_connection": true,
  "version": "0.1.0",
  "timestamp": "2025-07-31T19:16:50.390875"
}
```

### 2. Chat Endpoint
**Endpoint**: `POST /chat`  
**Description**: Process queries with intelligent routing

**Request Body**:
```json
{
  "message": "Your query here",
  "session_id": "optional-session-id"
}
```

**Response Example**:
```json
{
  "message": "Detailed answer with analysis...",
  "session_id": "6bea9fea-2326-458a-aa02-f3c9f20d7167",
  "sources": [],
  "tools_used": [
    {
      "tool_name": "vector_search",
      "args": {
        "query": "customers with high risk scores",
        "limit": 10
      },
      "tool_call_id": "call_WyEHnmkDH37CyrWzx07spYOM"
    }
  ],
  "metadata": {
    "search_type": "SearchType.HYBRID"
  }
}
```

### 3. Streaming Chat (SSE)
**Endpoint**: `POST /chat/stream`  
**Description**: Stream responses in real-time

**Request Body**: Same as chat endpoint

**Response**: Server-Sent Events stream
```
data: {"content": "Based on", "type": "text"}
data: {"content": " the analysis", "type": "text"}
data: {"done": true, "type": "end"}
```

## n8n Integration Workflows

### 1. Basic Agentic RAG
**Webhook**: `POST /webhook/spyro-agentic-rag`  
**Workflow ID**: `uojGfamAO32LBoVe`

### 2. Streaming Info
**Webhook**: `POST /webhook/spyro-agentic-rag-stream`  
**Workflow ID**: `RI1Whiz0F0KljPDo`

### 3. Advanced with Error Handling
**Webhook**: `POST /webhook/spyro-rag-advanced`  
**Workflow ID**: `HiQFo3nwcS7a94M4`

**Request Format**:
```json
{
  "query": "Your question",
  "session_id": "optional",
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response Format**:
```json
{
  "success": true,
  "answer": "Comprehensive answer...",
  "session_id": "session-id",
  "timestamp": "2025-07-31T19:30:00.000Z",
  "metadata": {
    "search_type": "hybrid",
    "response_time_ms": 1234,
    "tools_used_count": 2
  },
  "tools_used": [
    {
      "name": "vector_search",
      "purpose": "Semantic search in knowledge base",
      "query": "Disney risks",
      "call_id": "call_123"
    }
  ],
  "sources": []
}
```

## Example Queries

### 1. Risk Analysis
```bash
curl -X POST http://148.230.84.166:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are the main risks for Disney?"}'
```

### 2. Customer Information
```bash
curl -X POST http://148.230.84.166:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Show me all Enterprise tier customers and their MRR"}'
```

### 3. Product Details
```bash
curl -X POST http://148.230.84.166:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What features does SpyroAnalytics include?"}'
```

## Tool Types

The system uses multiple tools for intelligent query processing:

1. **vector_search**: Semantic similarity search using embeddings
2. **graph_search**: Neo4j graph traversal for relationships
3. **entity_search**: Find specific entities in the knowledge graph
4. **hybrid_search**: Combined vector and keyword search

## Error Handling

### Error Response Format:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "timestamp": "2025-07-31T19:30:00.000Z"
  },
  "session_id": "session-id",
  "suggestion": "Helpful suggestion for resolution"
}
```

### Common Error Codes:
- `MISSING_FIELD`: Required field missing in request
- `TIMEOUT`: Request took too long
- `RATE_LIMIT`: Too many requests
- `UNKNOWN_ERROR`: Unexpected error

## Best Practices

1. **Session Management**: Use consistent session_ids for conversation context
2. **Query Optimization**: Be specific in queries for better results
3. **Error Handling**: Always check the `success` field in responses
4. **Tool Transparency**: Review `tools_used` to understand how answers were derived

## Rate Limits
- **Requests per minute**: 60 (configurable)
- **Max tokens per request**: 1000 (configurable)
- **Timeout**: 30 seconds

## System Architecture
```
Client → n8n Webhook → Agentic RAG API → {
  → PostgreSQL (Vector Search)
  → Neo4j (Graph Traversal)
  → OpenAI (LLM Processing)
} → Response
```

## Monitoring
- Health checks should be performed every 5 minutes
- Monitor response times in metadata
- Track tool usage patterns for optimization