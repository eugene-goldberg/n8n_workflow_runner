# SpyroSolutions Neo4j GraphRAG Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Details](#component-details)
4. [Implementation Steps](#implementation-steps)
5. [API Endpoints](#api-endpoints)
6. [Web Interface](#web-interface)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Performance Optimization](#performance-optimization)
9. [Production Considerations](#production-considerations)
10. [Maintenance & Monitoring](#maintenance--monitoring)

## Overview

The SpyroSolutions RAG system combines Neo4j's graph database capabilities with vector search to provide intelligent question answering about business data. The system supports two primary search modes:

1. **Hybrid Search**: Combines vector embeddings and fulltext search for semantic queries
2. **Text2Cypher**: Converts natural language to graph queries for specific data retrieval

### Key Features
- Dual search modes (Hybrid and Graph Query)
- Real-time web interface with tool visualization
- RESTful API with authentication
- Automatic knowledge graph construction
- Session management and query history

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   React Web UI  │────▶│  FastAPI Proxy  │────▶│ SpyroSolutions   │
│  (Port 3000)    │     │  (Port 8001)    │     │ API (Port 8000)  │
└─────────────────┘     └─────────────────┘     └──────────────────┘
                               │                          │
                               ▼                          ▼
                         WebSocket                   Neo4j Database
                       (Real-time)                   (Port 7687)
                                                          │
                                                          ▼
                                              ┌─────────────────────┐
                                              │ • Vector Index      │
                                              │ • Fulltext Index    │
                                              │ • Graph Structure   │
                                              └─────────────────────┘
```

### Core Components

1. **Neo4j Database**: Stores graph structure, text chunks, and vector embeddings
2. **SpyroSolutions API**: Main RAG service with retriever implementations
3. **Web UI Backend**: Proxy server with WebSocket support
4. **React Frontend**: Interactive interface for queries

## Component Details

### 1. Neo4j Database Schema

#### Entities
```cypher
// Core Business Entities
(:Customer {name: STRING})
(:Product {name: STRING, description: STRING})
(:Project {name: STRING, status: STRING})
(:Team {name: STRING, size: INTEGER})
(:SaaSSubscription {plan: STRING, ARR: STRING})
(:CustomerSuccessScore {score: FLOAT, health_status: STRING})
(:Risk {level: STRING, type: STRING, description: STRING})
(:Event {type: STRING, date: STRING, impact: STRING})
(:SLA {metric: STRING, guarantee: STRING})
(:OperationalStatistics {metric: STRING, value: STRING})
(:OperationalCost {cost: STRING})
(:Profitability {impact: STRING})

// Text Chunks for RAG
(:__Chunk__ {text: STRING, embedding: LIST<FLOAT>})
```

#### Relationships
```cypher
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:Customer)-[:HAS_RISK]->(:Risk)
(:Customer)-[:AFFECTED_BY_EVENT]->(:Event)
(:Product)-[:USED_BY]->(:Customer)
(:Product)-[:ASSIGNED_TO_TEAM]->(:Team)
(:Product)-[:HAS_SLA]->(:SLA)
(:Product)-[:HAS_OPERATIONAL_STATS]->(:OperationalStatistics)
(:Project)-[:HAS_OPERATIONAL_COST]->(:OperationalCost)
(:Project)-[:CONTRIBUTES_TO_PROFITABILITY]->(:Profitability)
(entity)-[:FROM_CHUNK]->(:__Chunk__)
```

#### Indexes
```cypher
// Vector search
CREATE VECTOR INDEX spyro_vector_index IF NOT EXISTS
FOR (c:__Chunk__)
ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}}

// Fulltext search
CREATE FULLTEXT INDEX spyro_fulltext_index IF NOT EXISTS
FOR (c:__Chunk__)
ON EACH [c.text]

// Entity indexes for performance
CREATE INDEX FOR (c:Customer) ON (c.name)
CREATE INDEX FOR (p:Product) ON (p.name)
CREATE INDEX FOR (pr:Project) ON (pr.name)
CREATE INDEX FOR (t:Team) ON (t.name)
```

### 2. Retriever Implementations

#### HybridRetriever
- Combines vector similarity and keyword matching
- Best for: Conceptual queries, product descriptions, feature explanations
- Example: "What security features does SpyroSolutions offer?"

#### Text2CypherRetriever
- Converts natural language to Cypher queries using LLM
- Best for: Specific data queries, aggregations, relationship traversal
- Example: "Which customers have subscriptions worth more than $5M?"

Configuration:
```python
# Hybrid Retriever
hybrid_retriever = HybridRetriever(
    driver=driver,
    vector_index_name="spyro_vector_index",
    fulltext_index_name="spyro_fulltext_index",
    embedder=OpenAIEmbeddings()
)

# Text2Cypher Retriever
text2cypher_retriever = Text2CypherRetriever(
    driver=driver,
    llm=OpenAILLM(model_name="gpt-4o"),
    neo4j_schema=SPYRO_SCHEMA,
    examples=CYPHER_EXAMPLES
)
```

### 3. Knowledge Graph Construction

#### Using SimpleKGPipeline (Quick Start)
```python
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

# Initialize pipeline
kg_builder = SimpleKGPipeline(
    llm=llm,
    embedder=embedder,
    driver=driver,
    text_splitter=FixedSizeSplitter(chunk_size=500),
    entities=ENTITY_TYPES,
    relations=RELATION_TYPES
)

# Build from text
kg_builder.run(text="Your business data text...")
```

#### Enhanced KG Builder (Production)
- Entity resolution to prevent duplicates
- Consistent property extraction
- Schema validation
- Post-processing cleanup

See `enhanced_kg_builder.py` for implementation.

## Implementation Steps

### Step 1: Environment Setup

1. **Install Dependencies**
```bash
# Core dependencies
pip install neo4j-graphrag-python
pip install fastapi uvicorn httpx
pip install openai python-dotenv

# Frontend dependencies
cd web-ui/frontend
npm install
```

2. **Configure Environment Variables**
```bash
# .env file
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
OPENAI_API_KEY=your-api-key
SPYRO_API_KEY=spyro-secret-key-123
```

### Step 2: Database Setup

1. **Start Neo4j**
```bash
# Using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:latest
```

2. **Clean Existing Data**
```python
# clean_neo4j.py
session.run("MATCH (n) DETACH DELETE n")
```

3. **Create Indexes**
```python
# Run after data import
python3 create_indexes.py
```

### Step 3: Data Import

1. **From Structured Data**
```python
# Direct import for clean data
session.run("""
    CREATE (c:Customer {name: $name})
    CREATE (s:SaaSSubscription {plan: $plan, ARR: $arr})
    CREATE (c)-[:SUBSCRIBES_TO]->(s)
""", name="TechCorp", plan="Enterprise", arr="$5M")
```

2. **From Unstructured Text**
```python
# Using SimpleKGPipeline
python3 spyro_semantic_model_implementation.py
```

### Step 4: Start Services

1. **Main API Service**
```bash
cd /path/to/neo4j-graphrag-python
python3 enhanced_spyro_api_v2.py
# Runs on http://localhost:8000
```

2. **Web UI Backend**
```bash
cd web-ui/backend
python3 main.py
# Runs on http://localhost:8001
```

3. **Web UI Frontend**
```bash
cd web-ui/frontend
npm start
# Runs on http://localhost:3000
```

## API Endpoints

### Main API (Port 8000)

#### Health Check
```bash
GET /health
Headers: X-API-Key: spyro-secret-key-123

Response:
{
    "status": "healthy",
    "neo4j_connected": true,
    "node_count": 120,
    "indexes_available": ["spyro_vector_index", "spyro_fulltext_index"]
}
```

#### Execute Query
```bash
POST /query
Headers: 
  X-API-Key: spyro-secret-key-123
  Content-Type: application/json

Body:
{
    "question": "Which customers have which subscription plans?",
    "use_cypher": true,
    "top_k": 5
}

Response:
{
    "question": "Which customers have which subscription plans?",
    "answer": "Based on the graph data:\n - customer: TechCorp...",
    "context_items": 3,
    "retriever_type": "text2cypher",
    "processing_time_ms": 1205.32,
    "graph_results": [
        {
            "customer": "TechCorp Industries",
            "plan": "Enterprise Plus",
            "arr": "$5M"
        }
    ]
}
```

#### Statistics
```bash
GET /stats
GET /graph/stats
```

### Web UI Backend (Port 8001)

- `/chat` - Main query endpoint with WebSocket notifications
- `/health` - Combined health check
- `/sessions/{id}` - Session history
- `/ws` - WebSocket for real-time updates

## Web Interface

### Features
1. **Query Input**
   - Toggle between Hybrid and Graph Query modes
   - Auto-complete suggestions
   - Query history

2. **Real-time Visualization**
   - Active tool indicators
   - Processing time display
   - Context item count

3. **Example Queries**
   - Pre-configured queries for each mode
   - Click to populate input

### Usage Examples

#### Hybrid Search Queries
- "What products does SpyroSolutions offer?"
- "Explain the security capabilities"
- "Tell me about cloud infrastructure features"

#### Graph Query (Text2Cypher)
- "Which customers have subscriptions over $5M?"
- "Show all teams and their product assignments"
- "List customers at risk with their revenue"

## Common Issues & Solutions

### Issue 1: Duplicate Results in Text2Cypher
**Problem**: Queries return duplicate rows
**Solution**: Add DISTINCT to Cypher examples
```python
EXAMPLES = [
    "... RETURN DISTINCT c.name as customer, s.ARR as revenue"
]
```

### Issue 2: Missing Property Values
**Problem**: Properties return as None
**Solution**: Check actual property names in Neo4j
```cypher
MATCH (n:OperationalCost)
RETURN keys(n) as properties
LIMIT 1
```

### Issue 3: No Context Retrieved
**Problem**: Hybrid search returns 0 context items
**Solution**: Ensure chunks have __Chunk__ label
```python
# Fix chunk labels
session.run("""
    MATCH (n:Chunk)
    SET n:__Chunk__
""")
```

### Issue 4: Slow Query Performance
**Problem**: Queries take too long
**Solution**: Create appropriate indexes
```cypher
CREATE INDEX FOR (c:Customer) ON (c.name)
```

## Performance Optimization

### 1. Query Optimization
- Use indexes for frequently queried properties
- Limit result sets with `LIMIT` clauses
- Use `DISTINCT` to avoid duplicates
- Profile queries with `EXPLAIN` and `PROFILE`

### 2. Caching Strategy
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_embedding(text: str):
    return embedder.embed_query(text)
```

### 3. Batch Processing
```python
# Batch embed documents
embeddings = embedder.embed_documents(texts)

# Batch write to Neo4j
session.run("""
    UNWIND $records as record
    CREATE (c:__Chunk__ {text: record.text, embedding: record.embedding})
""", records=batch_data)
```

### 4. Connection Pooling
```python
driver = GraphDatabase.driver(
    uri, 
    auth=auth,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30
)
```

## Production Considerations

### 1. Security
- **API Authentication**: Implement proper API key management
- **Input Validation**: Sanitize user queries before Cypher generation
- **Rate Limiting**: Prevent abuse with request limits
- **HTTPS**: Use SSL/TLS for all connections

### 2. Scalability
- **Neo4j Clustering**: Use Neo4j Aura or Enterprise for HA
- **Load Balancing**: Distribute API requests
- **Async Processing**: Use background tasks for heavy operations
- **CDN**: Cache static assets

### 3. Monitoring
```python
# Add logging
import logging
logging.basicConfig(level=logging.INFO)

# Add metrics
from prometheus_client import Counter, Histogram

query_counter = Counter('rag_queries_total', 'Total RAG queries')
query_duration = Histogram('rag_query_duration_seconds', 'Query duration')

@query_duration.time()
def execute_query(question: str):
    query_counter.inc()
    # ... query logic
```

### 4. Error Handling
```python
class QueryError(Exception):
    pass

@app.exception_handler(QueryError)
async def query_error_handler(request: Request, exc: QueryError):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "type": "query_error"}
    )
```

## Maintenance & Monitoring

### Daily Tasks
1. **Monitor Query Performance**
```cypher
// Check slow queries
CALL dbms.listQueries() 
YIELD query, elapsedTimeMillis
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis
```

2. **Check Index Health**
```cypher
SHOW INDEXES YIELD name, state, populationPercent
WHERE state <> "ONLINE"
```

### Weekly Tasks
1. **Update Embeddings**
```python
# Re-embed updated content
python3 update_embeddings.py --since "7 days ago"
```

2. **Clean Orphaned Nodes**
```cypher
MATCH (n)
WHERE NOT (n)--()
DELETE n
```

### Monthly Tasks
1. **Backup Database**
```bash
neo4j-admin backup --to=/backup/$(date +%Y%m%d)
```

2. **Performance Analysis**
- Review query logs
- Analyze usage patterns
- Optimize frequently used queries

### Monitoring Queries
```cypher
// Database size
MATCH (n) RETURN count(n) as nodeCount

// Relationship distribution
MATCH ()-[r]->()
RETURN type(r) as relType, count(r) as count
ORDER BY count DESC

// Query performance
CALL dbms.queryJmx("org.neo4j:*") 
YIELD name, attributes
WHERE name CONTAINS "QueryExecution"
RETURN name, attributes
```

## Troubleshooting Guide

### Debug Mode
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add query logging
@app.post("/query")
async def execute_query(request: QueryRequest):
    logger.debug(f"Query: {request.question}")
    logger.debug(f"Mode: {'cypher' if request.use_cypher else 'hybrid'}")
    # ... rest of implementation
```

### Common Error Messages

1. **"No index with name chunk_vector_index found"**
   - Run index creation script
   - Verify index name matches configuration

2. **"The context does not provide information..."**
   - Check if chunks exist with proper labels
   - Verify embeddings are populated
   - Test retriever separately

3. **"dictionary update sequence element #0 has length 1"**
   - Text2Cypher result parsing issue
   - Check record format in enhanced_spyro_api_v2.py

## Conclusion

This implementation provides a robust foundation for the SpyroSolutions RAG system. The dual-mode search capability (Hybrid + Text2Cypher) allows for both semantic understanding and precise data retrieval, making it suitable for various business intelligence use cases.

For questions or issues, refer to:
- Neo4j GraphRAG Documentation: https://github.com/neo4j/neo4j-graphrag-python
- Neo4j Documentation: https://neo4j.com/docs/
- OpenAI API Reference: https://platform.openai.com/docs/