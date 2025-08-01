# SpyroSolutions Agentic RAG Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Testing Methodology](#testing-methodology)
5. [Troubleshooting](#troubleshooting)
6. [Performance Considerations](#performance-considerations)

## Overview

The SpyroSolutions Agentic RAG system is a sophisticated knowledge retrieval platform that combines:
- **Vector Search** (PostgreSQL with pgvector) for semantic similarity
- **Graph RAG** (Neo4j with Graphiti) for entity relationships
- **Tool Transparency** showing exactly how answers are derived
- **n8n Integration** for workflow automation and API orchestration

### Key Features
- Hybrid search combining vector and keyword approaches
- Automatic tool selection based on query type
- Session management with conversation history
- Server-sent events (SSE) for streaming responses
- Comprehensive error handling and monitoring

## Architecture

### System Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   n8n Webhook   │────▶│  Agentic RAG    │────▶│  PostgreSQL     │
│  (Port: 443)    │     │  (Port: 8058)   │     │  (pgvector)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                          │
                               │                          │
                               ▼                          ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │     Neo4j       │     │    OpenAI       │
                        │   (Graphiti)    │     │  (GPT-4-mini)   │
                        └─────────────────┘     └─────────────────┘
```

### Network Configuration
- All services run in Docker containers on `root_default` network
- Internal service discovery using container names
- External access through Nginx reverse proxy

## Implementation Details

### Phase 1: Environment Setup

#### Python Environment
```bash
# Server has Python 3.12.3 installed
cd /root/spyro-agentic-rag/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Directory Structure
```
/root/spyro-agentic-rag/
├── app/                    # Application source code
│   ├── ingestion/         # Document ingestion pipeline
│   ├── api/               # FastAPI application
│   ├── tools/             # RAG tools (vector, graph search)
│   └── .env               # Environment configuration
├── data/
│   └── documents/         # SpyroSolutions documents
├── logs/                  # Application logs
└── docker-compose.yml     # Service orchestration
```

### Phase 2: Database Configuration

#### PostgreSQL with pgvector
```sql
-- Extension already enabled in n8n_postgres_memory
CREATE DATABASE spyro_rag_db;

-- Schema includes:
-- - documents table for source materials
-- - chunks table with embeddings
-- - sessions and messages for conversation history
-- - Vector similarity search functions
```

#### Neo4j with Graphiti
```yaml
# Neo4j container configuration
NEO4J_HOST: spyro_neo4j
NEO4J_PORT: 7687
NEO4J_USER: neo4j
NEO4J_PASSWORD: SpyroSolutions2025!
```

### Phase 3: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
# Install system dependencies for compilation
RUN apt-get update && apt-get install -y gcc g++ postgresql-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8058
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8058"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  spyro_rag_api:
    build: .
    container_name: spyro_rag_api
    ports:
      - "8058:8058"
    env_file: ./app/.env
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    networks:
      - root_default
    external_links:
      - n8n_postgres_memory:postgres
      - spyro_neo4j:neo4j

networks:
  root_default:
    external: true
```

### Phase 4: Data Ingestion

#### Document Preparation
Three core documents were created:
1. **spyro_customers.md** - Customer portfolio with risk scores
2. **spyro_risk_analysis.md** - Detailed risk assessments
3. **spyro_products.md** - Product suite information

#### Ingestion Process
```bash
docker exec spyro_rag_api python -m ingestion.ingest --clean
```

Results:
- 3 documents processed
- 6 chunks created with embeddings
- Knowledge graph relationships established
- ~2 minutes processing time

### Phase 5: n8n Integration

#### Workflow Creation
Three workflows were created via n8n REST API:

1. **Basic Agentic RAG** (ID: uojGfamAO32LBoVe)
   - Simple webhook → API call → response flow
   
2. **Streaming Info** (ID: RI1Whiz0F0KljPDo)
   - Returns SSE endpoint details for real-time streaming
   
3. **Advanced with Error Handling** (ID: HiQFo3nwcS7a94M4)
   - Input validation with UUID generation
   - Comprehensive error handling
   - Response time tracking
   - Tool usage transparency

#### Key Implementation: UUID Generation
```javascript
// Generate proper UUID format for session_id
const sessionId = $json.body.session_id || $json.body.sessionId || 
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
```

## Testing Methodology

### 1. Direct API Testing

#### Health Check
```bash
curl -s http://148.230.84.166:8058/health
```
Expected response:
```json
{
  "status": "healthy",
  "database": true,
  "graph_database": true,
  "llm_connection": true,
  "version": "0.1.0"
}
```

#### Basic Query Test
```bash
curl -X POST http://148.230.84.166:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Which customers have the highest risk scores?"}'
```

### 2. Tool Selection Testing

#### Vector Search Test
Query: "What features does SpyroAnalytics include?"
- Triggers: `vector_search` tool
- Uses: Semantic similarity in knowledge base
- Search type: `SearchType.HYBRID`

#### Graph Search Test
Query: "What is the total revenue at risk for Disney?"
- Triggers: `graph_search` tool
- Uses: Neo4j relationship traversal
- Finds: Connected risk entities and mitigation strategies

### 3. n8n Webhook Testing

#### Test Mode Activation
1. Open workflow in n8n UI
2. Click "Listen for test event" on webhook node
3. Submit test request
4. Execute nodes manually to trace data flow

#### Production Testing
```bash
curl -X POST 'https://n8n.srv928466.hstgr.cloud/webhook/spyro-rag-advanced' \
  -H 'Content-Type: application/json' \
  -d '{"query": "Your test query here"}'
```

### 4. Error Handling Testing

#### Missing Field Test
```bash
curl -X POST 'https://n8n.srv928466.hstgr.cloud/webhook/spyro-rag-advanced' \
  -H 'Content-Type: application/json' \
  -d '{}'
```
Expected: 400 error with helpful message

#### Invalid Session ID Test
Before fix: "test-webhook-001" caused UUID validation error
After fix: Automatic UUID generation prevents errors

### 5. Performance Testing

#### Response Time Monitoring
- Direct API: ~2-3 seconds for complex queries
- n8n webhook: Additional ~1-2 seconds overhead
- Streaming endpoint: First token in <1 second

#### Load Testing Considerations
- PostgreSQL connection pooling configured
- Neo4j handles concurrent queries well
- Rate limiting at 60 requests/minute

## Troubleshooting

### Common Issues and Solutions

#### 1. Webhook Not Registered
**Error**: "The requested webhook is not registered"
**Solution**: 
- Ensure workflow is activated in n8n UI
- In test mode, click "Listen for test event"
- Use production URL for persistent webhooks

#### 2. UUID Validation Error
**Error**: "invalid UUID: length must be between 32..36 characters"
**Solution**: Updated Validate Input node to generate proper UUIDs

#### 3. Container Networking
**Error**: Connection refused to API
**Solution**: 
- Use container names (spyro_rag_api) not localhost
- Ensure all services on same Docker network

#### 4. OpenAI API Errors
**Error**: Invalid API key
**Solution**: Update .env file and restart container:
```bash
docker-compose down
docker-compose up -d
```

### Debugging Tools

#### Container Logs
```bash
docker logs spyro_rag_api -f
docker logs n8n_postgres_memory
docker logs spyro_neo4j
```

#### Database Queries
```bash
# Check vector embeddings
docker exec n8n_postgres_memory psql -U n8n_memory -d spyro_rag_db \
  -c "SELECT COUNT(*) FROM chunks;"

# Verify Neo4j relationships
docker exec spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' \
  'MATCH (n) RETURN COUNT(n)'
```

## Performance Considerations

### Optimization Strategies

1. **Vector Search Optimization**
   - HNSW index for fast similarity search
   - Chunk size balanced at 1000 characters
   - Overlap of 200 characters for context

2. **Graph Query Optimization**
   - Indexed entity properties
   - Limited traversal depth
   - Cached frequent queries

3. **API Response Optimization**
   - Connection pooling
   - Async request handling
   - Response streaming for large results

### Monitoring Recommendations

1. **System Metrics**
   - CPU/Memory usage per container
   - Database query times
   - API response times

2. **Business Metrics**
   - Query types distribution
   - Tool usage patterns
   - Session lengths

3. **Error Tracking**
   - Failed queries
   - Timeout incidents
   - Rate limit hits

## Security Considerations

1. **API Security**
   - Currently no authentication (add API keys for production)
   - Rate limiting configured
   - Input validation on all endpoints

2. **Database Security**
   - Credentials in environment variables
   - Network isolation via Docker
   - Regular backup recommended

3. **Data Privacy**
   - Session data retention policies
   - PII handling in documents
   - Audit logging capabilities

## Next Steps

### Phase 7: Production Configuration
1. Configure Nginx reverse proxy with SSL
2. Set up monitoring with Prometheus/Grafana
3. Implement backup strategies
4. Add authentication layer
5. Configure log rotation

### Future Enhancements
1. Multi-language support
2. Custom embedding models
3. Advanced caching strategies
4. Horizontal scaling setup
5. WebSocket support for real-time updates