# Development Guide

This guide covers development setup, architecture details, and best practices for the LangGraph Agentic RAG system.

## Development Setup

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd langgraph-agentic-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Database Setup

Run the setup script or manually start the databases:

```bash
# Automated setup
./scripts/setup_databases.sh

# Or manual setup
docker run -d --name pgvector -e POSTGRES_PASSWORD=password -p 5432:5432 ankane/pgvector
docker run -d --name neo4j -e NEO4J_AUTH=neo4j/password -p 7474:7474 -p 7687:7687 neo4j
```

### 3. Running the Application

```bash
# Run the agent CLI
python -m src.agents.main -i  # Interactive mode
python -m src.agents.main -q "Your query here"  # Single query

# Run the API server
./scripts/run_api.sh
# Or directly:
python -m uvicorn src.api.server:app --reload
```

## Architecture Overview

### Component Structure

```
src/
├── agents/          # LangGraph agent implementations
│   ├── router.py    # Query routing logic
│   ├── nodes.py     # Graph nodes for different tasks
│   └── main_agent.py # Main agent orchestration
├── retrievers/      # Retrieval implementations
│   ├── vector.py    # pgvector and Neo4j vector search
│   ├── hybrid.py    # Combined vector + keyword search
│   └── graph.py     # Graph traversal and Text2Cypher
├── tools/           # Agent tools
│   └── search_tools.py # Search tool wrappers
├── state/           # State management
│   ├── types.py     # State type definitions
│   └── checkpointer.py # PostgreSQL persistence
└── ingestion/       # Knowledge graph construction
    ├── extractors.py # Entity/relation extraction
    └── pipeline.py   # Ingestion orchestration
```

### Key Design Patterns

#### 1. Dual-Memory Architecture
- **Associative Memory**: Vector search for semantic similarity
- **Declarative Memory**: Graph database for structured relationships

#### 2. Dynamic Routing
The router analyzes queries and selects appropriate retrieval strategies:
- `simple_greeting`: Direct response without retrieval
- `fact_lookup`: Semantic vector search
- `relational_query`: Graph traversal with Cypher
- `hybrid_search`: Combined vector + keyword search
- `ambiguous`: Request clarification

#### 3. State Management
LangGraph StateGraph maintains conversation state with:
- Message history
- Tool execution records
- Error tracking
- Human-in-the-loop flags

#### 4. Error Recovery
Self-correction loops handle failures:
- Catch errors in tool execution
- Reflect on errors with LLM
- Retry with corrections
- Fallback after max retries

## Adding New Features

### Adding a New Retriever

1. Create a new retriever class in `src/retrievers/`:
```python
from .base import BaseRetriever

class CustomRetriever(BaseRetriever):
    async def retrieve(self, query: str, k: int = 10) -> List[RetrievalResult]:
        # Implementation
        pass
    
    def get_retriever_type(self) -> str:
        return "custom"
```

2. Create a tool wrapper in `src/tools/search_tools.py`:
```python
@tool
async def custom_search_tool(query: str) -> str:
    """Custom search tool description."""
    retriever = CustomRetriever()
    results = await retriever.retrieve(query)
    # Format and return results
```

3. Update router logic to use the new tool when appropriate.

### Adding a New Node

1. Define the node function in `src/agents/nodes.py`:
```python
async def custom_node(state: AgentState) -> Dict[str, Any]:
    """Custom node logic."""
    # Process state
    return {"updated_field": new_value}
```

2. Add to the graph in `src/agents/main_agent.py`:
```python
builder.add_node("custom", custom_node)
builder.add_edge("previous_node", "custom")
```

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Manual Testing
Use the example notebook:
```bash
jupyter notebook notebooks/example_usage.ipynb
```

## Debugging

### Enable Debug Logging
Set in `.env`:
```
LOG_LEVEL=DEBUG
```

### LangSmith Tracing
Ensure LangSmith is configured:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
```

View traces at: https://smith.langchain.com

### Common Issues

1. **Database Connection Errors**
   - Check Docker containers are running
   - Verify connection strings in `.env`

2. **Import Errors**
   - Ensure virtual environment is activated
   - Check all dependencies are installed

3. **Tool Execution Failures**
   - Check error logs for specific tool errors
   - Verify API keys and permissions

## Best Practices

### 1. Entity Extraction
- Use consistent entity types and relationship types
- Validate extracted data before storage
- Implement deduplication logic

### 2. Retrieval Optimization
- Index frequently queried properties
- Use appropriate chunk sizes (1000 chars recommended)
- Implement caching for repeated queries

### 3. State Management
- Keep state objects lean
- Clear unnecessary data between iterations
- Use thread IDs for conversation continuity

### 4. Error Handling
- Always wrap tool calls in try-except
- Provide meaningful error messages
- Implement retry logic with backoff

## Performance Tuning

### Vector Search
- Adjust `k` parameter based on use case
- Use metadata filters to narrow search space
- Consider hybrid search for better precision

### Graph Queries
- Limit traversal depth with `max_graph_depth`
- Use indexed properties in WHERE clauses
- Profile Cypher queries for optimization

### LLM Calls
- Use appropriate temperature settings
- Implement response caching
- Consider smaller models for routing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

Follow the code style:
- Use Black for formatting
- Run Ruff for linting
- Add type hints
- Document new functions