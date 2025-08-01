# SpyroSolutions Neo4j-GraphRAG-Python Adoption Plan

## Executive Summary

After studying the neo4j-graphrag-python library, I recommend adopting it as the foundation for SpyroSolutions' GraphRAG system. This official Neo4j library provides a robust, well-structured implementation that aligns perfectly with our needs and solves the tool selection problem we've been facing.

## Key Benefits of neo4j-graphrag-python

1. **Built-in Hybrid Retrievers**: The library includes `HybridRetriever` and `HybridCypherRetriever` classes that automatically combine vector and fulltext search
2. **Flexible Architecture**: Clean separation between retrievers, LLMs, and embedders
3. **Production-Ready**: Official Neo4j support with long-term maintenance
4. **Extensible Design**: Easy to add custom retrievers and components
5. **Built-in Text2Cypher**: Includes a `Text2CypherRetriever` for natural language to Cypher queries

## Implementation Strategy

### Phase 1: Direct Integration (Immediate)

```python
# Example integration with SpyroSolutions
from neo4j_graphrag.retrievers import HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

# Configure for SpyroSolutions
driver = neo4j.GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "yourpassword")
)

# Use existing indexes
hybrid_retriever = HybridRetriever(
    driver=driver,
    vector_index_name="vector",  # Your existing vector index
    fulltext_index_name="fulltext",  # Your existing fulltext index
    embedder=OpenAIEmbeddings(model="text-embedding-3-small"),
    neo4j_database="neo4j"
)

# Create Text2Cypher retriever
text2cypher = Text2CypherRetriever(
    driver=driver,
    llm=OpenAILLM(model_name="gpt-4"),
    neo4j_schema=None  # Auto-fetch schema
)

# Create GraphRAG instance
rag = GraphRAG(
    retriever=hybrid_retriever,
    llm=OpenAILLM(model_name="gpt-4")
)
```

### Phase 2: Custom Retriever with Router Integration

```python
from neo4j_graphrag.retrievers.base import Retriever
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem

class RouterEnabledRetriever(Retriever):
    """Custom retriever that uses our deterministic router"""
    
    def __init__(self, driver, vector_retriever, hybrid_retriever, text2cypher, router):
        super().__init__(driver)
        self.vector_retriever = vector_retriever
        self.hybrid_retriever = hybrid_retriever
        self.text2cypher = text2cypher
        self.router = router
    
    def search(self, query_text: str, **kwargs) -> RetrieverResult:
        # Use router to determine strategy
        strategy, confidence, entities = self.router.route(query_text)
        
        if strategy == "graph":
            # Use Text2Cypher for graph queries
            return self.text2cypher.search(query_text, **kwargs)
        elif strategy == "hybrid_sequential" or strategy == "hybrid_parallel":
            # Use HybridRetriever
            return self.hybrid_retriever.search(query_text, **kwargs)
        else:
            # Default to vector search
            return self.vector_retriever.search(query_text, **kwargs)
```

### Phase 3: Migration Steps

1. **Install neo4j-graphrag-python**:
   ```bash
   pip install "neo4j-graphrag[openai]"
   ```

2. **Update SpyroSolutions API**:
   - Replace custom retrieval logic with neo4j-graphrag retrievers
   - Maintain existing REST API interface
   - Use the same Neo4j indexes

3. **Update n8n Workflow**:
   - Modify webhook response to include retriever type used
   - Display this information in the UI

## Code Changes Required

### 1. Update `app/agent/api.py`:

```python
from neo4j_graphrag.retrievers import HybridRetriever, VectorRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

# Initialize retrievers
embedder = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
llm = OpenAILLM(
    model_name=os.getenv("LLM_MODEL", "gpt-4"),
    model_params={"temperature": 0.7}
)

vector_retriever = VectorRetriever(
    driver=driver,
    index_name="vector",
    embedder=embedder
)

hybrid_retriever = HybridRetriever(
    driver=driver,
    vector_index_name="vector",
    fulltext_index_name="fulltext",
    embedder=embedder
)

text2cypher = Text2CypherRetriever(
    driver=driver,
    llm=llm,
    neo4j_schema=None  # Auto-detect
)

# Create router-enabled retriever
router_retriever = RouterEnabledRetriever(
    driver=driver,
    vector_retriever=vector_retriever,
    hybrid_retriever=hybrid_retriever,
    text2cypher=text2cypher,
    router=ROUTER  # Your existing router
)

# Create GraphRAG
graph_rag = GraphRAG(
    retriever=router_retriever,
    llm=llm
)

@app.post("/agent")
async def execute_agent(request: AgentRequest):
    # Use GraphRAG
    result = graph_rag.search(
        query_text=request.message,
        return_context=True,
        retriever_config={"top_k": 5}
    )
    
    return {
        "response": result.answer,
        "context": result.retriever_result.items if hasattr(result, 'retriever_result') else [],
        "retriever_used": router_retriever.last_strategy_used
    }
```

### 2. Benefits Over Current Implementation

1. **Simplified Codebase**: Remove custom vector search, graph traversal logic
2. **Better Hybrid Search**: Built-in support for combining vector and fulltext
3. **Improved Text2Cypher**: Production-ready natural language to Cypher
4. **Extensibility**: Easy to add new retrievers or customize existing ones

### 3. Testing Strategy

```python
# Test script
import asyncio
from neo4j_graphrag.generation import GraphRAG

test_queries = [
    "What is the revenue at risk for TechCorp?",
    "Show me all customers with subscription issues",
    "What are the main features of our platform?",
    "Find customers similar to Acme Corp"
]

async def test_retrievers():
    for query in test_queries:
        result = graph_rag.search(query, return_context=True)
        print(f"Query: {query}")
        print(f"Answer: {result.answer}")
        print(f"Context items: {len(result.retriever_result.items)}")
        print("---")
```

## Timeline

- **Week 1**: Install and test neo4j-graphrag-python with existing data
- **Week 2**: Implement RouterEnabledRetriever
- **Week 3**: Update SpyroSolutions API to use new retrievers
- **Week 4**: Update n8n workflow and test end-to-end

## Conclusion

Adopting neo4j-graphrag-python provides a solid foundation that:
1. Solves the tool selection problem with built-in hybrid retrieval
2. Reduces maintenance burden with official Neo4j support
3. Improves reliability with production-tested code
4. Enables future enhancements with extensible architecture

The router we developed can be integrated as a custom retriever, giving us the best of both worlds: deterministic routing with production-ready retrieval implementations.