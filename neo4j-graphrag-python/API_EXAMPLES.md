# SpyroSolutions Agentic RAG API Examples

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require an API key in the header:
```
X-API-Key: spyro-secret-key-123
```

## Endpoints

### 1. Health Check
Check if the API and Neo4j are healthy:

```bash
curl -X GET http://localhost:8000/health \
  -H "X-API-Key: spyro-secret-key-123"
```

### 2. Single Query

#### Simple Query (Vector + Fulltext)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{
    "question": "What products does SpyroSolutions offer?",
    "use_cypher": false,
    "top_k": 5
  }'
```

#### Complex Query (With Graph Traversal)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{
    "question": "Which customers are at risk and what is their ARR?",
    "use_cypher": true,
    "top_k": 5
  }'
```

### 3. Batch Query
Execute multiple queries at once:

```bash
curl -X POST http://localhost:8000/batch_query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '[
    {
      "question": "What are the SLAs for each product?",
      "use_cypher": true
    },
    {
      "question": "Which projects have the highest profitability impact?",
      "use_cypher": true
    },
    {
      "question": "What is the total ARR?",
      "use_cypher": true
    }
  ]'
```

### 4. System Statistics
Get usage statistics:

```bash
curl -X GET http://localhost:8000/stats \
  -H "X-API-Key: spyro-secret-key-123"
```

### 5. Graph Statistics
Get knowledge graph statistics:

```bash
curl -X GET http://localhost:8000/graph/stats \
  -H "X-API-Key: spyro-secret-key-123"
```

### 6. Example Queries
Get example queries for testing:

```bash
curl -X GET http://localhost:8000/examples
```

## Query Examples by Category

### Product Information
```bash
# List all products
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What products does SpyroSolutions offer?"}'

# Product SLAs
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What are the SLAs for SpyroCloud Platform?", "use_cypher": true}'
```

### Customer Analysis
```bash
# At-risk customers
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "Which customers are at risk?", "use_cypher": true}'

# Customer success scores
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What are the customer success scores for all customers?"}'
```

### Financial Metrics
```bash
# Total ARR
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What is the total Annual Recurring Revenue?", "use_cypher": true}'

# Project profitability
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "Which projects have the highest profitability impact?", "use_cypher": true}'
```

### Risk Assessment
```bash
# Customer risks
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What risks are associated with each customer?", "use_cypher": true}'

# Churn risk
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "Which customers have high churn risk?", "use_cypher": true}'
```

### Team and Project Management
```bash
# Team assignments
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "Which teams are responsible for which products?", "use_cypher": true}'

# Project status
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: spyro-secret-key-123" \
  -d '{"question": "What is the status of all active projects?", "use_cypher": true}'
```

## Response Format

### Successful Query Response
```json
{
  "question": "Which customers are at risk?",
  "answer": "Based on the analysis, TechCorp Industries has a medium risk level...",
  "context_items": 5,
  "retriever_type": "hybrid_cypher",
  "processing_time_ms": 145.23,
  "timestamp": "2024-01-15T10:30:00"
}
```

### Error Response
```json
{
  "error": "Internal server error",
  "detail": "Error message details",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Python Example
```python
import requests

# Setup
api_url = "http://localhost:8000"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "spyro-secret-key-123"
}

# Execute query
response = requests.post(
    f"{api_url}/query",
    json={
        "question": "What is the total ARR?",
        "use_cypher": True
    },
    headers=headers
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Processing time: {result['processing_time_ms']}ms")
```

## Running the API

1. Start the API server:
   ```bash
   python3 enhanced_spyro_api.py
   ```

2. The API will be available at:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - OpenAPI schema: http://localhost:8000/openapi.json

3. Test with the client demo:
   ```bash
   python3 api_client_demo.py
   ```