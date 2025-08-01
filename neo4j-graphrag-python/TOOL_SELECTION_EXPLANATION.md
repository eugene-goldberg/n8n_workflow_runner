# Tool Selection in SpyroSolutions RAG System

## Overview

The tool selection in the SpyroSolutions RAG system is **deterministic and user-controlled**, not agent-based. There is no AI agent making the determination - instead, the user explicitly chooses which tool to use through a toggle switch in the UI.

## Architecture

### 1. User Interface (Frontend)
- **Toggle Switch**: Users see a toggle labeled "Use Graph Query (Text2Cypher)"
- **Binary Choice**: 
  - OFF (default) → Hybrid Search (Vector + Fulltext)
  - ON → Graph Query (Text2Cypher)

### 2. API Layer
The selection is passed through the API chain:

```typescript
// Frontend (App.tsx)
const [useCypher, setUseCypher] = useState(false);

// Sent in request
body: JSON.stringify({
  query: query,
  use_cypher: useCypher  // This boolean determines the tool
})
```

### 3. Backend Processing
```python
# API endpoint (enhanced_spyro_api_v2.py)
class QueryRequest(BaseModel):
    question: str
    use_cypher: bool = False  # User's choice
    top_k: int = 5

@app.post("/query")
async def execute_query(request: QueryRequest):
    if request.use_cypher:
        # Use Text2CypherRetriever
        cypher_results = rag_system.text2cypher_retriever.search(
            query_text=request.question
        )
    else:
        # Use GraphRAG with HybridRetriever
        result = rag_system.graph_rag.search(
            query_text=request.question
        )
```

## Tool Details

### 1. **Hybrid Search** (use_cypher = false)
- **Components**: HybridRetriever combining:
  - Vector Search (semantic similarity using embeddings)
  - Fulltext Search (keyword matching)
- **Process**:
  1. Query → Embeddings → Vector similarity search
  2. Query → Fulltext index search
  3. Results combined and ranked
  4. Retrieved chunks → LLM for answer generation
- **Best for**: Conceptual questions, general information, semantic understanding

### 2. **Graph Query** (use_cypher = true)
- **Component**: Text2CypherRetriever
- **Process**:
  1. Natural language query → LLM (GPT-4)
  2. LLM generates Cypher query using:
     - Neo4j schema definition
     - Example query patterns
  3. Cypher query executed on Neo4j
  4. Graph results formatted and returned
- **Best for**: Specific entity queries, relationships, aggregations

## Decision Flow

```
User Query
    ↓
[Toggle Switch]
    ↓
    ├─ OFF: Hybrid Search
    │   ├─ Vector Search
    │   ├─ Fulltext Search
    │   └─ GraphRAG Generation
    │
    └─ ON: Graph Query
        ├─ Text2Cypher Conversion
        ├─ Cypher Execution
        └─ Direct Results

```

## No Agent Intelligence

**Key Point**: There is NO agent or AI making the tool selection decision. The system does not:
- Analyze the query to determine which tool to use
- Have any routing logic based on query content
- Make autonomous decisions about retrieval strategy

Instead:
- Users must manually toggle between modes
- The choice is explicit and transparent
- Each mode has its own UI hints and example queries

## Example Queries by Mode

### Hybrid Search Mode
- "What security features does SpyroSolutions offer?"
- "Explain the benefits of cloud infrastructure"
- "Tell me about AI capabilities"

### Graph Query Mode
- "Which customers have subscriptions worth more than $5M?"
- "Show all teams and their assigned products"
- "List customers at risk with their revenue"

## Potential Improvements

While the current system is user-controlled, an agent-based approach could:

1. **Query Classification**: Analyze query intent to auto-select tool
2. **Hybrid Execution**: Run both tools and merge results
3. **Fallback Strategy**: Try Graph Query first, fall back to Hybrid if no results
4. **Context-Aware Routing**: Use conversation history to determine best tool

However, the current explicit approach has advantages:
- User control and transparency
- Predictable behavior
- No misclassification errors
- Clear expectations about results