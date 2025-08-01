# Hybrid Search Architecture in SpyroSolutions Agentic RAG

## Overview

The hybrid search functionality in the SpyroSolutions Agentic RAG system is a sophisticated multi-layered architecture that intelligently combines vector search (semantic similarity) and graph search (entity relationships) to provide optimal results based on query type.

## Key Components

### 1. Pydantic AI Agent (agent/agent.py)
The main orchestrator that:
- Receives user queries
- **Automatically selects appropriate tools** based on the query content
- Combines results from multiple search methods
- Returns responses with full tool transparency

### 2. System Prompt (agent/prompts.py)
Contains the intelligence for tool selection:
```
"Use the knowledge graph tool only when the user asks about two companies in the same question. 
Otherwise, use just the vector store tool."
```

However, in practice, the agent is more sophisticated and uses:
- **Vector search**: For semantic queries about features, descriptions, general information
- **Graph search**: For relationship queries, entity connections, risk associations
- **Hybrid search**: When both semantic and keyword matching would be beneficial

### 3. Search Tools (agent/tools.py)

#### Vector Search Tool
```python
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    # Generates embeddings using OpenAI
    # Searches PostgreSQL with pgvector
    # Returns semantically similar chunks
```

#### Graph Search Tool
```python
async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]:
    # Queries Neo4j via Graphiti
    # Traverses entity relationships
    # Returns facts and connections
```

#### Hybrid Search Tool
```python
async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    # Combines vector and keyword search
    # Uses PostgreSQL hybrid_search function
    # Weights results based on text_weight parameter
```

### 4. Database Layer

#### PostgreSQL with pgvector (agent/db_utils.py)
Implements the actual hybrid search:
```sql
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 10,
    text_weight FLOAT DEFAULT 0.3
)
```

This function:
1. Performs vector similarity search using `<=>` operator
2. Performs full-text search using PostgreSQL's text search
3. Combines scores: `(1 - text_weight) * vector_sim + text_weight * text_sim`
4. Returns results ordered by combined score

#### Neo4j with Graphiti (agent/graph_utils.py)
Handles graph queries through the Graphiti library:
- Entity extraction
- Relationship traversal
- Temporal fact management

## How Hybrid Search Works

### Query Flow

1. **User Query** → n8n Webhook → Agentic RAG API

2. **Agent Analysis**:
   - Pydantic AI agent analyzes the query
   - Based on the system prompt and query content, it decides which tools to use
   - Can invoke multiple tools in parallel

3. **Tool Selection Logic**:
   ```
   Query: "What features does SpyroAnalytics include?"
   → Uses: vector_search (semantic similarity)
   
   Query: "What risks does Disney have?"
   → Uses: graph_search (entity relationships)
   
   Query: "Tell me about enterprise customers and their issues"
   → Uses: hybrid_search (both semantic and keyword matching)
   ```

4. **Search Execution**:
   - **Vector Search**: Embeds query → finds similar chunks in PostgreSQL
   - **Graph Search**: Extracts entities → traverses Neo4j relationships
   - **Hybrid Search**: Combines both vector similarity and text matching

5. **Result Combination**:
   - Agent receives results from all invoked tools
   - Synthesizes information into coherent response
   - Includes tool transparency in metadata

### Metadata and Transparency

Every response includes:
```json
{
  "tools_used": [
    {
      "tool_name": "vector_search",
      "args": {"query": "SpyroAnalytics features", "limit": 10},
      "tool_call_id": "call_xxx"
    }
  ],
  "metadata": {
    "search_type": "SearchType.HYBRID"
  }
}
```

## Implementation Details

### SearchType Enum (agent/models.py)
```python
class SearchType(str, Enum):
    VECTOR = "vector"
    HYBRID = "hybrid"
    GRAPH = "graph"
```

### Hybrid Search SQL Function
The PostgreSQL function combines:
1. **Vector Similarity**: `1 - (embedding <=> query_embedding)`
2. **Text Similarity**: Full-text search with ts_rank
3. **Combined Score**: Weighted average of both scores

### Embedding Generation
- Uses OpenAI's text-embedding-3-small model
- 1536-dimensional vectors
- Cached in PostgreSQL for efficient retrieval

## Performance Characteristics

### Vector Search
- **Speed**: ~100-200ms for 10 results
- **Best for**: Semantic similarity, conceptual queries
- **Limitation**: May miss exact keyword matches

### Graph Search
- **Speed**: ~200-400ms depending on traversal depth
- **Best for**: Entity relationships, structured data
- **Limitation**: Requires well-defined entities

### Hybrid Search
- **Speed**: ~150-300ms for 10 results
- **Best for**: Balanced semantic and keyword matching
- **Advantage**: Best coverage of both approaches

## Configuration

### Environment Variables
```bash
# Vector search
VECTOR_DIMENSION=1536
EMBEDDING_MODEL=text-embedding-3-small

# Hybrid search defaults
DEFAULT_TEXT_WEIGHT=0.3
DEFAULT_SEARCH_LIMIT=10

# Graph search
NEO4J_URI=bolt://spyro_neo4j:7687
```

### Tuning Parameters
- **text_weight**: Balance between vector (0.0) and text (1.0) similarity
- **limit**: Maximum results per search
- **depth**: Graph traversal depth for relationship queries

## Future Enhancements

1. **Query Classification ML Model**: Train a model to better classify query intent
2. **Adaptive Weighting**: Dynamically adjust text_weight based on query type
3. **Result Re-ranking**: Use LLM to re-rank combined results
4. **Caching Layer**: Add Redis for frequently accessed queries
5. **Feedback Loop**: Learn from user interactions to improve tool selection