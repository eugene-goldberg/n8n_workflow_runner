# SpyroSolutions Agentic RAG Usage Guide

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd spyro-agentic-rag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: NEO4J_PASSWORD, OPENAI_API_KEY
```

### 3. Database Setup

```bash
# Initialize Neo4j database with sample data
python scripts/setup_database.py
```

### 4. Start the API

```bash
# Run the API server
python -m src.api.main

# API will be available at http://localhost:8000
```

## API Usage Examples

### Basic Query

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/query",
    json={"question": "Which customers have subscriptions worth more than $5M?"},
    headers={"X-API-Key": "spyro-secret-key-123"}
)

print(response.json())
```

### Query with Session Tracking

```python
# Query with session ID for conversation tracking
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "Tell me about TechCorp",
        "session_id": "user-123-session-456"
    },
    headers={"X-API-Key": "spyro-secret-key-123"}
)

# Follow-up query in same session
follow_up = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "What products do they use?",
        "session_id": "user-123-session-456"
    },
    headers={"X-API-Key": "spyro-secret-key-123"}
)
```

### Advanced Usage

```python
import httpx
import asyncio

async def query_agent(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/query",
            json={"question": question},
            headers={"X-API-Key": "spyro-secret-key-123"}
        )
        return response.json()

# Run multiple queries
async def main():
    queries = [
        "What is our total ARR?",
        "Which teams support SpyroAI?",
        "What are the main features of SpyroCloud?"
    ]
    
    results = await asyncio.gather(*[query_agent(q) for q in queries])
    
    for query, result in zip(queries, results):
        print(f"Q: {query}")
        print(f"A: {result['answer']}\n")

asyncio.run(main())
```

## Query Examples by Category

### Entity-Specific Queries (Uses GraphQuery Tool)

```python
# Customer queries
"Which customers have subscriptions worth more than $5M?"
"Show me all enterprise customers in North America"
"What is TechCorp's renewal probability?"

# Financial queries
"What is our total annual recurring revenue?"
"How much revenue does SpyroCloud generate?"
"Show me subscription values by customer"

# Team and project queries
"Which teams support SpyroAI?"
"How many people are in the Cloud Platform Team?"
"What projects is the AI Research Team working on?"

# Risk and objective queries
"What are our high-severity risks?"
"Which objectives are at risk?"
"Show me the progress on our AI Platform Enhancement objective"
```

### Product and Feature Queries (Uses HybridSearch Tool)

```python
# Product information
"What are the key features of SpyroCloud?"
"Tell me about SpyroAI's machine learning capabilities"
"How does SpyroSecure help with compliance?"

# Specific product details
"What is SpyroCloud's market focus?"
"List the security features in our platform"
"What makes SpyroAI different from competitors?"
```

### Conceptual Queries (Uses VectorSearch Tool)

```python
# General information
"What makes our products unique?"
"How do we help enterprises transform digitally?"
"What are the benefits of our platform?"

# Strategic questions
"How do we approach enterprise security?"
"What is our innovation strategy?"
"How do we ensure customer success?"
```

### Complex Multi-Tool Queries

```python
# Customer analysis
"Tell me everything about TechCorp - their subscription, satisfaction, and products they use"

# Business analysis
"How do operational costs impact profitability and what risks should we monitor?"

# Comprehensive queries
"Give me a complete overview of our AI products, which teams work on them, and their market performance"
```

## API Endpoints

### Query Execution
```bash
POST /query
{
    "question": "Your question here",
    "session_id": "optional-session-id"
}
```

### Health Check
```bash
GET /health
```

### Get Available Tools
```bash
GET /tools
Headers: X-API-Key: your-api-key
```

### Conversation History
```bash
GET /conversation?session_id=optional-session-id
Headers: X-API-Key: your-api-key
```

### Clear Conversation
```bash
POST /conversation/clear
Headers: X-API-Key: your-api-key
```

### System Capabilities
```bash
GET /capabilities
```

## Response Format

### Successful Query Response
```json
{
    "query": "Which customers have subscriptions worth more than $5M?",
    "answer": "Based on the data, there are 2 customers with subscriptions worth more than $5M:\n\n1. TechCorp - $8M subscription for SpyroCloud\n2. FinanceHub - $5M subscription for SpyroAI + SpyroSecure",
    "metadata": {
        "agent_type": "LangChain with OpenAI Functions",
        "model": "gpt-4o",
        "execution_time_seconds": 2.34,
        "tokens_used": 245,
        "cost_usd": 0.0024,
        "tools_available": ["GraphQuery", "HybridSearch", "VectorSearch"],
        "session_id": null,
        "timestamp": "2024-08-01T10:30:45.123456"
    },
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Response
```json
{
    "detail": "Error message here"
}
```

## Testing

### Run Test Suite
```bash
# Run comprehensive test suite
python scripts/test_agent.py
```

### Test Specific Functionality
```python
# Test conversation memory
from src.agents.spyro_agent import create_agent

agent = create_agent()

# First query
result1 = agent.query("Tell me about TechCorp")
print(result1['answer'])

# Follow-up (uses conversation context)
result2 = agent.query("What's their subscription value?")
print(result2['answer'])

# Check conversation history
history = agent.get_conversation_history()
print(f"Conversation has {len(history)} messages")

agent.close()
```

## Monitoring and Debugging

### Enable Verbose Logging
```bash
# In .env file
AGENT_VERBOSE=true
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### Monitor Token Usage
```python
# Response includes token usage
response = requests.post("/query", ...)
metadata = response.json()["metadata"]
print(f"Tokens used: {metadata['tokens_used']}")
print(f"Cost: ${metadata['cost_usd']}")
```

### Check Tool Selection
The agent's tool selection is autonomous, but you can see available tools:
```bash
GET /tools
```

## Best Practices

1. **Session Management**: Use session IDs for conversations that need context
2. **Error Handling**: Always handle potential API errors gracefully
3. **Rate Limiting**: Add delays between queries to avoid rate limits
4. **Cost Monitoring**: Track token usage and costs in responses
5. **Query Optimization**: Be specific in queries for better tool selection

## Troubleshooting

### Common Issues

1. **"Agent not initialized"**
   - Check Neo4j connection settings
   - Verify OPENAI_API_KEY is set
   - Check logs for initialization errors

2. **"Invalid API key"**
   - Verify X-API-Key header matches SPYRO_API_KEY in .env

3. **Slow responses**
   - Normal for complex queries (2-5 seconds)
   - Check if using appropriate model (gpt-4o vs gpt-3.5)

4. **No results from queries**
   - Run setup_database.py to ensure data exists
   - Check if indexes are created properly

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your queries
```

## Integration Examples

### With n8n Workflow
```javascript
// n8n HTTP Request node configuration
{
  "method": "POST",
  "url": "http://localhost:8000/query",
  "headers": {
    "X-API-Key": "{{ $credentials.spyroApiKey }}"
  },
  "body": {
    "question": "{{ $json.userQuestion }}",
    "session_id": "{{ $json.sessionId }}"
  }
}
```

### With Python Applications
```python
class SpyroRAGClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        
    def query(self, question: str, session_id: str = None):
        response = requests.post(
            f"{self.base_url}/query",
            json={"question": question, "session_id": session_id},
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SpyroRAGClient("http://localhost:8000", "spyro-secret-key-123")
result = client.query("What is our total ARR?")
print(result['answer'])
```